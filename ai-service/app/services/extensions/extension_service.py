from abc import ABC, abstractmethod
from typing import Sequence, Union, Callable
from uuid import uuid4

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.core import logging
from app.core.settings import env_settings
from app.services.extensions.composio_service import ComposioService

logger = logging.get_logger(__name__)


# noinspection PyMethodMayBeStatic
class ExtensionService(ABC):
    def __init__(self, name: str, app_enum: App, supported_actions: Sequence[Action]):
        self._name = name
        self._app_enum = app_enum
        self._supported_actions = supported_actions
        self._id = str(uuid4)
        self._redirect_url = env_settings.COMPOSIO_REDIRECT_URL

    def initialize_connection(self, user_id: str):
        if self._app_enum is None:
            raise ValueError("App enum is not set")
        if self._redirect_url is None:
            raise ValueError("Redirect URL is not set")

        result = ComposioService.initialize_app_connection(user_id, self._app_enum, self._redirect_url)
        return result

    def disconnect(self, connected_account_id: str):
        return ComposioService.delete_connection(connected_account_id)

    def check_connection(self, user_id: str):
        return ComposioService.check_app_connection(user_id, self._app_enum)

    def get_name(self) -> str:
        return self._name

    def get_app_enum(self) -> App:
        return self._app_enum

    def get_actions(self) -> Sequence[Action]:
        return self._supported_actions

    def get_action_names(self) -> Sequence[str]:
        tool_names = [str(action) for action in self._supported_actions]
        return tool_names

    @abstractmethod
    def get_tools(self) -> Sequence[Union[BaseTool, Callable]]:
        """Get the tools"""
        pass

    @abstractmethod
    def get_authed_tools(self, user_id: str) -> Sequence[Union[BaseTool, Callable]]:
        """Get the tools with the auth parameters"""
        pass
