from typing import Optional, Sequence

from app.core.agents.agent import Agent


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

    # noinspection DuplicatedCode
    def remove_agent(self, name: Optional[str] = None, id_: Optional[str]= None ):
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

    # noinspection DuplicatedCode
    def get_agent(self, name:Optional[str]=None, id_:Optional[str]=None) -> Agent|None:
        if name is None and id_ is None:
            raise ValueError("Either name or id_ must be provided")

        if id_ is not None and id_ in self.id_to_agent:
            return self.id_to_agent[id_]

        if name is not None and name in self.name_to_id:
            return self.id_to_agent[self.name_to_id[name]]

        return None


    def get_all_agents(self) -> Sequence[Agent]:
        return list(self.id_to_agent.values())


    def get_all_agent_names(self) -> Sequence[str]:
        return list(self.name_to_id.keys())