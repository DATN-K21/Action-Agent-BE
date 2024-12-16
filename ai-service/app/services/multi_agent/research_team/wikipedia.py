import logging
from langchain_community.retrievers import WikipediaRetriever
from langchain_core.tools import create_retriever_tool
from typing import Literal
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from app.services.models_service import get_openai_model
from app.services.multi_agent.utils.helpers import AgentState, AgentMetadata, AvailableAgents
from app.utils.messages import trimmer

logger = logging.getLogger(__name__)

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
    description: Literal[WIKIPEDIA_DESCRIPTION] = WIKIPEDIA_DESCRIPTION

def get_wikipedia_retriever_tool():
    retriever = WikipediaRetriever()
    retriever_tool = create_retriever_tool(
        retriever,
        "wikipedia_retriever_tool",
        "Search and return information from Wikipedia",
    )
    return retriever_tool

async def wikipedia_node(state: AgentState, config: RunnableConfig):
    try:
        wikipedia_tool = get_wikipedia_retriever_tool()
        model_forced_to_wikipedia = get_openai_model().bind_tools(
            [wikipedia_tool],
            tool_choice="wikipedia_retriever_tool"
        )
        messages = await trimmer.ainvoke(state["messages"])
        state["messages"] = messages
        result = await model_forced_to_wikipedia.ainvoke(state["messages"])

        for tool_call in result.tool_calls:
            selected_tool = {"wikipedia_retriever_tool": wikipedia_tool}[tool_call["name"].lower()]
            tool_msg = await selected_tool.ainvoke(tool_call)
            messages.append(tool_msg)

        return {
            "messages": [
                HumanMessage(content=messages[-1].content, name="wikipedia")
            ]
        }
    except Exception as e:
        logger.error(f"Error in execute wikipedia node: {e}")
        raise e
