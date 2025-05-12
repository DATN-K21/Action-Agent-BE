from typing import Callable, Sequence, Union

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.services.extensions.composio_service import ComposioService
from app.services.extensions.extension_service import ExtensionService


# Docs: https://app.composio.dev/app/slack
class OutlookService(ExtensionService):
    def __init__(self):
        name = str(App.OUTLOOK).lower()
        app_enum = App.OUTLOOK
        supported_actions = [
            Action.OUTLOOK_OUTLOOK_LIST_MESSAGES,
            Action.OUTLOOK_OUTLOOK_SEND_EMAIL,
            Action.OUTLOOK_OUTLOOK_LIST_EVENTS,
            Action.OUTLOOK_OUTLOOK_CALENDAR_CREATE_EVENT,
            Action.OUTLOOK_OUTLOOK_GET_EVENT,
            Action.OUTLOOK_OUTLOOK_GET_PROFILE,
            Action.OUTLOOK_OUTLOOK_CREATE_DRAFT,
            Action.OUTLOOK_DOWNLOAD_OUTLOOK_ATTACHMENT,
            Action.OUTLOOK_OUTLOOK_GET_CONTACT,
            Action.OUTLOOK_OUTLOOK_REPLY_EMAIL,
            Action.OUTLOOK_OUTLOOK_CREATE_CONTACT,
            Action.OUTLOOK_OUTLOOK_UPDATE_EMAIL
        ]

        super().__init__(
            name=name,
            app_enum=app_enum,
            supported_actions=supported_actions,
        )

    def get_tools(self) -> Sequence[Union[BaseTool, Callable]]:
        toolset = ComposioService.get_toolset()
        tools = toolset.get_tools(actions=self._supported_actions)
        return tools

    def get_authed_tools(self, user_id) -> Sequence[Union[BaseTool, Callable]]:
        toolset = ComposioService.get_user_toolset(user_id)
        tools = toolset.get_tools(actions=self._supported_actions)
        return tools
