from typing import Callable, Sequence, Union

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.services.extensions.composio_service import ComposioService
from app.services.extensions.extension_service import ExtensionService


# Docs: https://app.composio.dev/app/slack
class NotionService(ExtensionService):
    def __init__(self):
        name = str(App.NOTION).lower()
        app_enum = App.NOTION
        supported_actions = [
            Action.NOTION_INSERT_ROW_DATABASE,
            Action.NOTION_ADD_PAGE_CONTENT,
            Action.NOTION_CREATE_NOTION_PAGE,
            Action.NOTION_CREATE_DATABASE,
            Action.NOTION_FETCH_DATABASE,
            Action.NOTION_GET_ABOUT_ME,
            Action.NOTION_QUERY_DATABASE,
            Action.NOTION_LIST_USERS,
            Action.NOTION_FETCH_ROW,
            Action.NOTION_GET_ABOUT_USER,
            Action.NOTION_FETCH_COMMENTS,
            Action.NOTION_UPDATE_ROW_DATABASE,
            Action.NOTION_CREATE_COMMENT,
            Action.NOTION_DELETE_BLOCK,
            Action.NOTION_UPDATE_SCHEMA_DATABASE

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
