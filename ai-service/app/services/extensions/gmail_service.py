from typing import Callable, Sequence, Union

from composio_langgraph import Action
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

from app.core import logging
from app.core.settings import env_settings
from app.services.extensions.composio_service import ComposioService
from app.services.extensions.multiple_tools_base import create_multiple_tools_workflow
from app.utils.enums import HumanAction
from app.utils.streaming import astream_state

logger = logging.get_logger(__name__)


def _send_email_schema_processor(schema: dict) -> dict:
    # Not support attachment in send email schema
    del schema["attachment"]
    return schema


def _fetch_emails_post_processor(output_data: dict) -> dict:
    # Abbreviate the output data
    if output_data["successfull"]:
        for message in output_data["data"]["response_data"]["messages"]:
            del message["attachmentList"]
            del message["payload"]

    return output_data


class GmailService:
    _instance = None
    _app_enum = ComposioService.get_app_enum("GMAIL")
    _redirect_url = env_settings.COMPOSIO_REDIRECT_URL
    _supported_actions = [
        Action.GMAIL_SEND_EMAIL,
        Action.GMAIL_FETCH_EMAILS,
        Action.GMAIL_REPLY_TO_THREAD,
        Action.GMAIL_SEARCH_PEOPLE,
        Action.GMAIL_GET_CONTACTS,
        Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID,
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GmailService, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True

    @classmethod
    def initialize_connection(cls, user_id: str):
        result = ComposioService.initialize_app_connection(user_id, cls._app_enum, cls._redirect_url)
        return result

    @classmethod
    def logout(cls, connected_account_id: str):
        return ComposioService.delete_connection(connected_account_id)

    @classmethod
    def get_actions(cls):
        toolset = ComposioService.get_toolset()
        tools = toolset.get_tools(actions=cls._supported_actions)
        tool_names = [tool.name for tool in tools]
        return tool_names

    @classmethod
    def get_authed_tools(cls, user_id: str, connected_account_id: str):
        toolset = ComposioService.get_connected_account_toolset(
            user_id=user_id,
            app_enum=cls._app_enum,
            connected_account_id=connected_account_id,
        )

        tools = toolset.get_tools(
            processors={
                "schema": {
                    Action.GMAIL_SEND_EMAIL: _send_email_schema_processor,
                },
                "post": {
                    Action.GMAIL_FETCH_EMAILS: _fetch_emails_post_processor,
                },
            },
            actions=cls._supported_actions,
        )

        return tools

    @classmethod
    async def execute_gmail(
        cls,
        user_input: str,
        thread_id: str,
        tools: Sequence[Union[BaseTool, Callable]],
        checkpointer: AsyncPostgresSaver,
        max_recursion: int = 5,
    ):
        try:
            graph = create_multiple_tools_workflow(tools, checkpointer)
            state = {"messages": [HumanMessage(user_input)], "question": user_input}
            config = RunnableConfig(
                recursion_limit=max_recursion,
                configurable={"thread_id": thread_id},
            )
            response = await graph.ainvoke(state, config)

            state = await graph.aget_state(config)
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
            logger.error(f"[gmail_service/execute_gmail] Error in executing graph: {str(e)}")
            raise e

    @classmethod
    async def handle_interrupt_execute_gmail(
        cls,
        action: HumanAction,
        thread_id: str,
        tools: Sequence[Union[BaseTool, Callable]],
        checkpointer: AsyncPostgresSaver,
        max_recursion: int = 5,
    ):
        try:
            graph = create_multiple_tools_workflow(tools, checkpointer)
            config = RunnableConfig(
                recursion_limit=max_recursion,
                configurable={"thread_id": thread_id},
            )
            response = await graph.ainvoke(Command(resume=action), config)

            return (response["messages"][-1].content,)
        except Exception as e:
            logger.error(f"[gmail_service/handle_interrupt_execute_gmail] Error in executing graph: {str(e)}")
            raise e

    @classmethod
    async def stream_gmail(
        cls,
        user_input: str,
        thread_id: str,
        tools: Sequence[Union[BaseTool, Callable]],
        checkpointer: AsyncPostgresSaver,
        max_recursion: int = 5,
    ):
        try:
            graph = create_multiple_tools_workflow(tools, checkpointer)
            state = {"messages": [HumanMessage(user_input)], "question": user_input}
            config = RunnableConfig(
                recursion_limit=max_recursion,
                configurable={"thread_id": thread_id},
            )
            return astream_state(graph, state, config)
        except Exception as e:
            logger.error(f"[gmail_service/stream_gmail] Error in executing graph: {str(e)}")
            raise e

    @classmethod
    async def handle_interrupt_stream_gmail(
        cls,
        action: HumanAction,
        thread_id: str,
        tools: Sequence[Union[BaseTool, Callable]],
        checkpointer: AsyncPostgresSaver,
        max_recursion: int = 5,
    ):
        try:
            graph = create_multiple_tools_workflow(tools, checkpointer)
            config = RunnableConfig(
                recursion_limit=max_recursion,
                configurable={"thread_id": thread_id},
            )
            return astream_state(graph, Command(resume=action), config)
        except Exception as e:
            logger.error(f"[gmail_service/handle_interrupt_stream_gmail] Error in executing graph: {str(e)}")
            raise e
