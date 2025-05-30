from functools import cache

from langchain.tools import BaseTool
from langchain.tools.retriever import create_retriever_tool

from app.core.rag.pgvector import PGVectorWrapper
from app.core.tools import managed_tools


@cache
def get_tool(tool_name: str) -> BaseTool:
    for _, tool in managed_tools.items():
        if tool.display_name == tool_name:
            return tool.tool
    raise ValueError(f"Unknown tool: {tool_name}")


@cache
def get_retrieval_tool(tool_name: str, description: str, user_id: str, kb_id: str):
    retriever = PGVectorWrapper().retriever(user_id, kb_id)
    return create_retriever_tool(retriever, name=tool_name, description=description)
