from typing import Callable, Sequence, Union

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.services.extensions.composio_service import ComposioService
from app.services.extensions.extension_service import ExtensionService


# Docs: https://app.composio.dev/app/googlemaps
class GoogleMapsService(ExtensionService):
    def __init__(self):
        name = str(App.GOOGLEMAPS).lower()
        app_enum = App.GOOGLE_MAPS
        supported_actions = [
            Action.GOOGLE_MAPS_GET_ROUTE,
            Action.GOOGLE_MAPS_TEXT_SEARCH,
            Action.GOOGLE_MAPS_NEARBY_SEARCH,
            Action.GOOGLE_MAPS_GET_DIRECTION
        ]

        super().__init__(
            name=name,
            app_enum=app_enum,
            supported_actions=supported_actions,
        )

    def get_tools(self) -> Sequence[Union[BaseTool, Callable]]:
        toolset = ComposioService.get_toolset()
        tools = toolset.get_tools
        return tools

    def get_authed_tools(self, user_id) -> Sequence[Union[BaseTool, Callable]]:
        toolset = ComposioService.get_user_toolset(user_id)
        tools = toolset.get_tools
        return tools
