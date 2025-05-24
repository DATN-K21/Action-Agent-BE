from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import uuid4

from langgraph.graph.state import CompiledStateGraph
from langgraph.types import StateSnapshot

from app.core.graph.base import ToolCall
from app.core.models.agent_models import AgentExecutionResult, AgentInterruptHandlingResult
from app.core.utils.streaming import MessagesStream


class BaseAgent(ABC):
    def __init__(
            self,
            graph: CompiledStateGraph,
            name: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None,
    ):
        self.id = str(uuid4())
        self.graph = graph
        self.name = name
        self.config = config

    async def async_get_state(self, thread_id: str) -> StateSnapshot:
        state = await self.graph.aget_state(config={"configurable": {"thread_id": thread_id}})
        return state

    @abstractmethod
    async def async_chat(
            self,
            question: str,
            thread_id: Optional[str] = None,
            recursion_limit: int = 20,
    ) -> AgentExecutionResult:
        """Execute the agent's graph with given input"""
        pass

    @abstractmethod
    async def async_handle_chat_interrupt(
            self,
            execute: bool,
            tool_calls: Optional[list[ToolCall]] = None,
            thread_id: Optional[str] = None,
            recursion_limit: int = 20,
    ) -> AgentInterruptHandlingResult:
        """Handle the interrupt in the agent's graph"""
        pass

    @abstractmethod
    async def async_stream(
            self,
            question: str,
            thread_id: Optional[str] = None,
            recursion_limit: int = 20,
    ) -> MessagesStream:
        """Stream the agent's graph with given input"""
        pass

    @abstractmethod
    async def async_handle_stream_interrupt(
            self,
            execute: bool,
            tool_calls: Optional[list[ToolCall]] = None,
            thread_id: Optional[str] = None,
            recursion_limit: int = 20,
    ) -> MessagesStream:
        """Stream the agent's graph with given input"""
        pass
