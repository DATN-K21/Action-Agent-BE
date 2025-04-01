from typing import Final, Literal

from langchain_community.retrievers.wikipedia import WikipediaRetriever
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import create_retriever_tool

from app.core import logging
from app.services.model_service import AIModelService
from app.services.multi_agent.utils.helpers import AgentMetadata, AgentState, AvailableAgents

logger = logging.get_logger(__name__)

WIKIPEDIA_DESCRIPTION = """
\n<agent>\n
<name>wikipedia</name>\n
<usage>Use the Wikipedia agent to search and retrieve information directly from Wikipedia, 
accessing comprehensive summaries and details from its extensive knowledge base.</usage>\n
</agent>\n
"""


class WikipediaAgentMetadata(AgentMetadata):
    type: Literal[AvailableAgents.WIKIPEDIA] = AvailableAgents.WIKIPEDIA
    name: Literal["wikipedia"] = "wikipedia"
    description: Final = WIKIPEDIA_DESCRIPTION


def get_wikipedia_retriever_tool():
    retriever = WikipediaRetriever(wiki_client=None)
    retriever_tool = create_retriever_tool(
        retriever,
        "wikipedia_retriever_tool",
        "Search and return information from Wikipedia",
    )
    return retriever_tool


async def wikipedia_node(state: AgentState, config: RunnableConfig):
    try:
        wikipedia_tool = get_wikipedia_retriever_tool()
        model_forced_to_wikipedia = AIModelService.get_ai_model().bind_tools([wikipedia_tool],
                                                                             tool_choice="wikipedia_retriever_tool")
        result = await model_forced_to_wikipedia.ainvoke([state["question"]])
        messages = state["messages"]

        for tool_call in result.tool_calls:  # type: ignore
            selected_tool = {"wikipedia_retriever_tool": wikipedia_tool}[tool_call["name"].lower()]
            tool_msg = await selected_tool.ainvoke(tool_call)
            messages.append(tool_msg)

        return {"messages": [HumanMessage(content=messages[-1].content, name="wikipedia")]}
    except Exception as e:
        logger.error(f"Error in executing wikipedia node: {e}")
        raise
