import traceback

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import create_retriever_tool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core import logging
from app.schemas.base import ResponseWrapper
from app.schemas.chat import ChatResponse
from app.services.retrieval_base import create_workflow
from app.utils.streaming import MessagesStream, astream_state
from app.utils.uploading import vstore

logger = logging.get_logger(__name__)


class RagService:
    def __init__(self, checkpointer: AsyncPostgresSaver):
        self.checkpointer = checkpointer

    def get_retriever(self, thread_id: str):
        return vstore.as_retriever(
            search_kwargs={"filter": {"namespace": {"$in": [thread_id]}}},
        )

    def get_retriever_tool(self, thread_id: str):
        return create_retriever_tool(
            self.get_retriever(thread_id),
            "retriever_tool",
            "Search and return information from the most relevant documents",
        )

    @logging.log_function_inputs(logger)
    async def execute_rag(self, thread_id: str, user_input: str, max_recursion: int = 5) -> ResponseWrapper[ChatResponse]:
        try:
            retriever_tool = self.get_retriever_tool(thread_id)
            graph = create_workflow(tool=retriever_tool, tool_name="retriever_tool")
            state = {"messages": [HumanMessage(user_input)], "question": user_input}
            config = RunnableConfig(
                recursion_limit=max_recursion,
                configurable={"thread_id": thread_id},
            )
            response = await graph.ainvoke(state, config)
            content = response["messages"][-1].content
            response_data = ChatResponse(threadId=thread_id, output=content) if content else None
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def stream_rag(self, thread_id: str, user_input: str, max_recursion: int = 5) -> MessagesStream:
        try:
            retriever_tool = self.get_retriever_tool(thread_id)
            graph = create_workflow(tool=retriever_tool, tool_name="retriever_tool")
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
