import logging

from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.memory.checkpoint import AsyncPostgresCheckpoint
from app.utils.messages import get_message_prefix, trimmer
from app.prompts.prompt_templates import get_rag_prompt_template
from app.services.models_service import get_openai_model

CHECKPOINTER = AsyncPostgresCheckpoint.get_instance()

logger = logging.getLogger(__name__)

async def create_workflow(tool: BaseTool, tool_name: str):
    # Define the retriever tool
    tools = [tool]

    class AgentState(TypedDict):
        # The add_messages function defines how an update should be processed
        # Default is to replace. add_messages says "append"
        messages: Annotated[Sequence[BaseMessage], add_messages]
        question: str

    async def agent(state):
        """
        Invokes the agent model to generate a response based on the current state. Given
        the question, it will decide to retrieve using the retriever tool, or simply end.
        Args:
            state (messages): The current state
        Returns:
            dict: The updated state with the agent response appended to messages
        """
        print("---CALL AGENT---")
        messages = [HumanMessage(content=state["question"])]

        model = get_openai_model()
        model = model.bind_tools(tools, tool_choice=tool_name)
        response = await model.ainvoke(messages)
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    async def generate(state):
        """
        Generate answer
        Args:
            state (messages): The current state
        Returns:
             dict: The updated state with re-phrased question
        """
        print("---GENERATE---")
        messages = state["messages"]
        messages = await trimmer.ainvoke(messages)
        question = state["question"]

        # Get the documents
        docs = "#Previous Messages:\n"
        docs += "\n\n".join(f"{get_message_prefix(msg)}: {msg.content}" for msg in messages)

        # Get the prompt
        prompt = get_rag_prompt_template()
        llm = get_openai_model()

        # Chain
        rag_chain = prompt | llm | StrOutputParser()

        # Run
        response = await rag_chain.ainvoke({"context": docs, "question": question})
        return {"messages": [response]}

    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the nodes
    workflow.add_node("agent", agent)  # agent
    retrieve = ToolNode(tools)
    workflow.add_node("retrieve", retrieve)  # retrieval
    workflow.add_node("generate", generate)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition,
        {
            "tools": "retrieve",
            END: END,
        },
    )
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    # Compile
    return workflow.compile(checkpointer=CHECKPOINTER)