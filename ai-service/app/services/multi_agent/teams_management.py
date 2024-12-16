import logging

from langgraph.graph import StateGraph, START
from langchain_core.runnables.config import RunnableConfig
from typing import List, Any, Literal

from app.services.multi_agent.utils.helpers import AgentState, make_supervisor_node, AgentMetadata, AvailableAgents, trimmer
from app.services.models_service import get_openai_model
from app.services.multi_agent.research_team.research_supervisor import research_team_node, ResearchTeamMetadata


logger = logging.getLogger(__name__)

# ************ Build teams management graph  ************
METAS: List[Any] = [
    ResearchTeamMetadata()
]

main_supervisor_node = make_supervisor_node(get_openai_model(), METAS)

teams_builder = StateGraph(state_schema=AgentState)
teams_builder.add_node("main_supervisor", main_supervisor_node)
teams_builder.add_node(ResearchTeamMetadata().name, research_team_node)

teams_builder.add_edge(START, "main_supervisor"),
teams_builder.add_edge(ResearchTeamMetadata().name, "main_supervisor")
teams_builder.add_conditional_edges("main_supervisor", lambda state: state["next"])
teams_management_graph = teams_builder.compile()

# ************ Configura teams manager  ************
TEAMS_MANAGEMENT_DESCRIPTION = (
    "\n<agent>\n"
    "<name>teams_management</name>\n"
    "<usage>Supervises and coordinates the activities of multiple teams, ensuring alignment "
    "with project goals and efficient execution of tasks. Provides strategic guidance, "
    "oversees progress, and resolves conflicts within the teams.</usage>\n"
    "<sub_agent>\n"
    f"\n{ResearchTeamMetadata().description}\n"
    "</sub_agent>\n"
    "</agent>\n"
)

class TeamsManagementMetadata(AgentMetadata):
    type: Literal[AvailableAgents.TEAMS_MANAGEMENT] = AvailableAgents.TEAMS_MANAGEMENT
    name: Literal["teams_management"] = "teams_management"
    description: Literal[TEAMS_MANAGEMENT_DESCRIPTION] = TEAMS_MANAGEMENT_DESCRIPTION

async def team_management_node(state: AgentState, config: RunnableConfig):
    try:
        state["messages"] = await trimmer.ainvoke(state["messages"])
        result = await teams_management_graph.ainvoke(state, config)
        return {
            "retrival_doc": result["messages"][-1].content
        }
    except Exception as e:
        logger.error(f"Error in execute graph of teams_management node: {e}")
        raise e