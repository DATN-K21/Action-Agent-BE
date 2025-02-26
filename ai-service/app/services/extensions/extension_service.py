from abc import ABC, abstractmethod

from app.core import logging
from app.core.settings import env_settings
from app.services.extensions.composio_service import ComposioService

logger = logging.get_logger(__name__)


class ExtensionService(ABC):
    _redirect_url = env_settings.COMPOSIO_REDIRECT_URL
    _name = None
    _app_enum = None
    _supported_actions = None


    @classmethod
    def initialize_connection(cls, user_id: str):
        if cls._app_enum is None:
            raise ValueError("App enum is not set")
        if cls._redirect_url is None:
            raise ValueError("Redirect URL is not set")

        result = ComposioService.initialize_app_connection(user_id, cls._app_enum, cls._redirect_url)
        return result


    @classmethod
    def logout(cls, connected_account_id: str):
        return ComposioService.delete_connection(connected_account_id)


    @classmethod
    def get_name(cls):
        return cls._name


    @classmethod
    def get_app_enum(cls):
        return cls._app_enum


    @classmethod
    @abstractmethod
    def get_actions(cls):
        """ Get the actions """
        pass


    @classmethod
    @abstractmethod
    def get_tools(cls):
        """ Get the tools """
        pass


    @classmethod
    @abstractmethod
    def get_authed_tools(cls, user_id: str, connected_account_id: str):
        """ Get the tools with the auth parameters """
        pass