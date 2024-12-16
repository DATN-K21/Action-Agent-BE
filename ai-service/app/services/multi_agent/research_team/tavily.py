import logging
from langchain_community.tools.tavily_search import TavilySearchResults

from typing import Literal
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from app.services.models_service import get_openai_model
from app.services.multi_agent.utils.helpers import AgentState, AgentMetadata, AvailableAgents
from app.utils.messages import trimmer

logger = logging.getLogger(__name__)

MAX_RESULTS = 5

TAVILY_DESCRIPTION = """
\n<agent>\n
<name>tavily</name>\n
<usage>Use the Tavily search engine to retrieve high-quality, AI-optimized answers and resources from 
a diverse range of web-based information, ensuring accurate and context-aware search results.</usage>\n
</agent>\n
"""

class TavilyAgentMetadata(AgentMetadata):
    type: Literal[AvailableAgents.TAVILY] = AvailableAgents.TAVILY
    name: Literal["tavily"] = "tavily"
    description: Literal[TAVILY_DESCRIPTION] = TAVILY_DESCRIPTION

tavily_tool = TavilySearchResults(max_results=MAX_RESULTS, name="tavily_search_tool")

async def tavily_node(state: AgentState, config: RunnableConfig):
    try:
        model_forced_to_tavily = get_openai_model().bind_tools([tavily_tool], tool_choice="tavily_search_tool")
        messages = await trimmer.ainvoke(state["messages"])
        state["messages"] = messages
        result = await model_forced_to_tavily.ainvoke(state["messages"])

        for tool_call in result.tool_calls:
            selected_tool = {"tavily_search_tool": tavily_tool}[tool_call["name"].lower()]
            tool_msg = await selected_tool.ainvoke(tool_call)
            messages.append(tool_msg)

        return {
            "messages": [
                HumanMessage(content=messages[-1].content, name="tavily")
            ]
        }
    except Exception as e:
        logger.error(f"Error in execute tavily node: {e}")
        raise e