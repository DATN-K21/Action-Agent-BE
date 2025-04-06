from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from structlog.stdlib import BoundLogger

from app.core import logging
from app.core.agents.base import BaseAgent
from app.core.graph.base import HumanEditingData, ToolCall
from app.core.models.agent_models import AgentExecutionResult, AgentInterruptHandlingResult
from app.core.utils.config_helper import get_invocation_config
from app.core.utils.streaming import MessagesStream, astream_state, LanggraphNodeEnum


class Agent(BaseAgent):
    def __init__(
            self,
            graph: CompiledStateGraph,
            logger: Optional[BoundLogger] = None,
            name: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None,
    ):
        if logger is None:
            logger = logging.get_logger(self.__class__.__name__)
        super().__init__(graph=graph, logger=logger, name=name, config=config)

    async def async_chat(
            self,
            question: str,
            thread_id: Optional[str] = None,
            timezone: Optional[str] = None,
            max_recursion: Optional[int] = None,
    ) -> AgentExecutionResult:
        try:
            state = {"messages": [HumanMessage(question)], "question": question}
            config = get_invocation_config(
                thread_id=thread_id,
                timezone=timezone,
                recursion_limit=max_recursion,
            )
            response = await self.graph.ainvoke(input=state, config=config)

            state = await self.graph.aget_state(config=config)
            if len(state.tasks) > 0:
                task = state.tasks[-1]
                if len(task.interrupts) > 0:
                    interrupt = task.interrupts[-1]
                    return AgentExecutionResult(
                        interrupted=True,
                        output=interrupt.value,
                    )

            return AgentExecutionResult(
                interrupted=False,
                output=response["messages"][-1].content,
            )
        except Exception as e:
            self.logger.error(f"Error in executing graph: {str(e)}")
            raise

    async def async_handle_chat_interrupt(
            self,
            execute: bool,
            tool_calls: Optional[list[ToolCall]] = None,
            thread_id: Optional[str] = None,
            timezone: Optional[str] = None,
            max_recursion: Optional[int] = None,
    ) -> AgentInterruptHandlingResult:
        try:
            config = get_invocation_config(
                thread_id=thread_id,
                timezone=timezone,
                recursion_limit=max_recursion,
            )
            response = await self.graph.ainvoke(
                Command(
                    resume=HumanEditingData(
                        execute=execute,
                        tool_calls=tool_calls
                    ).model_dump()
                ),
                config=config
            )

            return AgentInterruptHandlingResult(
                output=response["messages"][-1].content,
            )

        except Exception as e:
            self.logger.error(f"Error in executing graph: {str(e)}")
            raise

    async def async_stream(
            self, question: str,
            thread_id: Optional[str] = None,
            timezone: Optional[str] = None,
            max_recursion: Optional[int] = None,
    ) -> MessagesStream:
        try:
            state = {"messages": [HumanMessage(question)], "question": question}
            config = get_invocation_config(
                thread_id=thread_id,
                timezone=timezone,
                recursion_limit=max_recursion,
            )
            return astream_state(app=self.graph, input_=state, config=config)
        except Exception as e:
            self.logger.error(f"Error in executing graph: {str(e)}")
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
            config = get_invocation_config(
                thread_id=thread_id,
                timezone=timezone,
                recursion_limit=max_recursion,
            )
            return astream_state(
                app=self.graph,
                input_=Command(
                    resume=HumanEditingData(
                        execute=execute,
                        tool_calls=tool_calls
                    ).model_dump()
                ),
                config=config,
                allow_stream_nodes=[LanggraphNodeEnum.AGENT_NODE, LanggraphNodeEnum.GENERATE_NODE],
            )
        except Exception as e:
            self.logger.error(f"Error in executing graph: {str(e)}")
            raise
