import logging
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage

from app.services.retrieval_base_service import create_workflow

MAX_RESULTS = 5

logger = logging.getLogger(__name__)

async def execute_search(thread_id: str, user_input: str, max_recursion: int = 5):
    try:
        tavily_tool = TavilySearchResults(max_results=MAX_RESULTS, name="tavily_search_tool")
        graph = await create_workflow(tool=tavily_tool, tool_name="tavily_search_tool")
        state = {"messages": [HumanMessage(user_input)], "question": user_input}
        config = {"recursion_limit": max_recursion, "configurable": {"thread_id": thread_id}}
        response = await graph.ainvoke(state, config)
        return response["messages"][-1].content
    except Exception as e:
        logger.error(f"Error in execute graph of RAG bot: {str(e)}")
        raise e