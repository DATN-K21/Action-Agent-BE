from typing import Sequence, Union, Callable

from fastapi import Depends
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.agents.agent import Agent
from app.core.graph.base import GraphBuilder
from app.core.tools.deps import get_search_tools, get_rag_tools, get_gmail_tools
from app.memory.deps import get_checkpointer


def get_chat_agent(checkpointer: AsyncPostgresSaver = Depends(get_checkpointer)):
    builder = GraphBuilder(checkpointer=checkpointer)
    graph = builder.build_graph()
    chat_agent = Agent(graph, name="chat_agent")
    return chat_agent


def get_search_agent(
        checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
        tools: Sequence[Union[BaseTool, Callable]] = Depends(get_search_tools)
):
    builder = GraphBuilder(checkpointer=checkpointer, tools=tools)
    graph = builder.build_graph()
    search_agent = Agent(graph, name="search_agent")
    return search_agent


def get_rag_agent(
        checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
        tools: Sequence[Union[BaseTool, Callable]] = Depends(get_rag_tools)
):
    builder = GraphBuilder(checkpointer=checkpointer, tools=tools)
    graph = builder.build_graph()
    rag_agent = Agent(graph, name="rag_agent")
    return rag_agent


def get_gmail_agent(
        checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
        tools: Sequence[Union[BaseTool, Callable]] = Depends(get_gmail_tools)
):
    builder = GraphBuilder(checkpointer=checkpointer, tools=tools)
    graph = builder.build_graph()
    gmail_agent = Agent(graph, name="gmail_agent")
    return gmail_agent