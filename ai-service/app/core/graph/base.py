from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph, add_messages, START, END
from typing import Dict, Any, Annotated, Sequence, TypedDict, Union, Callable, Optional

from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt
from structlog.stdlib import BoundLogger

from app.prompts.prompt_templates import get_retriever_prompt_template, get_markdown_answer_generating_prompt_template, \
    get_simple_agent_prompt_template
from app.services.model_service import get_openai_model
from app.utils.enums import MessageName
from app.utils.messages import get_message_prefix, trimmer
from app.core import logging


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    determine_tool_message: AIMessage
    question: str
    next: str

class GraphBuilder:
    def __init__(
            self,
            checkpointer: AsyncPostgresSaver,
            logger: Optional[BoundLogger] = None,
            tools: Optional[Sequence[Union[BaseTool, Callable]]] = None,
            name: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None
    ):
        self.checkpointer= checkpointer
        self.logger = logging.get_logger(self.__class__.__name__) if logger is None else logger
        self.tools = tools
        self.name = name
        self.config = config

    async def _async_agent_node(self, state: State):
        print("---AGENT NODE---")
        model = get_openai_model()
        messages = trimmer.invoke(state["messages"])
        prompt = get_simple_agent_prompt_template()
        chain = prompt | model

        try:
            response = await chain.ainvoke({"messages": messages})
        except Exception as e:
            self.logger.error(f"[_agent_node] Error in invoking chain: {str(e)}")
            raise

        return {"messages": [AIMessage(content=response.content, name=MessageName.AI)], "next": END}

    async def _async_determining_tool_node(self, state: State):
        print("---DETERMINE TOOL NODE---")
        messages = await trimmer.ainvoke(state["messages"])

        docs = "#Previous Messages: "
        docs += "\n\n".join([f"##{get_message_prefix(message)}: \n {message.content}\n\n" for message in messages])

        question = state["question"]

        model = get_openai_model()
        prompt = get_retriever_prompt_template()
        model = model.bind_tools(self.tools)
        chain = prompt | model

        try:
            response = await chain.ainvoke({"question": question, "context": docs})
        except Exception as e:
            self.logger.error(f"[_determining_tool_node] Error in invoking chain: {str(e)}")
            raise

        if not response.content is None and response.content != "":
            return {
                "messages": [AIMessage(content=response.content, name=MessageName.AI)],
                "next": END,
            }

        # We return a list, because this will get added to the existing list
        return {"determine_tool_message": response, "next": "human_review_node"}

    def _human_review_node(self, state: State):
        print("---HUMAN REVIEW NODE---")

        try:
            review_action = interrupt(
                {
                    "question": "Continue executing the tool call?",
                    # Surface tool calls for review
                    "tool_calls": state["determine_tool_message"].tool_calls,
                }
            )
        except Exception as e:
            self.logger.error(f"[human_review_node] Error in interrupting workflow : {str(e)}")
            raise e

        # Approve the tool call and continue
        if review_action == "continue":
            return {"next": "tool_node"}

        # Reject the tool call and generate a response
        return {"next": END}

    async def _async_tool_node(self, state: State, config: RunnableConfig):
        print("---TOOL NODE---")
        determine_tool_message = state["determine_tool_message"]
        messages = []
        for tool_call in determine_tool_message.tool_calls:
            selected_tool = None
            for tool in self.tools:
                if tool.name == tool_call["name"]:
                    selected_tool = tool
                    break

            if selected_tool is None:
                continue

            try:
                tool_msg = await selected_tool.ainvoke(tool_call, config)
            except Exception as e:
                self.logger.error(f"[_tool_node] Error in invoking tool: {str(e)}")
                raise e

            # Check tool_msg is AIMessage
            if isinstance(tool_msg, ToolMessage):
                messages.append(AIMessage(content=tool_msg.content, name=MessageName.TOOL))

        return {"messages": messages, "next": "generate_node"}

    async def _async_generate_node(self, state: State):
        print("---GENERATE NODE---")
        try:
            messages = await trimmer.ainvoke(state["messages"])
            tool_message = messages[-1] if len(messages) > 0 else None
            question = state["question"]

            # Get the documents
            if tool_message is None:
                docs = "#No tool messages"
            else:
                docs = f"\n\n##{get_message_prefix(tool_message)}: \n {tool_message.content}\n\n"

            # Get the prompt
            prompt = get_markdown_answer_generating_prompt_template()
            llm = get_openai_model()

            # Chain
            rag_chain = prompt | llm

            # Run
            response = await rag_chain.ainvoke({"context": docs, "question": question})
            return {
                "messages": [AIMessage(response.content, name=MessageName.AI)],
                "next": END,
            }

        except Exception as e:
            self.logger.error(f"[_generate_node] Error in invoking chain: {str(e)} ")
            raise


    def build_graph(
            self,
            perform_action: Optional[bool] = False,
            has_human_acceptance_flow:Optional[bool] = False
    )-> CompiledStateGraph:
        # Define a new graph
        workflow = StateGraph(State)

        if self.tools is None or len(self.tools) == 0 or not perform_action:
            workflow.add_node("agent_node", self._async_agent_node)
            workflow.add_edge(START, "agent_node")
            workflow.add_edge("agent_node", END)

        elif not has_human_acceptance_flow:
            workflow.add_node("determining_tool_node", self._async_determining_tool_node)  # agent
            workflow.add_node("tool_node", self._async_tool_node)  # retrieval
            workflow.add_node("generate_node", self._async_generate_node)

            workflow.add_edge(START, "determining_tool_node")
            workflow.add_edge("determining_tool_node", "tool_node")
            workflow.add_edge("tool_node", "generate_node")
            workflow.add_edge("generate_node", END)

        else:
            workflow.add_node("determining_tool_node", self._async_determining_tool_node)  # agent
            workflow.add_node("human_review_node", self._human_review_node)  # human review
            workflow.add_node("tool_node", self._async_tool_node)  # retrieval
            workflow.add_node("generate_node", self._async_generate_node)

            workflow.add_edge(START, "determining_tool_node")
            workflow.add_conditional_edges("determining_tool_node", lambda state: state["next"])
            workflow.add_conditional_edges("human_review_node", lambda state: state["next"])
            workflow.add_edge("tool_node", "generate_node")
            workflow.add_edge("generate_node", END)

        return workflow.compile(checkpointer=self.checkpointer)