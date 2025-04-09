from functools import lru_cache

from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.agents.base import BuiltinAgent
from app.core.agents.manager import AgentManager
from app.core.graph.builder import GraphBuilder
from app.core.tools.tools import get_rag_tools, get_search_tools
from app.memory.deps import get_checkpointer


@lru_cache()
def get_agent_manager(checkpointer: AsyncPostgresSaver = Depends(get_checkpointer)):
    manager = AgentManager()

    # Register chat agent
    chat_builder = GraphBuilder(checkpointer=checkpointer)
    chat_graph = chat_builder.build_graph(perform_action=False, has_human_acceptance_flow=False)
    config = chat_builder.get_config()
    chat_agent = BuiltinAgent("chat-agent", chat_graph)
    manager.register_agent(chat_agent)

    # Register search agent
    search_builder = GraphBuilder(checkpointer=checkpointer, tools=list(get_search_tools()))
    search_graph = search_builder.build_graph(perform_action=True, has_human_acceptance_flow=False)
    search_agent = BuiltinAgent("search-agent", search_graph)
    manager.register_agent(search_agent)

    # Register rag agent
    rag_builder = GraphBuilder(checkpointer=checkpointer, tools=list(get_rag_tools()))
    rag_graph = rag_builder.build_graph(perform_action=True, has_human_acceptance_flow=False)
    rag_agent = BuiltinAgent("rag-agent", rag_graph)
    manager.register_agent(rag_agent)

    return manager
