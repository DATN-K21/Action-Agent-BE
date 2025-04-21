from typing import Callable, Sequence, Union

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.services.extensions.composio_service import ComposioService
from app.services.extensions.extension_service import ExtensionService


# Docs: https://app.composio.dev/app/slack
class GoogleDriveService(ExtensionService):
    def __init__(self):
        name = str(App.GOOGLEDRIVE).lower()
        app_enum = App.GOOGLEDRIVE
        supported_actions = [
            Action.GOOGLEDRIVE_FIND_FILE,
            Action.GOOGLEDRIVE_CREATE_FILE_FROM_TEXT,
            Action.GOOGLEDRIVE_FIND_FOLDER,
            Action.GOOGLEDRIVE_CREATE_FOLDER,
            Action.GOOGLEDRIVE_UPLOAD_FILE,
            Action.GOOGLEDRIVE_ADD_FILE_SHARING_PREFERENCE,
            Action.GOOGLEDRIVE_EDIT_FILE,
            Action.GOOGLEDRIVE_COPY_FILE,
            Action.GOOGLEDRIVE_DOWNLOAD_FILE,
            Action.GOOGLEDRIVE_DELETE_FOLDER_OR_FILE
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
