from functools import lru_cache
from typing import Optional

from fastapi import Depends
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent

from app.core.logging import get_logger
from app.memory.checkpoint import get_checkpointer
from app.services.llm_service import get_llm_chat_model

logger = get_logger(__name__)


def build_basic_agent(
        *,
        name: str,
        model: BaseLanguageModel,
        tools: list[BaseTool],
        checkpointer: AsyncPostgresSaver,
        prompt: Optional[str] = None,
        interrupt_before: Optional[list[str]] = None,
) -> CompiledGraph:
    """
    Constructs a LangGraph ReAct agent with the specified tools and language model.

    Returns:
        Callable: A LangGraph agent instance ready to handle inputs.
    """

    agent = create_react_agent(
        name=name,
        model=model,
        tools=tools,
        checkpointer=checkpointer,
        prompt=prompt,
        interrupt_before=interrupt_before,
    )
    return agent


class AgentMngr:
    """
    Agent Manager to manage the agents.
    """

    def __init__(self):
        self.agents = {}

    def register_agent(self, agent: CompiledGraph):
        if agent.name in self.agents:
            raise ValueError(f"Agent '{agent.name}' already exists")
        self.agents[agent.name] = agent

    def get_agent(self, name: str) -> Optional[CompiledGraph]:
        return self.agents.get(name)

    def get_all_agents(self) -> list[CompiledGraph]:
        return list(self.agents.values())


@lru_cache()
def get_agent_managerV2(checkpointer: AsyncPostgresSaver = Depends(get_checkpointer)):
    manager = AgentMngr()

    # Register chat agent
    chat_agent = build_basic_agent(
        name="chat-agent",
        model=get_llm_chat_model(),
        tools=[],
        checkpointer=checkpointer,
        prompt="You are a helpful assistant named Doraemon.",
        interrupt_before=None,
    )
    manager.register_agent(chat_agent)

    # Register search agent
    # Register rag agent

    return manager
