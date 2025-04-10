from abc import ABC, abstractmethod
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
        graph: CompiledStateGraph,
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
class BuiltinAgent(BaseAgent):
    def __init__(
        self,
        *,
        id: str,
        graph: CompiledStateGraph,
    ):
        super().__init__(id=id, type=AgentType.BUILTIN, graph=graph)

    async def ainvoke(
        self,
        question: str,
        config: RunnableConfig,
        **kwargs,
    ) -> AgentExecutionResult:
        """
        Execute the agent's graph with given input
        """
        try:
            # Logging
            function_name = "BuiltinAgent.ainvoke =>"
            logger.debug(f"{function_name} Question: {question}")

            # Invoke the graph
            state = {"messages": [HumanMessage(question)]}
            response = await self.graph.ainvoke(input=state, config=config, **kwargs)

            # TODO: handle later
            # state = await self.graph.aget_state(config=config, subgraphs=False)
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
            logger.error(f"{function_name} Has error: {str(e)}")
            raise

    async def astream(
        self,
        question: str,
        config: RunnableConfig,
        **kwargs,
    ) -> MessagesStream:
        try:
            # Logging
            function_name = "BuiltinAgent.async_stream =>"
            logger.debug(f"{function_name} Question: {question}")

            state = {"messages": [HumanMessage(question)]}
            return astream_state(app=self.graph, input_=state, config=config, **kwargs)
        except Exception as e:
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
                config=RunnableConfig(),
                allow_stream_nodes=[LanggraphNodeEnum.AGENT_NODE, LanggraphNodeEnum.GENERATE_NODE],
            )
        except Exception as e:
            logger.error(f"Error in executing graph: {str(e)}")
            raise
