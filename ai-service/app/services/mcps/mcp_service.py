from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.db_session import get_db_session
from app.core.models import ToolInfo
from app.schemas.connected_mcp import GetConnectedMcpResponse
from app.services.database.connected_mcp_service import ConnectedMcpService

logger = logging.get_logger(__name__)


class McpService:
    @classmethod
    async def aget_mcp_tool_info(cls, user_id: str, connected_mcp_id: str) -> list[ToolInfo]:
        """
        Retrieve information about a specific MCP tool for a user.

        :param user_id: The ID of the user.
        :param connected_mcp_id: The ID of the connected MCP.
        :return: ToolInfo object containing details about the MCP tool.
        """
        logger.info(f"Retrieving MCP tool info for user {user_id} and MCP {connected_mcp_id}")

        session: AsyncSession = await get_db_session()
        connected_mcp_service: ConnectedMcpService = ConnectedMcpService(db=session)

        result = await connected_mcp_service.get_connected_mcp_by_id(
            user_id=user_id,
            connected_mcp_id=connected_mcp_id
        )

        if result.status != 200 or result.data is None:
            logger.error(f"Failed to retrieve connected MCP: {result.message}")
            raise ValueError(f"Could not find connected MCP with ID {connected_mcp_id}")

        connected_mcp: GetConnectedMcpResponse = result.data

        client = MultiServerMCPClient({
            f"{connected_mcp.mcp_name}": {
                "url": connected_mcp.url,
                "transport": connected_mcp.connection_type
            }
        })

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
