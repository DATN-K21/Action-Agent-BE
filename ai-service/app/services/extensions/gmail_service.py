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
from app.services.extensions.extension_service import ExtensionService

logger = logging.get_logger(__name__)


def _send_email_schema_processor(schema: dict) -> dict:
    # Not support attachment in send email schema
    del schema["attachment"]
    return schema


def _fetch_emails_post_processor(output_data: dict) -> dict:
    # Abbreviate the output data
    if output_data["successfull"]:
        for message in output_data["data"]["messages"]:
            del message["attachmentList"]
            del message["payload"]

    return output_data


class GmailService(ExtensionService):
    _name = "gmail"
    _app_enum = ComposioService.get_app_enum("GMAIL")
    _supported_actions = [
        Action.GMAIL_SEND_EMAIL,
        Action.GMAIL_FETCH_EMAILS,
        Action.GMAIL_REPLY_TO_THREAD,
        Action.GMAIL_SEARCH_PEOPLE,
        Action.GMAIL_GET_CONTACTS,
        Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID,
    ]


    @classmethod
    def get_actions(cls):
        toolset = ComposioService.get_toolset()
        tools = toolset.get_tools(actions=cls._supported_actions)
        tool_names = [tool.name for tool in tools]
        return tool_names


    @classmethod
    def get_tools(cls):
        toolset = ComposioService.get_toolset()
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