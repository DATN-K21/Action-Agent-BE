from typing import Callable, Sequence, Union

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.services.extensions.composio_service import ComposioService
from app.services.extensions.extension_service import ExtensionService


# Docs: https://app.composio.dev/app/googlecalendar
class GoogleMeetService(ExtensionService):
    def __init__(self):
        name = str(App.GOOGLEMEET).lower()
        app_enum = App.GOOGLEMEET
        supported_actions = [
            Action.GOOGLEMEET_CREATE_MEET,
            Action.GOOGLEMEET_GET_MEET,
            Action.GOOGLEMEET_GET_TRANSCRIPTS_BY_CONFERENCE_RECORD_ID,
            Action.GOOGLEMEET_GET_CONFERENCE_RECORD_FOR_MEET,
            Action.GOOGLEMEET_GET_RECORDINGS_BY_CONFERENCE_RECORD_ID
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
