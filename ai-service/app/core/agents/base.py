from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Optional

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, StateSnapshot

from app.core import logging
from app.core.graph.builder import HumanEditingData, ToolCall
from app.core.models.agent_models import AgentExecutionResult, AgentInterruptHandlingResult
from app.core.utils.streaming import LanggraphNodeEnum, MessagesStream, astream_state

logger = logging.get_logger(__name__)


class AgentType(StrEnum):
    """
    Enum for agent types.
    """

    MULTI = "multi"
    BUILTIN = "builtin"
    COMPOSIO = "composio"
    MCP = "mcp"


###################################################################################
##################### BaseAgent Class #############################################
###################################################################################
class BaseCompiledAgent(ABC):
    """
    Base class for all types of agents.
    This class defines the common interface for all agents.
    """
    def __init__(
        self,
        id: str,
        type: AgentType,
        graph: CompiledStateGraph,
        config: RunnableConfig,
    ):
        self.id = id
        self.type = type
        self.graph = graph
        self.config = config

    async def get_state_snapshot(self) -> StateSnapshot:
        """
        Get the state of an agent/thread.
        """
        return await self.graph.aget_state(self.config)

    @abstractmethod
    async def ainvoke(
        self,
        question: str,
    ) -> AgentExecutionResult:
        """Execute the agent's graph with given input"""
        pass

    @abstractmethod
    async def astream(
        self,
        question: str,
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
class BuiltinAgent(BaseCompiledAgent):
    def __init__(
        self,
        id: str,
        graph: CompiledStateGraph,
        config: RunnableConfig,
    ):
        super().__init__(id=id, type=AgentType.BUILTIN, graph=graph, config=config)

    async def ainvoke(
        self,
        question: str,
    ) -> AgentExecutionResult:
        """
        Execute the agent's graph with given input
        """
        try:
            state = {"messages": [HumanMessage(question)]}
            response = await self.graph.ainvoke(input=state, config=self.config)

            state = await self.graph.aget_state(self.config)

            # TODO: handle later
            # if len(state.tasks) > 0:
            #     task = state.tasks[-1]
            #     if len(task.interrupts) > 0:
            #         interrupt = task.interrupts[-1]
            #         return AgentExecutionResult(
            #             interrupted=True,
            #             output=interrupt.value,
            #         )

            return AgentExecutionResult(
                interrupted=False,
                output=response["messages"][-1].content,
            )
        except Exception as e:
            function_name = "BuiltinAgent.ainvoke"
            logger.error(f"{function_name} Has error: {str(e)}")
            raise

    async def async_stream(
        self,
        question: str,
    ) -> MessagesStream:
        try:
            state = {"messages": [HumanMessage(question)]}
            return astream_state(app=self.graph, input_=state, config=self.config)
        except Exception as e:
            function_name = "BuiltinAgent.async_stream"
            logger.error(f"{function_name} Has error: {str(e)}")
            raise

    ############################ TODO: later ###########################################
    async def async_handle_chat_interrupt(
        self,
        execute: bool,
        tool_calls: Optional[list[ToolCall]] = None,
        thread_id: Optional[str] = None,
        timezone: Optional[str] = None,
        max_recursion: Optional[int] = None,
    ) -> AgentInterruptHandlingResult:
        try:
            response = await self.graph.ainvoke(
                Command(resume=HumanEditingData(execute=execute, tool_calls=tool_calls).model_dump()), config=self.config
            )

            return AgentInterruptHandlingResult(
                output=response["messages"][-1].content,
            )

        except Exception as e:
            logger.error(f"Error in executing graph: {str(e)}")
            raise

    async def async_handle_stream_interrupt(
        self,
        execute: bool,
        tool_calls: Optional[list[ToolCall]] = None,
        thread_id: Optional[str] = None,
        timezone: Optional[str] = None,
        max_recursion: Optional[int] = None,
    ) -> MessagesStream:
        try:
            return astream_state(
                app=self.graph,
                input_=Command(resume=HumanEditingData(execute=execute, tool_calls=tool_calls).model_dump()),
                config=self.config,
                allow_stream_nodes=[LanggraphNodeEnum.AGENT_NODE, LanggraphNodeEnum.GENERATE_NODE],
            )
        except Exception as e:
            logger.error(f"Error in executing graph: {str(e)}")
            raise


#########################################################################################