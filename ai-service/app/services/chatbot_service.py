import logging
from langgraph.graph import START, StateGraph, MessagesState
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import trim_messages, HumanMessage

from app.services.models_service import get_openai_model, MAX_TOKENS
from app.memory.checkpoint import AsyncPostgresCheckpoint
from app.utils.exceptions import ExecutingException

logger = logging.getLogger(__name__)

CHECKPOINTER = AsyncPostgresCheckpoint.get_instance()

async def create_workflow():

    async def call_model(state: MessagesState):
        model = get_openai_model()

        state = trim_messages(
            state["messages"],
            max_tokens=MAX_TOKENS,
            strategy="last",
            token_counter=model,
            include_system=True,
            allow_partial=True,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful assistant. Answer the following question:"
                ),
                MessagesPlaceholder(variable_name="messages")
            ]
        )

        chain = prompt | model
        response = await chain.ainvoke(state)

        return {"messages": response}


    # Define the graph
    workflow = StateGraph(state_schema=MessagesState)
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)
    graph = workflow.compile(checkpointer=CHECKPOINTER)
    return graph

async def execute_chatbot(thread_id: str, user_input: str):
    config = {"configurable": {"thread_id": f"{thread_id}"}}
    query = user_input
    input_messages = [HumanMessage(query)]
    try:
        graph = await create_workflow()
        response = await graph.ainvoke({"messages": input_messages}, config)
        content = response["messages"][-1].content
        return content
    except Exception as e:
        logger.error(f"Error in execute graph of chatbot: {str(e)}")
        raise e