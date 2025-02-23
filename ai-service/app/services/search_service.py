import traceback

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from app.core import logging
from app.schemas.base import ResponseWrapper
from app.schemas.chat import ChatResponse
from app.services.retrieval_base import create_workflow
from app.utils.streaming import MessagesStream, astream_state

logger = logging.get_logger(__name__)


class SearchService:
    def __init__(self):
        self.tavily_tool = TavilySearchResults(max_results=5, name="tavily_search_tool")

    @logging.log_function_inputs(logger)
    async def execute_search(self, thread_id: str, user_input: str, max_recursion: int = 5) -> ResponseWrapper[ChatResponse]:
        """Chat with the search tool."""
        try:
            graph = create_workflow(tool=self.tavily_tool, tool_name="tavily_search_tool")
            state = {"messages": [HumanMessage(user_input)], "question": user_input}
            config = RunnableConfig(
                recursion_limit=max_recursion,
                configurable={"thread_id": thread_id},
            )
            response = await graph.ainvoke(state, config)
            last_message = response["messages"][-1].content
            response_data = ChatResponse(thread_id=thread_id, output=last_message) if last_message else None

            if response_data is None:
                return ResponseWrapper.wrap(status=404, message="No response found")

            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def stream_search(self, thread_id: str, user_input: str, max_recursion: int = 5) -> MessagesStream:
        try:
            graph = create_workflow(tool=self.tavily_tool, tool_name="tavily_search_tool")
            state = {"messages": [HumanMessage(user_input)], "question": user_input}
            config = RunnableConfig(
                recursion_limit=max_recursion,
                configurable={"thread_id": thread_id},
            )
            return astream_state(graph, state, config)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            return self.error_stream()

    async def error_stream(self) -> MessagesStream:
        error_message = AIMessage("An error occurred. Please try again later.")
        yield [error_message]
        return
