from typing import Optional

from app.core import logging
from app.core.agents.base import BaseAgent
from app.core.agents.types import AgentType

logger = logging.get_logger(__name__)


class AgentManager:
    """
    Singleton to manage all agents.
    This class is responsible for registering and retrieving graphs.
    """

    _instance = None
    _agents: dict[str, BaseAgent] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentManager, cls).__new__(cls)
        return cls._instance

    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent in the manager.
        """
        if agent.id in self._agents:
            raise ValueError(f"Agent with id {agent.id} already exists.")
        self._agents[agent.id] = agent
        logger.info(f"Agent {agent.id} registered successfully.")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by id.
        """
        return self._agents.get(agent_id, None)

    def get_agents(self) -> dict[str, BaseAgent]:
        """
        Get all agents.
        """
        return self._agents

    def get_agent_by_type(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """
        Get an agent by type.
        """
        for agent in self._agents.values():
            if agent.type == agent_type:
                return agent
        return None

    def get_agent_by_id(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by id.
        """
        return self._agents.get(agent_id, None)


def get_agent_manager() -> AgentManager:
    """
    Get the singleton instance of the agent manager.
    """
    return AgentManager()
