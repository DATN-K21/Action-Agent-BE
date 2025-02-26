from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from structlog.stdlib import BoundLogger

from app.core import logging


class BaseAgent(ABC):
    def __init__(
            self,
            graph: CompiledStateGraph,
            logger: Optional[BoundLogger] = None,
            name: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None,
    ):
        self.graph = graph
        self.logger = logging.get_logger(self.__class__.__name__) if logger is None else logger
        self.name = name
        self.config = config


    @abstractmethod
    def async_get_state(self, config: Dict[str, Any]):
        """Build and return the current LangGraph state"""
        pass


    @abstractmethod
    async def async_execute(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's graph with given input"""
        pass


    @abstractmethod
    async def async_handle_interrupt_execute(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's graph with given input"""
        pass


    @abstractmethod
    async def async_stream(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Stream the agent's graph with given input"""
        pass


    @abstractmethod
    async def async_handle_interrupt_stream(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Stream the agent's graph with given input"""
        pass