from collections.abc import Callable
from typing import Union

from langchain_core.tools import BaseTool

from app.services.extensions.extension_service import ExtensionService


class ComposioAdapter(BaseTool):
    """Wrapper to make Composio tools configurable"""

    def __init__(self, tool: Union[BaseTool, Callable], **kwargs):
        super().__init__(**kwargs)
        self.tool = tool
        self._user_id = None
        self._connected_account_id = None
        self._composio_extension_service = None


    def set_composio_extension_service(self, composio_extension_service: type[ExtensionService]):
        self._composio_extension_service = composio_extension_service


    def configure(self, user_id: str, connected_account_id: str):
        """Set runtime configuration"""
        self._user_id = user_id
        self._connected_account_id = connected_account_id


    def _run(self, *args, **kwargs):
        """Execute with configured credentials"""
        if not self._user_id or not self._connected_account_id or not self._composio_extension_service:
            raise ValueError("User ID, Account ID and Extension Service class must be configured before running")

        tools = self._composio_extension_service.get_authed_tools(
            user_id=self._user_id,
            connected_account_id=self._connected_account_id
        )

        for tool in tools:
            if tool.name == self.tool.name:
                return tool.execute(
                    *args,
                    **kwargs
                )

        raise ValueError(f"Not found authed tool for {self.tool.name}")