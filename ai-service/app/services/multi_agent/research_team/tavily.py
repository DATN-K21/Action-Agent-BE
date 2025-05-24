from typing import Final, Literal

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from pydantic import SecretStr

from app.core import logging
from app.core.settings import env_settings
from app.services.llm_service import get_llm_chat_model
from app.services.multi_agent.utils.helpers import AgentMetadata, AgentState, AvailableAgents

logger = logging.get_logger(__name__)

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
    description: Final = TAVILY_DESCRIPTION


api_wrapper = TavilySearchAPIWrapper(tavily_api_key=SecretStr(env_settings.TOOL_TAVILY_API_KEY))
tavily_tool = TavilySearchResults(max_results=MAX_RESULTS, name="tavily_search_tool", api_wrapper=api_wrapper)


async def tavily_node(state: AgentState, config: RunnableConfig):
    try:
        model_forced_to_tavily = get_llm_chat_model().bind_tools([tavily_tool], tool_choice="tavily_search_tool")
        result = await model_forced_to_tavily.ainvoke([state["question"]])
        messages = state["messages"]

        for tool_call in result.tool_calls:
            selected_tool = {"tavily_search_tool": tavily_tool}[tool_call["name"].lower()]
            tool_msg = await selected_tool.ainvoke(tool_call)
            messages.append(tool_msg)

        return {"messages": [HumanMessage(content=messages[-1].content, name="tavily")]}
    except Exception as e:
        logger.error(f"Error in executing tavily node: {e}")
        raise
