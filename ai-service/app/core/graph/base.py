import json
from typing import Annotated, Any, Callable, Dict, Optional, Sequence, TypedDict, Literal

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt

from app.core import logging
from app.core.enums import MessageName
from app.core.utils.messages import get_message_prefix, trimmer
from app.prompts.prompt_templates import (
    get_markdown_answer_generating_prompt_template,
    get_simple_agent_prompt_template,
    get_openai_function_prompt_template, get_human_in_loop_evaluation_prompt_template,
)
from app.services.model_service import get_openai_model

logger = logging.get_logger(__name__)


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_selection_message: AIMessage
    tool_message: ToolMessage
    question: str
    next: str


class BinaryScore(TypedDict):
    score: Literal["yes", "no"]


# noinspection PyMethodMayBeStatic
class GraphBuilder:
    def __init__(
            self,
            checkpointer: AsyncPostgresSaver,
            tools: Optional[list[BaseTool | Callable]] = None,
            name: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None,
    ):
        self.checkpointer = checkpointer
        self.tools = tools
        self.name = name
        self.config = config

    async def _async_agent_node(self, state: State):
        logger.info("---AGENT NODE---")

        try:
            model = get_openai_model()
            messages = trimmer.invoke(state["messages"])
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
            question = state["question"]

            model = get_openai_model(temperature=0)
            prompt = get_openai_function_prompt_template()
            model = model.bind_tools(self.tools)
            chain = prompt | trimmer | model
            response = await chain.ainvoke({
                "input": question,
                "chat_history": state["messages"],
                "agent_scratchpad": []
            })

            if response.content is not None and response.content != "":
                return {
                    "messages": [AIMessage(content=response.content, name=MessageName.AI)],
                    "next": END,
                }

            return {"tool_selection_message": response, "next": "evaluate_human_in_loop_node"}

        except Exception as e:
            logger.error(f"[_async_select_tool_node] Error in invoking chain: {str(e)}")
            raise

    async def _async_evaluate_human_in_loop_node(self, state: State):
        logger.info("---EVALUATE HUMAN IN LOOP NODE---")
        tool_selection_message = state["tool_selection_message"]
        str_tool_calls = json.dumps(tool_selection_message.tool_calls)

        prompt = get_human_in_loop_evaluation_prompt_template()
        model = get_openai_model(model="gpt-3.5-turbo-0125", temperature=0)
        chain = prompt | model.with_structured_output(BinaryScore)
        response = await chain.ainvoke({"tool_calls": str_tool_calls})

        if response["score"] == "yes":
            return {"next": "human_review_node"}
        else:
            return {"next": "tool_node"}

    async def _async_human_review_node(self, state: State):
        logger.info("---HUMAN REVIEW NODE---")

        # Make a stream by using LLM (for socketio stream)
        str_tool_message = json.dumps(state["tool_selection_message"].tool_calls)
        model = get_openai_model(temperature=0)
        model = model.bind_tools(self.tools)
        await model.ainvoke(input=str_tool_message)

        review_action = interrupt(
            {
                # Surface tool calls for review
                "tool_calls": state["tool_selection_message"].tool_calls
            }
        )

        # Approve the tool call and continue
        if review_action == "continue":
            return {"next": "tool_node", "messages": [AIMessage(content=str_tool_message, name=MessageName.TOOL)]}

        # Reject the tool call and generate a response
        return {"next": END, "messages": [AIMessage(content=str_tool_message, name=MessageName.TOOL)]}

    async def _async_tool_node(self, state: State, config: RunnableConfig):
        logger.info("---TOOL NODE---")
        try:

            tool_selection_message = state["tool_selection_message"]
            messages = []
            for tool_call in tool_selection_message.tool_calls:
                selected_tool = None
                for tool in self.tools:  # type: ignore
                    if tool.name == tool_call["name"]:
                        selected_tool = tool
                        break
                if selected_tool is None:
                    continue
                tool_msg = await selected_tool.ainvoke(tool_call, config)

                # Check tool_msg is AIMessage
                if isinstance(tool_msg, ToolMessage):
                    messages.append(tool_msg)

            return {"tool_message": messages[-1], "next": "generate_node"}

        except Exception as e:
            logger.error(f"[_tool_node] Error in invoking tool: {str(e)}")
            raise e

    async def _async_generate_node(self, state: State):
        logger.info("---GENERATE NODE---")
        try:
            tool_message = state["tool_message"]
            question = state["question"]

            # Get the documents
            if tool_message is None:
                docs = "#No tool messages"
            else:
                docs = f"\n\n##{get_message_prefix(tool_message)}: \n {tool_message.content}\n\n"

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
                                           lambda state: END if state["next"] == END else "tool_node")
            workflow.add_edge("tool_node", "generate_node")
            workflow.add_edge("generate_node", END)

        else:
            workflow.add_node("select_tool_node", self._async_select_tool_node)  # agent
            workflow.add_node("evaluate_human_in_loop_node", self._async_evaluate_human_in_loop_node)
            workflow.add_node("human_review_node", self._async_human_review_node)  # human review
            workflow.add_node("tool_node", self._async_tool_node)  # retrieval
            workflow.add_node("generate_node", self._async_generate_node)

            workflow.add_edge(START, "select_tool_node")
            workflow.add_conditional_edges("select_tool_node", lambda state: state["next"])
            workflow.add_conditional_edges("evaluate_human_in_loop_node", lambda state: state["next"])
            workflow.add_conditional_edges("human_review_node", lambda state: state["next"])
            workflow.add_edge("tool_node", "generate_node")
            workflow.add_edge("generate_node", END)

        return workflow.compile(checkpointer=self.checkpointer)
