from enum import Enum
from typing import List, Literal, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, MessagesState
from pydantic import BaseModel

from app.core import logging
from app.utils.messages import trimmer

logger = logging.get_logger(__name__)


class AvailableAgents(str, Enum):
    FILE_RAG = "file_rag"
    TAVILY = "tavily"
    WIKIPEDIA = "wikipedia"
    RESEARCH_TEAM = "research_team"
    TEAMS_MANAGEMENT = "teams_management"


class AgentMetadata(BaseModel):
    type: AvailableAgents
    name: str
    description: str


# The agent state is the input to each node in the graph
class AgentState(MessagesState):
    # The 'next' field indicates where to route to next
    next: str
    # The 'traversal' field contains the chat history
    traversal: list[str]
    # The 'question' field contains the user's question
    question: str
    # The 'retrival_doc' field contains the document to be retrieved
    retrival_doc: str


def make_supervisor_node(llm: BaseChatModel, metas: List[AgentMetadata]):
    members = [meta.name for meta in metas]
    options = ["FINISH"] + members
    meta_json_array = [meta.description for meta in metas]
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}.\n Given the following user request,"
        " respond with the worker to act next.\n Each worker will perform a"
        " task and respond with their results and status.\n When finished,"
        " respond with FINISH.\n If you cannot identify an appropriate worker for the task, respond with FINISH.\n"
        "Details of the workers are as follows: \n"
        f"\n{meta_json_array}\n"
    )

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""

        next: Literal[*options]  # type: ignore

    async def supervisor_node(state: AgentState):
        """An LLM-based router."""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
            ] + state["messages"]
            messages = await trimmer.ainvoke(messages)

            response = await llm.with_structured_output(Router).ainvoke(messages)
            next_ = response["next"]  # type: ignore
            traversal = []

            # Initialize traversal
            if "traversal" in state:
                traversal = state["traversal"]

            # Avoid loop in graph
            if next_ in traversal:
                next_ = END
            traversal.append(next_)

            # Set End node of graph
            if next_ == "FINISH":
                next_ = END

            print("*" * 10 + "SUPERVISOR NODE" + "*" * 10)
            print({"next": next_})

            return {"next": next_, "traversal": traversal}
        except Exception as e:
            logger.error(
                f"[helpers/make_supervisor_node/supervisor_node] Error in supervisor node: {e}"
            )
            raise

    return supervisor_node
