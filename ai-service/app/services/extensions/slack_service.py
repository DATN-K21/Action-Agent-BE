from typing import Callable, Sequence, Union

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.services.extensions.composio_service import ComposioService
from app.services.extensions.extension_service import ExtensionService


# Docs: https://app.composio.dev/app/slack
class SlackService(ExtensionService):
    def __init__(self):
        name = str(App.SLACK).lower()
        app_enum = App.SLACK
        supported_actions = [
            Action.SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL,
            Action.SLACK_SEARCH_FOR_MESSAGES_WITH_QUERY,
            Action.SLACK_LIST_ALL_SLACK_TEAM_CHANNELS_WITH_VARIOUS_FILTERS,
            Action.SLACK_FETCH_CONVERSATION_HISTORY,
            Action.SLACK_LIST_ALL_SLACK_TEAM_USERS_WITH_PAGINATION,
            Action.SLACK_ADD_REACTION_TO_AN_ITEM,
            Action.SLACK_SCHEDULES_A_MESSAGE_TO_A_CHANNEL_AT_A_SPECIFIED_TIME,
            Action.SLACK_CREATE_A_REMINDER,
            Action.SLACK_REMOVE_REACTION_FROM_ITEM,
            Action.SLACK_UPDATES_A_SLACK_MESSAGE,
            Action.SLACK_CREATE_CHANNEL_BASED_CONVERSATION,
            Action.SLACK_DELETE_A_PUBLIC_OR_PRIVATE_CHANNEL,
            Action.SLACK_SEARCH_CHANNELS_IN_AN_ENTERPRISE_ORGANIZATION,
            Action.SLACK_CREATE_AN_ENTERPRISE_TEAM,
            Action.SLACK_FETCH_MESSAGE_THREAD_FROM_A_CONVERSATION,
            Action.SLACK_LIST_WORKSPACE_USERS,
            Action.SLACK_RETRIEVE_CONVERSATION_INFORMATION,
            Action.SLACK_INVITE_USER_TO_WORKSPACE_WITH_OPTIONAL_CHANNEL_INVITES,
            Action.SLACK_RENAME_A_CONVERSATION,
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
