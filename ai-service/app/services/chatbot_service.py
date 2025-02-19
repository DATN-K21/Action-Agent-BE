import traceback

from langchain_core.messages import AIMessage, HumanMessage, filter_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph

from app.core import logging
from app.memory.checkpoint import AsyncPostgresSaver
from app.schemas.base import ResponseWrapper
from app.schemas.chat import ChatResponse
from app.services.model_service import get_openai_model
from app.utils.messages import trimmer
from app.utils.streaming import MessagesStream, astream_state

logger = logging.get_logger(__name__)


class ChatbotService:
    def __init__(self, checkpointer: AsyncPostgresSaver):
        self.checkpointer = checkpointer

    async def create_workflow(self):
        async def call_model(state: MessagesState):
            model = get_openai_model()
            messages = filter_messages(state["messages"], include_types=[HumanMessage, AIMessage])
            messages = trimmer.invoke(messages)
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a helpful assistant. Answer the following question:",
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )

            chain = prompt | model

            try:
                response = await chain.ainvoke({"messages": messages})
            except Exception as e:
                logger.error(f"[chatbot_service/create_workflow/call_model] Error in calling model: {str(e)}")
                raise e

            return {"messages": [response]}

        # Define the graph
        workflow = StateGraph(state_schema=MessagesState)
        workflow.add_edge(START, "model")
        workflow.add_node("model", call_model)
        workflow.add_edge("model", END)
        graph = workflow.compile(checkpointer=self.checkpointer)
        return graph

    @logging.log_function_inputs(logger)
    async def execute_chatbot(self, thread_id: str, user_input: str) -> ResponseWrapper[ChatResponse]:
        try:
            config = RunnableConfig(configurable={"thread_id": thread_id})
            query = user_input
            input_messages = [HumanMessage(query)]
            graph = await self.create_workflow()
            response = await graph.ainvoke({"messages": input_messages}, config)
            content = response["messages"][-1].content

            if not content:
                return ResponseWrapper.wrap(status=404, message="No response found")

            response_data = ChatResponse(threadId=thread_id, output=content)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def stream_chatbot(self, thread_id: str, user_input: str) -> MessagesStream:
        try:
            config = RunnableConfig(configurable={"thread_id": thread_id})
            query = user_input
            input_messages = [HumanMessage(query)]
            graph = await self.create_workflow()
            return astream_state(graph, {"messages": input_messages}, config)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            return self.error_stream()

    async def error_stream(self) -> MessagesStream:
        error_message = AIMessage("An error occurred. Please try again later.")
        yield [error_message]
        return
