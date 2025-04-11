from typing import Any, Final, List, Literal

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import START, StateGraph

from app.core import logging
from app.services.model_service import get_chat_model
from app.services.multi_agent.research_team.rag import FileRagAgentMetadata, rag_node
from app.services.multi_agent.research_team.tavily import TavilyAgentMetadata, tavily_node
from app.services.multi_agent.research_team.wikipedia import WikipediaAgentMetadata, wikipedia_node
from app.services.multi_agent.utils.helpers import AgentMetadata, AgentState, AvailableAgents, make_supervisor_node

logger = logging.get_logger(__name__)

# ************ Build research graph ************
METAS: List[Any] = [
    TavilyAgentMetadata(),
    WikipediaAgentMetadata(),
    FileRagAgentMetadata(),
]

research_supervisor = make_supervisor_node(get_chat_model(), METAS)

# Define graph builder
research_builder = StateGraph(state_schema=AgentState)
research_builder.add_node("research_supervisor", research_supervisor)
research_builder.add_node(TavilyAgentMetadata().name, tavily_node)
research_builder.add_node(WikipediaAgentMetadata().name, wikipedia_node)
research_builder.add_node(FileRagAgentMetadata().name, rag_node)

# Define the control flow
research_builder.add_edge(START, "research_supervisor")
# We want our workers to ALWAYS "report back" to the supervisor when done
research_builder.add_edge(TavilyAgentMetadata().name, "research_supervisor")
research_builder.add_edge(WikipediaAgentMetadata().name, "research_supervisor")
research_builder.add_edge(FileRagAgentMetadata().name, "research_supervisor")
# Add the edges where routing applies
research_builder.add_conditional_edges("research_supervisor", lambda state: state["next"])

# Compile the graph
research_graph = research_builder.compile()


# ************ Configura research team  ************
RESEARCH_TEAM_DESCRIPTION = (
    "\n<agent>\n"
    "<name>research_team</name>\n"
    "<usage>Supervises and coordinates the activities of research agents, ensuring alignment "
    "with project goals and efficient execution of tasks. Provides strategic guidance, "
    "oversees progress, and resolves conflicts within the research team.</usage>\n"
    "<sub_agent>\n"
    f"{TavilyAgentMetadata().description}\n"
    f"{WikipediaAgentMetadata().description}\n"
    f"{FileRagAgentMetadata().description}\n"
    "</sub_agent>\n"
    "</agent>\n"
)


class ResearchTeamMetadata(AgentMetadata):
    type: Literal[AvailableAgents.RESEARCH_TEAM] = AvailableAgents.RESEARCH_TEAM
    name: Literal["research_supervisor"] = "research_supervisor"
    description: Final = RESEARCH_TEAM_DESCRIPTION


# Define callback for the research team node
async def research_team_node(state: AgentState, config: RunnableConfig):
    try:
        result = await research_graph.ainvoke(state, config)
        return {"messages": [HumanMessage(content=result["messages"][-1].content, name="research_team")]}
    except Exception as e:
        logger.error(f"Error in executing graph: {str(e)}")
        raise
