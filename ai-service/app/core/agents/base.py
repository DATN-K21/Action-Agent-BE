from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledGraph
from langgraph.types import StateSnapshot

from app.core import logging
from app.core.agents.types import AgentType
from app.core.models.agent_models import AgentExecutionResult, AgentInterruptHandlingResult
from app.core.utils.streaming import MessagesStream

logger = logging.get_logger(__name__)


###################################################################################
##################### BaseAgent Class #############################################
###################################################################################
class BaseAgent(ABC):
    """
    Base class for all types of agents.
    This class defines the common interface for all type of agents.
    """

    def __init__(
        self,
        *,
        id: str,
        type: AgentType,
        graph: CompiledGraph,
    ):
        self.id = id
        self.type = type
        self.graph = graph

    async def get_graph_state(
        self,
        config: RunnableConfig,
        subgraphs: bool = False,
    ) -> StateSnapshot:
        """
        Get the state of the agent's graph for the given config.
        """
        return await self.graph.aget_state(
            config=config,
            subgraphs=subgraphs,
        )

    @abstractmethod
    async def ainvoke(
        self,
        question: str,
        config: RunnableConfig,
        **kwargs,
    ) -> AgentExecutionResult:
        """Execute the agent's graph with given input"""
        pass

    @abstractmethod
    async def astream(
        self,
        question: str,
        config: RunnableConfig,
        **kwargs,
    ) -> MessagesStream:
        """
        Stream the agent's graph with given input
        """
        pass

    ########################## TODO: later ##########################################
    @abstractmethod
    async def async_handle_chat_interrupt(
        self,
        execute: bool,
        tool_calls: Optional[list[ToolCall]] = None,
        thread_id: Optional[str] = None,
        max_recursion: int = 10,
    ) -> AgentInterruptHandlingResult:
        """
        Handle the interrupt in the agent's graph
        """
        pass

    @abstractmethod
    async def async_handle_stream_interrupt(
        self,
        execute: bool,
        tool_calls: Optional[list[ToolCall]] = None,
        thread_id: Optional[str] = None,
        max_recursion: int = 10,
    ) -> MessagesStream:
        """
        Stream the agent's graph with given input
        """
        pass

    #####################################################################################


########################################################################################
######################## BuiltinAgent Class ############################################
########################################################################################
