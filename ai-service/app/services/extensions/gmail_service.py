from typing import Callable, Sequence, Union

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.core import logging
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
    def __init__(self):
        name = str(App.GMAIL).lower()
        app_enum = App.GMAIL
        supported_actions = [
            Action.GMAIL_SEND_EMAIL,
            Action.GMAIL_FETCH_EMAILS,
            Action.GMAIL_REPLY_TO_THREAD,
            Action.GMAIL_SEARCH_PEOPLE,
            Action.GMAIL_GET_CONTACTS,
            Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID,
        ]

        super().__init__(
            name=name,
            app_enum=app_enum,
            supported_actions=supported_actions,
        )

    def get_tools(self) -> Sequence[Union[BaseTool, Callable]]:
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
            actions=self._supported_actions,
        )
        return tools

    def get_authed_tools(self, user_id: str) -> Sequence[Union[BaseTool, Callable]]:
        toolset = ComposioService.get_user_toolset(user_id=user_id)

        tools = toolset.get_tools(
            processors={
                "schema": {
                    Action.GMAIL_SEND_EMAIL: _send_email_schema_processor,
                },
                "post": {
                    Action.GMAIL_FETCH_EMAILS: _fetch_emails_post_processor,
                },
            },
            actions=self._supported_actions,
        )

        return tools
