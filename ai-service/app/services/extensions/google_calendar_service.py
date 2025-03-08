from typing import Callable, Sequence, Union

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.services.extensions.composio_service import ComposioService
from app.services.extensions.extension_service import ExtensionService


# Docs: https://app.composio.dev/app/googlecalendar
class GoogleCalendarService(ExtensionService):
    def __init__(self):
        name = str(App.GOOGLECALENDAR).lower()
        app_enum = App.GOOGLECALENDAR
        supported_actions = [
            Action.GOOGLECALENDAR_FIND_EVENT,
            Action.GOOGLECALENDAR_CREATE_EVENT,
            Action.GOOGLECALENDAR_FIND_FREE_SLOTS,
            Action.GOOGLECALENDAR_GET_CURRENT_DATE_TIME,
            Action.GOOGLECALENDAR_DELETE_EVENT,
            Action.GOOGLECALENDAR_REMOVE_ATTENDEE,
            Action.GOOGLECALENDAR_UPDATE_EVENT,
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
