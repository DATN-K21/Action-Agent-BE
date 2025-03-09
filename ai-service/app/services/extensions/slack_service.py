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
            Action.SLACK_CREATE_CHANNEL_BASED_CONVERSATION,
            Action.SLACK_INITIATES_CHANNEL_BASED_CONVERSATIONS,
            Action.SLACK_LIST_ALL_SLACK_TEAM_USERS_WITH_PAGINATION,
            Action.SLACK_FIND_USER_BY_EMAIL_ADDRESS,
            Action.SLACK_RETRIEVE_DETAILED_USER_INFORMATION,
            Action.SLACK_DELETE_A_PUBLIC_OR_PRIVATE_CHANNEL,
            Action.SLACK_ADD_REACTION_TO_AN_ITEM,
            Action.SLACK_ADD_A_REMOTE_FILE_FROM_A_SERVICE,
            Action.SLACK_SCHEDULES_A_MESSAGE_TO_A_CHANNEL_AT_A_SPECIFIED_TIME,
            Action.SLACK_CREATE_A_REMINDER,
            Action.SLACK_SEARCH_CHANNELS_IN_AN_ENTERPRISE_ORGANIZATION,
            Action.SLACK_UPLOAD_OR_CREATE_A_FILE_IN_SLACK,
            Action.SLACK_ARCHIVE_A_PUBLIC_OR_PRIVATE_CHANNEL,
            Action.SLACK_LIST_ALL_TEAMS_IN_AN_ENTERPRISE_ORGANIZATION,
            Action.SLACK_CREATE_AN_ENTERPRISE_TEAM,
            Action.SLACK_FETCH_MESSAGE_THREAD_FROM_A_CONVERSATION,
            Action.SLACK_REMOVE_REACTION_FROM_ITEM,
            Action.SLACK_UPDATES_A_SLACK_MESSAGE,
            Action.SLACK_CREATE_A_SLACK_USER_GROUP,
            Action.SLACK_LIST_WORKSPACE_USERS,
            Action.SLACK_LIST_ACCESSIBLE_CONVERSATIONS_FOR_A_USER,
            Action.SLACK_REGISTERS_A_NEW_CALL_WITH_PARTICIPANTS,
            Action.SLACK_LIST_TEAM_WORKSPACE_APP_REQUESTS,
            Action.SLACK_LIST_PENDING_WORKSPACE_INVITE_REQUESTS,
            Action.SLACK_RETRIEVE_CONVERSATION_INFORMATION,
            Action.SLACK_OPEN_USER_DIALOG_WITH_JSON_DEFINED_UI,
            Action.SLACK_FETCH_ITEM_REACTIONS,
            Action.SLACK_TRIGGER_USER_PERMISSIONS_MODAL,
            Action.SLACK_LIST_FILES_WITH_FILTERS_IN_SLACK,
            Action.SLACK_LIST_APPROVED_APPS_FOR_ORG_OR_WORKSPACE,
            Action.SLACK_SHARE_A_ME_MESSAGE_IN_A_CHANNEL,
            Action.SLACK_GET_CURRENT_TEAM_INTEGRATION_LOGS,
            Action.SLACK_PUSH_VIEW_TO_ROOT_VIEW_STACK,
            Action.SLACK_LIST_DISCONNECTED_CHANNELS_WITH_ORIGINAL_IDS_FOR_EKM,
            Action.SLACK_RETRIEVE_USER_PROFILE_INFORMATION,
            Action.SLACK_LIST_RESTRICTED_APPS_FOR_AN_ORG_OR_WORKSPACE,
            Action.SLACK_REMOVE_USER_FROM_WORKSPACE,
            Action.SLACK_DELETES_A_MESSAGE_FROM_A_CHAT,
            Action.SLACK_LIST_USER_REACTIONS,
            Action.SLACK_LIST_USER_GROUPS_FOR_TEAM_WITH_OPTIONS,
            Action.SLACK_LISTS_USER_S_STARRED_ITEMS_WITH_PAGINATION,
            Action.SLACK_START_REAL_TIME_MESSAGING_SESSION,
            Action.SLACK_LIST_APPROVED_WORKSPACE_INVITE_REQUESTS,
            Action.SLACK_ACTIVATE_OR_MODIFY_DO_NOT_DISTURB_DURATION,
            Action.SLACK_ADD_A_STAR_TO_AN_ITEM,
            Action.SLACK_MAP_USER_IDS_FOR_ENTERPRISE_GRID_WORKSPACES,
            Action.SLACK_RETRIEVE_CONVERSATION_MEMBERS_LIST,
            Action.SLACK_LIST_SCHEDULED_MESSAGES_IN_A_CHANNEL,
            Action.SLACK_ADD_ENTERPRISE_USER_TO_WORKSPACE,
            Action.SLACK_LIST_SLACK_S_REMOTE_FILES_WITH_FILTERS,
            Action.SLACK_LIST_DENIED_WORKSPACE_INVITE_REQUESTS,
            Action.SLACK_INVITE_USER_TO_WORKSPACE_WITH_OPTIONAL_CHANNEL_INVITES,
            Action.SLACK_RENAME_A_CONVERSATION,
            Action.SLACK_UPDATE_WORKFLOW_EXTENSION_STEP_CONFIGURATION,
            Action.SLACK_SET_CHANNEL_POSTING_PERMISSIONS,
            Action.SLACK_SET_WORKSPACE_NAME,
            Action.SLACK_EXCHANGE_OAUTH_CODE_FOR_ACCESS_TOKEN,
            Action.SLACK_REQUEST_ADDITIONAL_APP_PERMISSIONS,
            Action.SLACK_RETRIEVE_DETAILED_INFORMATION_ABOUT_A_FILE,
            Action.SLACK_SET_USER_PROFILE_PHOTO_WITH_CROPPING_OPTIONS,
            Action.SLACK_GET_CURRENT_TEAM_S_ACCESS_LOGS,
            Action.SLACK_SET_WORKSPACE_DEFAULT_CHANNELS,
            Action.SLACK_RETRIEVE_TEAM_PROFILE_DETAILS,
            Action.SLACK_APPROVE_AN_APP_INSTALLATION_IN_A_WORKSPACE,
            Action.SLACK_INDICATE_WORKFLOW_STEP_FAILURE,
            Action.SLACK_RETRIEVE_A_USER_S_IDENTITY_DETAILS,
            Action.SLACK_DELETE_A_COMMENT_ON_A_FILE,
            Action.SLACK_PROMOTE_USER_TO_WORKSPACE_OWNER,
            Action.SLACK_MARK_WORKFLOW_STEP_AS_COMPLETED,
            Action.SLACK_OPEN_A_VIEW_FOR_A_SLACK_USER,
            Action.SLACK_ADD_A_CUSTOM_EMOJI_TO_A_SLACK_TEAM,
            Action.SLACK_EXCHANGE_OAUTH_VERIFIER_FOR_ACCESS_TOKEN,
            Action.SLACK_LIST_ENTERPRISE_GRID_ORGANIZATION_EMOJIS,
            Action.SLACK_DELETE_A_FILE_BY_ID,
            Action.SLACK_LIST_EVENT_AUTHORIZATIONS_FOR_APPS,
            Action.SLACK_FETCH_CURRENT_TEAM_INFO_WITH_OPTIONAL_TEAM_SCOPE,
            Action.SLACK_SET_READ_CURSOR_IN_A_CONVERSATION,
            Action.SLACK_FETCH_DND_STATUS_FOR_MULTIPLE_TEAM_MEMBERS,
            Action.SLACK_LIST_ORG_LEVEL_IDP_GROUP_CHANNELS,
            Action.SLACK_ADD_DEFAULT_CHANNELS_TO_IDP_GROUP,
            Action.SLACK_REMOVE_IDP_GROUP_FROM_PRIVATE_CHANNEL,
            Action.SLACK_LIST_APP_USER_GRANTS_AND_SCOPES_ON_TEAM

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
