import logging
from langchain_core.tools import create_retriever_tool
from typing import Literal
from langchain_core.runnables.config import RunnableConfig

from app.services.models_service import get_openai_model
from app.services.multi_agent.utils.helpers import AgentState, AgentMetadata, AvailableAgents
from app.utils.messages import trimmer
from app.utils.upload import vstore

logger = logging.getLogger(__name__)

FILE_RAG_DESCRIPTION="""
\n<agent>\n
<name>file_rag<name>\n
<usage>Use the File RAG agent to query specific questions related to the content of an uploaded file, 
retrieving precise and contextual information based on the file's data.</usage>\n
</agent>\n
"""

class FileRagAgentMetadata(AgentMetadata):
    type: Literal[AvailableAgents.FILE_RAG] = AvailableAgents.FILE_RAG
    name: Literal["file_rag"] = "file_rag"
    description: Literal[FILE_RAG_DESCRIPTION]= FILE_RAG_DESCRIPTION


def get_rag_tool(thread_id: str):
    retriever = vstore.as_retriever(
        search_kwargs={"filter": {"namespace": {"$in": [thread_id]}}}
    )

    rag_tool = create_retriever_tool(
        retriever,
        "retriever_tool",
        "Use the File RAG tool to query specific questions related to the content of an uploaded file, "
        "retrieving precise and contextual information based on the file's data.",
    )

    return rag_tool

async def file_rag_node(state: AgentState, config: RunnableConfig):
    try:
        rag_tool = get_rag_tool(config["configurable"].get("thread_id", ""))
        model_forced_to_rag = get_openai_model().bind_tools([rag_tool], tool_choice="retriever_tool")
        messages = await trimmer.ainvoke(state["messages"])
        state["messages"] = messages
        result = await model_forced_to_rag.ainvoke(state["messages"])

        for tool_call in result.tool_calls:
            selected_tool = {"retriever_tool": rag_tool}[tool_call["name"].lower()]
            tool_msg = await selected_tool.ainvoke(tool_call)
            messages.append(tool_msg)

        return {
            "messages": [messages[-1].content]
        }
    except Exception as e:
        logger.error(f"Error in execute file_rag node: {str(e)}")
        raise e