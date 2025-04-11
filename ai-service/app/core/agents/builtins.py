from typing import Optional

from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import Prompt
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt.tool_node import ToolNode

from app.core import logging
from app.core.agents.base import BaseAgent
from app.core.agents.types import AgentType
from app.core.utils.streaming import astream_state

logger = logging.get_logger(__name__)


class BuiltinAgent(BaseAgent):
    """
    Builtin agent class for handling builtin agents.
    Including:
    - Chat Agent
    - Search Agent
    - RAG Agent
    """

    def __init__(
        self,
        *,
        id: str,
        model: str | LanguageModelLike,
        tools: ToolExecutor | list[BaseTool] | ToolNode,
        prompt: Optional[Prompt] = None,
    ):
        """
        Initialize the builtin agent with the given graph.
        """

        agent_executor = create_react_agent(
            model=model,
            tools=tools,
            prompt=prompt,
        )

        super().__init__(id=id, type=AgentType.BUILTIN, graph=graph)

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
