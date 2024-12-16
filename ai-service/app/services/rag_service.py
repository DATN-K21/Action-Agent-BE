import logging
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import create_retriever_tool
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.memory.checkpoint import AsyncPostgresCheckpoint
from app.utils.messages import get_message_prefix, trimmer
from app.utils.upload import vstore
from app.services.models_service import get_openai_model
from app.prompts.prompt_templates import get_rag_prompt_template
from app.services.retrieval_base_service import create_workflow

CHECKPOINTER = AsyncPostgresCheckpoint.get_instance()

logger = logging.getLogger(__name__)

def get_retriever(thread_id: str):
    return vstore.as_retriever(
        search_kwargs={"filter": {"namespace": {"$in": [thread_id]}}}
    )

 # Define the retriever tool
def get_retriever_tool(thread_id: str):
    return create_retriever_tool(
        get_retriever(thread_id),
        "retriever_tool",
        "Search and return information from the most relevant documents"
    )


async def execute_rag(thread_id: str, user_input: str, max_recursion: int = 5):
    try:
        retriever_tool = get_retriever_tool(thread_id)
        graph = await create_workflow(tool = retriever_tool, tool_name = "retriever_tool")
        state = {"messages": [HumanMessage(user_input)], "question": user_input}
        config = {"recursion_limit": max_recursion, "configurable": {"thread_id": thread_id}}
        response = await graph.ainvoke(state, config)
        return response["messages"][-1].content
    except Exception as e:
        logger.error(f"Error in execute graph of RAG bot: {str(e)}")
        raise e