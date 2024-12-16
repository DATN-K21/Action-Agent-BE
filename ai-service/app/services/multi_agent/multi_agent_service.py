import logging

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import MessagesState, StateGraph, START, END

from app.memory.checkpoint import AsyncPostgresCheckpoint
from app.services.multi_agent.teams_management import team_management_node
from app.services.models_service import get_openai_model
from app.prompts.prompt_templates import get_rag_prompt_template
from app.utils.messages import get_message_prefix

logger = logging.getLogger(__name__)

CHECKPOINTER = AsyncPostgresCheckpoint.get_instance()

class AgentState(MessagesState):
    question: str
    retrival_doc: str

def create_workflow():
    async def generate(state):
        messages = state["messages"]
        question = state["question"]
        retrival_doc = state["retrival_doc"]

        # Get the documents
        docs = "#Previous Messages:\n"
        docs += "\n\n".join(f"{get_message_prefix(msg)}: {msg.content}" for msg in messages)
        docs += f"\n\n#Retrieval Document: {retrival_doc}"

        # Prompt
        prompt = get_rag_prompt_template()

        # Model
        model = get_openai_model()

        # Chain
        rag_chain = prompt | model | StrOutputParser()

        # Run
        response = await rag_chain.ainvoke({"context": docs, "question": question})
        return {"messages": [AIMessage(content=response)]}


    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the nodes we will cycle between
    workflow.add_node("teams_management", team_management_node)  # Integrating agents
    workflow.add_node("generate", generate)  # Generating a response after we know the documents are relevant

    # Call agent node to decide to retrieve or not
    workflow.add_edge(START, "teams_management")
    workflow.add_edge(
        "teams_management",
        "generate"
    )
    workflow.add_edge("generate", END)

    # Compile
    graph = workflow.compile(checkpointer=CHECKPOINTER)

    return graph


async def execute_multi_agent(thread_id: str, user_input: str, max_recursion: int = 10):
    config = {"recursion_limit": max_recursion, "configurable": {"thread_id": thread_id}}
    query = HumanMessage(content=user_input)

    try:
        graph = create_workflow()
        result = await graph.ainvoke(
                {
                    "messages": [query],
                    "question": user_input
                },
                config
        )
        return result["messages"][-1].content
    except Exception as e:
        logger.error(f"Error in execute graph of multi_agent: {str(e)}")
        raise e