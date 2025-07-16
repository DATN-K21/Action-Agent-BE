import asyncio
from datetime import datetime
from typing import Sequence

from composio import App
from composio_langgraph import Action
from langchain_core.tools import BaseTool

from app.core import logging
from app.core.models import ToolInfo
from app.core.settings import env_settings
from app.schemas.extension import DeleteConnection
from app.services.extensions.composio_client import ComposioClient

logger = logging.get_logger(__name__)


class ExtensionService:
    def __init__(
        self,
        name: str,
        app_enum: App,
        supported_actions: list[Action] = list(),
        redirect_url: str = env_settings.COMPOSIO_REDIRECT_URL,
    ):
        self._name = name
        self._app_enum = app_enum
        self._supported_actions = supported_actions if supported_actions is not None else []
        self._redirect_url = redirect_url

        # Get the integration id if it exists, otherwise create a new one
        self._integration_id = ComposioClient.get_or_initiate_integration(app_enum=self._app_enum)

    async def ainitialize_connection(self, user_id: str):
        if self._app_enum is None:
            raise ValueError("App enum is not set")
        if self._redirect_url is None:
            raise ValueError("Redirect URL is not set")

        # Run in thread pool to avoid blocking
        result = await asyncio.to_thread(ComposioClient.initiate_app_connection, user_id, self._app_enum, self._redirect_url)
        return result

    async def adisconnect(self, connected_account_id: str) -> DeleteConnection:
        return await asyncio.to_thread(ComposioClient.delete_connection, connected_account_id)

    async def acheck_connection(self, user_id: str) -> bool:
        return await asyncio.to_thread(ComposioClient.check_app_connection, user_id, self._app_enum)

    def get_name(self) -> str:
        return self._name

    def get_app_enum(self) -> App:
        return self._app_enum

    def get_actions(self) -> Sequence[Action]:
        return self._supported_actions

    def get_action_names(self) -> Sequence[str]:
        tool_names = [str(action) for action in self._supported_actions]
        return tool_names

    async def aget_tools(self) -> Sequence[ToolInfo]:
        """Get the tools"""
        # Run in thread pool to avoid blocking
        toolset = await asyncio.to_thread(ComposioClient.get_toolset)
        tools = await asyncio.to_thread(toolset.get_tools, actions=self._supported_actions)

        tool_infos = [
            ToolInfo(
                description=tool.description,
                tool=tool,
                display_name=tool.name,
                input_parameters=tool.get_input_jsonschema(),
            )
            for tool in tools
        ]

        return tool_infos

    async def aget_authed_tools(self, user_id: str) -> Sequence[BaseTool]:
        """Get the tools for a specific user"""

        start_time = datetime.now()
        # Run in thread pool to avoid blocking
        toolset = await asyncio.to_thread(ComposioClient.get_user_toolset, user_id=user_id)
        tools = await asyncio.to_thread(toolset.get_tools, actions=self._supported_actions)
        logger.info(f"[_get_authed_tools] get_tools completed in {datetime.now() - start_time}. UserId={user_id}, Tools={len(tools)}")

        return tools

    @classmethod
    async def aget_specified_tool(cls, action: Action) -> BaseTool:
        """Get the specified tool"""
        toolset = await asyncio.to_thread(ComposioClient.get_toolset)
        tools = await asyncio.to_thread(toolset.get_tools, actions=[action])
        if len(tools) == 1:
            return tools[0]
        else:
            raise ValueError("Multiple tools found or no tool found for the specified action.")

    @classmethod
    async def aget_authed_specified_tool(cls, user_id: str, action: Action) -> BaseTool:
        """Get the specified tool for a specific user"""
        toolset = await asyncio.to_thread(ComposioClient.get_user_toolset, user_id=user_id)
        tools = await asyncio.to_thread(toolset.get_tools, actions=[action])
        if len(tools) == 1:
            return tools[0]
        else:
            raise ValueError("Multiple tools found or no tool found for the specified action.")
