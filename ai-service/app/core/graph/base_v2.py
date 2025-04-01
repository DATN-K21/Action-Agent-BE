import json
from typing import Annotated, Any, Dict, Optional, Sequence, TypedDict, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig, Runnable
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt
from pydantic import BaseModel, TypeAdapter

from app.core import logging
from app.core.enums import MessageName
from app.core.monkey_patches.deps import patch_lib
from app.core.tools.tools import get_date_parser_tools
from app.core.utils.messages import trimmer, truncate_text
from app.prompts.prompt_templates import (
    get_markdown_answer_generating_prompt_template,
    get_simple_agent_prompt_template,
    get_openai_function_prompt_template, get_human_in_loop_evaluation_prompt_template,
    get_enhanced_prompt_template, get_regenerate_tool_calls_prompt_template,
)
from app.services.model_service import get_openai_model

logger = logging.get_logger(__name__)


class ToolCall(BaseModel):
    name: str
    args: dict
    id: Optional[str] = None
    type: Optional[str] = None


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_calls: list[ToolCall]
    tool_messages: list[AIMessage]
    question: str
    next: str
    interrupted: bool


class BinaryScore(TypedDict):
    score: Literal["yes", "no"]


class StreamData(BaseModel):
    node_name: str
    name: MessageName
    output: str


class HumanEditingData(BaseModel):
    execute: bool
    tool_calls: Optional[list[ToolCall]] = None


# noinspection PyMethodMayBeStatic
class GraphBuilder:
    def __init__(
            self,
            checkpointer: AsyncPostgresSaver,
            tools: Optional[list[BaseTool | Runnable]] = None,
            tool_choice: Optional[str] = None,
            name: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None,
    ):
        self.checkpointer = checkpointer
        self.tools = tools
        self.tool_choice = tool_choice
        self.name = name
        self.config = config
        self.enhanced_question_tools = []

        # Add date parser tools to the enhanced question tools
        self.enhanced_question_tools.extend(get_date_parser_tools())

    async def _async_enhance_prompt_node(self, state: State, config: RunnableConfig):
        logger.info("---ENHANCE PROMPT NODE---")
        try:
            question = state.get("question")

            model = get_openai_model(temperature=0, streaming=False)
            prompt = get_enhanced_prompt_template()
            agent = create_react_agent(
                model=model,
                tools=self.enhanced_question_tools,
                prompt=prompt
            )

            response = await agent.ainvoke(input={"messages": HumanMessage(question)}, config=config)

            print("[updated question]", response["messages"][-1].content)

            return {"question": response["messages"][-1].content}

        except Exception as e:
            logger.error(f"[_enhance_question_node] Error in invoking chain: {str(e)}")
            raise

    async def _async_agent_node(self, state: State):
        logger.info("---AGENT NODE---")

        try:
            model = get_openai_model()
            messages = trimmer.invoke(state.get("messages"))
            prompt = get_simple_agent_prompt_template()
            chain = prompt | model
            response = await chain.ainvoke({"messages": messages})

            return {"messages": [AIMessage(content=response.content, name=MessageName.AI)], "next": END}
        except Exception as e:
            logger.error(f"[_agent_node] Error in invoking chain: {str(e)}")
            raise

    async def _async_select_tool_node(self, state: State):
        logger.info("---SELECT TOOL NODE---")

        try:
            question = state.get("question")
            messages = trimmer.invoke(state.get("messages"))

            model = get_openai_model(temperature=0)
            prompt = get_openai_function_prompt_template()
            if self.tool_choice is not None:
                model = model.bind_tools(tools=self.tools, tool_choice=self.tool_choice)
            else:
                model = model.bind_tools(self.tools)
            chain = prompt | trimmer | model
            response = await chain.ainvoke({
                "input": question,
                "chat_history": messages,
                "agent_scratchpad": []
            })

            if response.content is not None and response.content != "":
                return {
                    "messages": [AIMessage(content=response.content, name=MessageName.AI)],
                    "next": END,
                }

            adapter = TypeAdapter(list[ToolCall])
            print("[tool_calls]", response.tool_calls)

            return {"tool_calls": adapter.validate_python(response.tool_calls),
                    "next": "evaluate_human_in_loop_node"}

        except Exception as e:
            logger.error(f"[_async_select_tool_node] Error in invoking chain: {str(e)}")
            raise

    async def _async_evaluate_human_in_loop_node(self, state: State):
        logger.info("---EVALUATE HUMAN IN LOOP NODE---")
        tool_calls = state.get("tool_calls")
        str_tool_calls = json.dumps([item.model_dump() for item in tool_calls])

        prompt = get_human_in_loop_evaluation_prompt_template()
        model = get_openai_model(model="gpt-4o-mini", temperature=0)
        chain = prompt | model.with_structured_output(BinaryScore)
        response = await chain.ainvoke({"tool_calls": str_tool_calls})

        if response["score"] == "yes":
            return {"next": "human_editing_node", "interrupted": True}
        else:
            return {"next": "tool_node", "interrupted": False}

    async def _async_human_editing_node(self, state: State):
        logger.info("---HUMAN EDITING NODE---")

        # Make a stream by using LLM (for socketio stream)
        str_tool_message = json.dumps([item.model_dump() for item in state.get("tool_calls")])
        model = get_openai_model(temperature=0)
        model = model.bind_tools(self.tools)
        prompt = get_regenerate_tool_calls_prompt_template()
        chain = prompt | model

        await chain.ainvoke(input={"tool_calls": str_tool_message})

        data = interrupt(
            {
                "tool_calls": state.get("tool_calls")
            }
        )

        adapter = TypeAdapter(HumanEditingData)
        data = adapter.validate_python(data)

        # Approve the tool call and continue
        if data.execute:
            human_tool_calls = data.tool_calls
            if human_tool_calls is not None:
                tool_calls = state.get("tool_calls")
                for human_tool_call in human_tool_calls:
                    index = next((i for i, item in enumerate(tool_calls)
                                  if item.name == human_tool_call.name
                                  ), -1)
                    tool_calls[index].args = human_tool_call.args

                state["tool_calls"] = tool_calls
                str_tool_message = json.dumps([item.model_dump() for item in tool_calls])

            return {"next": "tool_node", "messages": [AIMessage(content=str_tool_message, name=MessageName.TOOL)]}

        # Reject the tool call and generate a response
        return {"next": END}

    async def _async_tool_node(self, state: State, config: RunnableConfig):
        logger.info("---TOOL NODE---")

        try:
            # Fix composio library
            patch_lib()

            tool_calls = state.get("tool_calls")
            messages = []
            for tool_call in tool_calls:
                selected_tool = None
                for tool in self.tools:  # type: ignore
                    if tool.name == tool_call.name:
                        selected_tool = tool
                        break
                if selected_tool is None:
                    continue
                data = await selected_tool.ainvoke(tool_call.args, config)

                # Check tool_msg is AIMessage
                if data is not None:
                    messages.append(AIMessage(content=str(data), name=MessageName.TOOL,
                                              additional_kwargs={"tool_call": tool_call.model_dump()}))

            return {"tool_messages": messages, "next": "generate_node"}

        except Exception as e:
            logger.error(f"[_tool_node] Error in invoking tool: {str(e)}")
            raise e

    async def _async_generate_node(self, state: State):
        logger.info("---GENERATE NODE---")
        try:
            tool_calls = state.get("tool_calls")
            tool_messages = state.get("tool_messages")
            question = state.get("question")

            # Get the documents
            docs = ""

            if state.get("interrupted"):
                if tool_calls is None or len(tool_calls) == 0:
                    docs += "\n#No tool calls\n"
                else:
                    for tool_call in tool_calls:
                        docs += f"\n## ToolCall: \n {tool_call.model_dump_json()}\n"

            if tool_messages is None or len(tool_messages) == 0:
                docs += "\n#No tool messages\n"
            else:
                for tool_message in tool_messages:
                    docs += f"\n## ToolMessage: \n {tool_message.content}\n"

            docs = truncate_text(docs)

            prompt = get_markdown_answer_generating_prompt_template()
            llm = get_openai_model(temperature=0.5)
            rag_chain = prompt | llm

            response = await rag_chain.ainvoke({"context": docs, "question": question})

            return {
                "messages": [AIMessage(response.content, name=MessageName.AI)],
                "next": END,
            }

        except Exception as e:
            logger.error(f"[_generate_node] Error in invoking chain: {str(e)} ")
            raise

    def build_graph(
            self, perform_action: Optional[bool] = False, has_human_acceptance_flow: Optional[bool] = False
    ) -> CompiledStateGraph:
        # Define a new graph
        workflow = StateGraph(State)

        if self.tools is None or len(self.tools) == 0 or not perform_action:
            workflow.add_node("agent_node", self._async_agent_node)
            workflow.add_edge(START, "agent_node")
            workflow.add_edge("agent_node", END)

        elif not has_human_acceptance_flow:
            workflow.add_node("select_tool_node", self._async_select_tool_node)  # agent
            workflow.add_node("tool_node", self._async_tool_node)  # retrieval
            workflow.add_node("generate_node", self._async_generate_node)

            workflow.add_edge(START, "select_tool_node")
            workflow.add_conditional_edges("select_tool_node",
                                           lambda state: END if state.get("next") == END else "tool_node")
            workflow.add_edge("tool_node", "generate_node")
            workflow.add_edge("generate_node", END)

        else:
            workflow.add_node("enhance_prompt_node", self._async_enhance_prompt_node)
            workflow.add_node("select_tool_node", self._async_select_tool_node)  # agent
            workflow.add_node("evaluate_human_in_loop_node", self._async_evaluate_human_in_loop_node)
            workflow.add_node("human_editing_node", self._async_human_editing_node)  # human edit
            workflow.add_node("tool_node", self._async_tool_node)  # retrieval
            workflow.add_node("generate_node", self._async_generate_node)

            workflow.add_edge(START, "enhance_prompt_node")
            workflow.add_edge("enhance_prompt_node", "select_tool_node")
            workflow.add_conditional_edges("select_tool_node", lambda state: state.get("next"))
            workflow.add_conditional_edges("evaluate_human_in_loop_node", lambda state: state.get("next"))
            workflow.add_conditional_edges("human_editing_node", lambda state: state.get("next"))
            workflow.add_edge("tool_node", "generate_node")
            workflow.add_edge("generate_node", END)

        return workflow.compile(checkpointer=self.checkpointer)
