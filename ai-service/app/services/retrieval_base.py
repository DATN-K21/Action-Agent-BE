from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.core import logging
from app.prompts.prompt_templates import get_retriever_prompt_template
from app.services.model_service import get_openai_model
from app.utils.messages import get_message_prefix, trimmer

logger = logging.get_logger(__name__)


def create_workflow(tool: BaseTool, tool_name: str, checkpointer: AsyncPostgresSaver):
    # Define the retriever tool
    tools = [tool]

    class AgentState(TypedDict):
        # The add_messages function defines how an update should be processed
        # Default is to replace. add_messages says "append"
        messages: Annotated[Sequence[BaseMessage], add_messages]
        question: str

    async def agent(state):
        """
        Invokes the agent model to generate a response based on the current state. Given
        the question, it will decide to retrieve using the retriever tool, or simply end.
        Args:
            state (messages): The current state
        Returns:
            dict: The updated state with the agent response appended to messages
        """
        print("---CALL AGENT---")
        messages = await trimmer.ainvoke(state["messages"])

        model = get_openai_model()
        model = model.bind_tools(tools)

        try:
            response = await model.ainvoke(messages)
        except Exception as e:
            logger.error(f"[retrieval_base/agent] Error in calling model: {str(e)}")
            raise

        return {"messages": [response]}

    async def generate(state):
        """
        Generate answer
        Args:
            state (messages): The current state
        Returns:
             dict: The updated state with re-phrased question
        """
        print("---GENERATE---")
        messages = await trimmer.ainvoke(state["messages"])
        question = state["question"]

        # Get the documents
        docs = "#Previous Messages:\n"
        docs += "\n\n".join(f"##{get_message_prefix(msg)}: \n {msg.content}" for msg in messages)

        # Get the prompt
        prompt = get_retriever_prompt_template()
        llm = get_openai_model()

        # Chain
        rag_chain = prompt | llm

        # Run
        try:
            response = await rag_chain.ainvoke({"context": docs, "question": question})
        except Exception as e:
            logger.error(f"[retrieval_base/generate] Error in calling model: {str(e)} ")
            raise

        return {"messages": [response]}

    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the nodes
    workflow.add_node("agent", agent)  # agent
    retrieve = ToolNode(tools)
    workflow.add_node("retrieve", retrieve)  # retrieval
    workflow.add_node("generate", generate)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "retrieve",
            END: END,
        },
    )
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    # Compile
    return workflow.compile(checkpointer=checkpointer)
