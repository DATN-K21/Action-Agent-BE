import traceback

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from app.core import logging
from app.memory.checkpoint import AsyncPostgresSaver
from app.prompts.prompt_templates import get_retriever_prompt_template
from app.schemas.base import ResponseWrapper
from app.schemas.chat import ChatResponse
from app.services.model_service import get_openai_model
from app.services.multi_agent.teams_management import team_management_node
from app.services.multi_agent.utils.helpers import AgentState
from app.utils.messages import get_message_prefix, trimmer
from app.utils.streaming import MessagesStream, astream_state

logger = logging.get_logger(__name__)


class MultiAgentService:
    def __init__(self, checkpointer: AsyncPostgresSaver):
        self.checkpointer = checkpointer

    def create_workflow(self):
        async def generate(state):
            messages = await trimmer.ainvoke(state["messages"])
            question = state["question"]
            retrival_doc = state["retrival_doc"]

            # Get the documents
            docs = "#Previous Messages:\n"
            docs += "\n\n".join(f"##{get_message_prefix(msg)}: {msg.content}" for msg in messages)
            docs += f"\n\n#Retrieval Document: {retrival_doc}"

            # Prompt
            prompt = get_retriever_prompt_template()

            # Model
            model = get_openai_model()

            # Chain
            rag_chain = prompt | trimmer | model

            # Run
            response = await rag_chain.ainvoke({"context": docs, "question": question})
            return {"messages": [response]}

        # Define a new graph
        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("teams_management", team_management_node)  # Integrating agents
        workflow.add_node("generate", generate)  # Generating a response after we know the documents are relevant

        # Call agent node to decide to retrieve or not
        workflow.add_edge(START, "teams_management")
        workflow.add_edge("teams_management", "generate")
        workflow.add_edge("generate", END)

        # Compile
        graph = workflow.compile(checkpointer=self.checkpointer)
        return graph

    @logging.log_function_inputs(logger)
    async def execute_multi_agent(
        self, thread_id: str, user_input: str, max_recursion: int = 10
    ) -> ResponseWrapper[ChatResponse]:
        try:
            config = RunnableConfig(
                recursion_limit=max_recursion,
                configurable={"thread_id": thread_id},
            )
            query = HumanMessage(content=user_input)
            graph = self.create_workflow()
            result = await graph.ainvoke({"messages": [query], "question": user_input}, config)
            content = result["messages"][-1].content
            if not content:
                return ResponseWrapper.wrap(status=404, message="No response found")
            response_data = ChatResponse(threadId=thread_id, output=content)
            return ResponseWrapper.wrap(status=200, data=response_data)
        except Exception as e:
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def stream_multi_agent(self, thread_id: str, user_input: str, max_recursion: int = 10) -> MessagesStream:
        try:
            config = RunnableConfig(
                recursion_limit=max_recursion,
                configurable={"thread_id": thread_id},
            )
            query = HumanMessage(content=user_input)
            graph = self.create_workflow()
            state = {"messages": [query], "question": user_input}
            return astream_state(graph, state, config)
        except Exception as e:
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            return self.error_stream()

    async def error_stream(self) -> MessagesStream:
        error_message = AIMessage("An error occurred. Please try again later.")
        yield [error_message]
        return
