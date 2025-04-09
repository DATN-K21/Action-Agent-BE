from typing import Optional

from app.core.agents.agent import Agent


class AgentManager:
    def __init__(self):
        self.agent_list: dict[str, Agent] = {}

    def register_agent(self, agent: Agent):
        """
        Register an agent in the manager.
        """
        if agent.name is None or agent.name == "":
            raise ValueError("Agent name is not set")
        if agent.name in self.agent_list:
            raise ValueError(f"Agent '{agent.name} already exists")
        self.agent_list[agent.name] = agent
        self.agent_list = dict(sorted(self.agent_list.items()))

    def remove_agent(self, name: str):
        """
        Remove an agent from the manager by its name.
        """
        if name is not None and name in self.agent_list:
            del self.agent_list[name]

    def get_agent(self, name: str) -> Optional[Agent]:
        """
        Get an agent by its name.
        """
        if name in self.agent_list:
            return self.agent_list[name]
        return None

    def get_all_agents(self) -> list[Agent]:
        """
        Get all agents in the manager.
        """
        return list(self.agent_list.values())

    def get_all_agent_names(self) -> list[str]:
        """
        Get all agent names in the manager.
        """
        return list(self.agent_list.keys())
