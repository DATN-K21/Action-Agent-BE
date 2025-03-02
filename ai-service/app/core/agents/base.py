from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import uuid4

from langgraph.graph.state import CompiledStateGraph
from langgraph.types import StateSnapshot
from structlog.stdlib import BoundLogger

from app.core import logging
from app.core.models.agent_models import AgentExecutionResult, AgentInterruptHandlingResult
from app.utils.enums import HumanAction
from app.utils.streaming import MessagesStream


class BaseAgent(ABC):
    def __init__(
        self,
        graph: CompiledStateGraph,
        logger: Optional[BoundLogger] = None,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.id = str(uuid4())
        self.graph = graph
        self.logger = logging.get_logger(self.__class__.__name__) if logger is None else logger
        self.name = name
        self.config = config

    async def async_get_state(self, thread_id: str) -> StateSnapshot:
        state = await self.graph.aget_state(config={"configurable": {"thread_id": thread_id}})
        return state

    @abstractmethod
    async def async_execute(
        self,
        question: str,
        thread_id: Optional[str] = None,
        max_recursion: int = 10,
    ) -> AgentExecutionResult:
        """Execute the agent's graph with given input"""
        pass

    @abstractmethod
    async def async_handle_execution_interrupt(
        self,
        action: HumanAction,
        thread_id: Optional[str] = None,
        max_recursion: int = 10,
    ) -> AgentInterruptHandlingResult:
        """Handle the interrupt in the agent's graph"""
        pass

    @abstractmethod
    async def async_stream(self, question: str, thread_id: Optional[str] = None, max_recursion: int = 10) -> MessagesStream:
        """Stream the agent's graph with given input"""
        pass

    @abstractmethod
    async def async_handle_interrupt_stream(
        self,
        action: HumanAction,
        thread_id: Optional[str] = None,
        max_recursion: int = 10,
    ) -> MessagesStream:
        """Stream the agent's graph with given input"""
        pass
