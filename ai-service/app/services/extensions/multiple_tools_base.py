from typing import Annotated, Callable, Sequence, TypedDict, Union

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.types import interrupt

from app.core import logging
from app.memory import get_checkpointer
from app.prompts.prompt_templates import get_retriever_prompt_template
from app.services.model_service import get_openai_model
from app.utils.enums import MessageName
from app.utils.messages import get_message_prefix, trimmer

logger = logging.get_logger(__name__)


def create_multiple_tools_workflow(tools: Sequence[Union[BaseTool, Callable]]):
    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        determine_tool_message: AIMessage
        question: str
        next: str

    async def determining_tool_node(state):
        print("---DETERMINE TOOL NODE---")
        messages = await trimmer.ainvoke(state["messages"])

        docs = "#Previous Messages: "
        docs += "\n\n".join([f"##{get_message_prefix(message)}: \n {message.content}\n\n" for message in messages])

        question = state["question"]

        model = get_openai_model()
        prompt = get_retriever_prompt_template()
        model = model.bind_tools(tools)
        chain = prompt | model

        try:
            response = await chain.ainvoke({"question": question, "context": docs})
        except Exception as e:
            logger.error(f"[multi_tools_base/determining_tool_node] Error in calling model: {str(e)}")
            raise e

        if response.content != "":
            return {
                "messages": [AIMessage(content=response.content, name=MessageName.AI)],
                "next": END,
            }

        # We return a list, because this will get added to the existing list
        return {"determine_tool_message": response, "next": "human_review_node"}

    def human_review_node(state):
        print("---HUMAN REVIEW NODE---")
        review_action = interrupt(
            {
                "question": "Continue executing the tool call?",
                # Surface tool calls for review
                "tool_calls": state["determine_tool_message"].tool_calls,
            }
        )

        # Approve the tool call and continue
        if review_action == "continue":
            return {"next": "tool_node"}

        # Reject the tool call and generate a response
        return {"next": END}

    async def tool_node(state):
        print("---TOOL NODE---")
        determine_tool_message = state["determine_tool_message"]
        messages = []
        for tool_call in determine_tool_message.tool_calls:
            selected_tool = None
            for tool in tools:
                if tool.name == tool_call["name"]:
                    selected_tool = tool
                    break

            if selected_tool is None:
                continue

            try:
                tool_msg = await selected_tool.ainvoke(tool_call)
            except Exception as e:
                logger.error(f"[multi_tools_base/tool_node] Error in calling tool: {str(e)}")
                raise e

            # Check tool_msg is AIMessage
            if isinstance(tool_msg, ToolMessage):
                messages.append(AIMessage(content=tool_msg.content, name=MessageName.TOOL))

        return {"messages": messages, "next": "generate_node"}

    async def generate_node(state):
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
            prompt = get_retriever_prompt_template()
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
            logger.error(f"[multi_tools_base/generate_node] Error in calling model: {str(e)} ")
            raise e

    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the nodes
    workflow.add_node("determining_tool_node", determining_tool_node)  # agent
    workflow.add_node("human_review_node", human_review_node)  # human review
    workflow.add_node("tool_node", tool_node)  # retrieval
    workflow.add_node("generate_node", generate_node)

    workflow.add_edge(START, "determining_tool_node")
    workflow.add_conditional_edges("determining_tool_node", lambda state: state["next"])
    workflow.add_conditional_edges("human_review_node", lambda state: state["next"])
    workflow.add_edge("tool_node", "generate_node")
    workflow.add_edge("generate_node", END)

    # Compile
    return workflow.compile(checkpointer=get_checkpointer())
