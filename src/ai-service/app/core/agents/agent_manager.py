from functools import lru_cache
from typing import Optional

from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.agents.agent import Agent
from app.core.graph.base import GraphBuilder
from app.core.tools.tools import get_rag_tools, get_search_tools
from app.memory.checkpoint import get_checkpointer


class AgentManager:
    def __init__(self):
        self.id_to_agent = {}
        self.name_to_id = {}

    def register_agent(self, agent: Agent):
        if agent.id is None:
            raise ValueError("Agent id is not set")

        if agent.name is None:
            raise ValueError("Agent name is not set")

        if agent.id in self.id_to_agent:
            raise ValueError(f"Agent '{agent.id} already exists")

        if agent.name in self.name_to_id:
            raise ValueError(f"Agent '{agent.name}' already exists")

        self.id_to_agent[agent.id] = agent
        self.name_to_id[agent.name] = agent.id

    def remove_agent(self, name: Optional[str] = None, id_: Optional[str] = None):
        if name is None and id_ is None:
            raise ValueError("Either name or id_ must be provided")

        if id_ is not None and id_ in self.id_to_agent:
            agent = self.id_to_agent[id_]
            del self.name_to_id[agent.name]
            del self.id_to_agent[id_]
            return

        if name is not None and name in self.name_to_id:
            id_ = self.name_to_id[name]
            del self.name_to_id[name]
            del self.id_to_agent[id_]
            return

    def get_agent(self, name: Optional[str] = None, id_: Optional[str] = None) -> Agent | None:
        if name is None and id_ is None:
            raise ValueError("Either name or id_ must be provided")

        if id_ is not None and id_ in self.id_to_agent:
            return self.id_to_agent[id_]

        if name is not None and name in self.name_to_id:
            return self.id_to_agent[self.name_to_id[name]]

        return None

    def get_all_agents(self) -> list[Agent]:
        return list(self.id_to_agent.values())

    def get_all_agent_names(self) -> list[str]:
        return list(self.name_to_id.keys())


@lru_cache()
def get_agent_manager(checkpointer: AsyncPostgresSaver = Depends(get_checkpointer)):
    manager = AgentManager()

    # Register chat agent
    chat_builder = GraphBuilder(checkpointer=checkpointer)
    chat_graph = chat_builder.build_graph(perform_action=False, has_human_acceptance_flow=False)
    chat_agent = Agent(chat_graph, name="chat-agent")
    manager.register_agent(chat_agent)

    # Register search agent
    search_builder = GraphBuilder(checkpointer=checkpointer, tools=list(get_search_tools()))
    search_graph = search_builder.build_graph(perform_action=True, has_human_acceptance_flow=False)
    search_agent = Agent(search_graph, name="search-agent")
    manager.register_agent(search_agent)

    # Register rag agent
    rag_builder = GraphBuilder(checkpointer=checkpointer, tools=list(get_rag_tools()))
    rag_graph = rag_builder.build_graph(perform_action=True, has_human_acceptance_flow=False)
    rag_agent = Agent(rag_graph, name="rag-agent")
    manager.register_agent(rag_agent)

    return manager