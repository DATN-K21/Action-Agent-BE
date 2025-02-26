from typing import Optional, Dict, Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from structlog.stdlib import BoundLogger

from app.core import logging
from app.core.agents.base import BaseAgent
from app.core.utils.config_helper import get_invoking_config
from app.utils.enums import HumanAction
from app.utils.streaming import astream_state



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


    async def async_get_state(self, config: Dict[str, Any]):
        return await self.graph.aget_state(config)


    async def async_execute(
            self,
            question: str,
            thread_id: Optional[str]=None,
            user_id: Optional[str] = None,
            connected_account_id: Optional[str] = None,
            max_recursion: int = 10,
    ) -> Dict[str, Any]:
        try:
            state = {"messages": [HumanMessage(question)], "question": question}
            config = get_invoking_config(
                thread_id=thread_id,
                user_id=user_id,
                connected_account_id=connected_account_id,
                recursion_limit=max_recursion,
            )
            response = await self.graph.ainvoke(state, config)

            state = await self.graph.aget_state(config)
            if len(state.tasks) > 0:
                task = state.tasks[-1]
                if len(task.interrupts) > 0:
                    interrupt = task.interrupts[-1]
                    return {
                        "interrupted": True,
                        "output": interrupt.value,
                    }
            return {
                "interrupted": False,
                "output": response["messages"][-1].content,
            }
        except Exception as e:
            self.logger.error(f"[async_execute] Error in executing graph: {str(e)}")
            raise


    async def async_handle_interrupt_execute(
            self,
            action: HumanAction,
            thread_id: Optional[str] = None,
            user_id: Optional[str] = None,
            connected_account_id: Optional[str] = None,
            max_recursion: int = 10,
    ) -> Dict[str, Any]:
        try:
            config = get_invoking_config(
                thread_id=thread_id,
                user_id=user_id,
                connected_account_id=connected_account_id,
                recursion_limit=max_recursion,
            )
            response = await self.graph.ainvoke(Command(resume=action), config)

            return response["messages"][-1].content
        except Exception as e:
            self.logger.error(f"[async_handle_interrupt_execute] Error in executing graph: {str(e)}")
            raise


    async def async_stream(
            self,
            question: str,
            thread_id: Optional[str] =None,
            user_id: Optional[str] = None,
            connected_account_id: Optional[str] = None,
            max_recursion: int = 10
    ):
        try:
            state = {"messages": [HumanMessage(question)], "question": question}
            config = get_invoking_config(
                thread_id=thread_id,
                user_id=user_id,
                connected_account_id=connected_account_id,
                recursion_limit=max_recursion,
            )
            return astream_state(self.graph, state, config)
        except Exception as e:
            self.logger.error(f"[async_stream] Error in executing graph: {str(e)}")
            raise


    async def async_handle_interrupt_stream(
            self,
            action: HumanAction,
            thread_id: Optional[str] = None,
            user_id: Optional[str] = None,
            connected_account_id: Optional[str] = None,
            max_recursion: int = 10,
    ):
        try:
            config = get_invoking_config(
                thread_id=thread_id,
                user_id=user_id,
                connected_account_id=connected_account_id,
                recursion_limit=max_recursion,
            )
            return astream_state(self.graph, Command(resume=action), config)
        except Exception as e:
            self.logger.error(f"[async_stream] Error in executing graph: {str(e)}")
            raise