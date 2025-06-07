from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection

from app.core import logging
from app.core.models import ToolInfo

logger = logging.get_logger(__name__)


class McpService:
    @classmethod
    async def aget_mcp_tool_info(cls, connections: dict[str, Connection]) -> list[ToolInfo]:
        """
        Retrieve information about a specific MCP tool for a user.

        :param user_id: The ID of the user.
        :param connections: A dictionary containing MCP connection details.
        :return: ToolInfo object containing details about the MCP tool.
        """

        client = MultiServerMCPClient(connections=connections)

        tools: list[BaseTool] = await client.get_tools()

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
