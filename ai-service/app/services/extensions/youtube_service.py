from typing import Callable, Sequence, Union

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.services.extensions.composio_service import ComposioService
from app.services.extensions.extension_service import ExtensionService


# Docs: https://app.composio.dev/app/youtube
class YoutubeService(ExtensionService):
    def __init__(self):
        name = str(App.YOUTUBE).lower()
        app_enum = App.YOUTUBE
        supported_actions = [
            Action.YOUTUBE_SEARCH_YOU_TUBE,
            Action.YOUTUBE_VIDEO_DETAILS,
            Action.YOUTUBE_LIST_CAPTION_TRACK,
            Action.YOUTUBE_LOAD_CAPTIONS,
            Action.YOUTUBE_LIST_CHANNEL_VIDEOS,
            Action.YOUTUBE_LIST_USER_SUBSCRIPTIONS,
            Action.YOUTUBE_LIST_USER_PLAYLISTS,
            Action.YOUTUBE_SUBSCRIBE_CHANNEL,
            Action.YOUTUBE_UPDATE_VIDEO,
            Action.YOUTUBE_UPDATE_THUMBNAIL
        ]

        super().__init__(
            name=name,
            app_enum=app_enum,
            supported_actions=supported_actions,
        )

    def get_tools(self) -> Sequence[Union[BaseTool, Callable]]:
        toolset = ComposioService.get_toolset()
        tools = toolset.get_tools(apps=[self._app_enum], actions=self._supported_actions)
        return tools

    def get_authed_tools(self, user_id) -> Sequence[Union[BaseTool, Callable]]:
        toolset = ComposioService.get_user_toolset(user_id)
        tools = toolset.get_tools(actions=self._supported_actions)
        return tools
