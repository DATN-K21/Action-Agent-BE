from functools import lru_cache

from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.agents.agent import Agent
from app.core.agents.agent_manager import AgentManager
from app.core.graph.base import GraphBuilder
from app.core.tools.tools import get_search_tools, get_rag_tools
from app.memory.deps import get_checkpointer
from app.services.model_service import AIModelService


@lru_cache()
def get_agent_manager(checkpointer: AsyncPostgresSaver = Depends(get_checkpointer)):
    manager = AgentManager()

    model = AIModelService.get_ai_model()

    # Register chat agent
    chat_builder = GraphBuilder(model=model, tools=[], checkpointer=checkpointer)
    chat_graph = chat_builder.build_graph()
    chat_agent = Agent(chat_graph, name="chat-agent")
    manager.register_agent(chat_agent)

    # Register search agent
    search_builder = GraphBuilder(model=model, tools=list(get_search_tools()), checkpointer=checkpointer)
    search_graph = search_builder.build_graph()
    search_agent = Agent(search_graph, name="search-agent")
    manager.register_agent(search_agent)

    # Register rag agent
    rag_builder = GraphBuilder(model=model, tools=list(get_rag_tools()), checkpointer=checkpointer)
    rag_graph = rag_builder.build_graph()
    rag_agent = Agent(rag_graph, name="rag-agent")
    manager.register_agent(rag_agent)

    return manager
