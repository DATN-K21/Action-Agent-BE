from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import Connection, MultiServerMCPClient

from app.core.utils.models import Action
from app.services.database.connected_mcp_service import ConnectedMcpService


class McpService:
    @classmethod
    async def aget_tools(cls, connections: dict[str, Connection]) -> list[BaseTool]:
        """
        Get the tools for each connected MCP.
        :return: list of tools
        """
        mcp_client = MultiServerMCPClient(connections)
        tools = await mcp_client.get_tools()
        return tools

    @classmethod
    async def aget_actions(cls, connections: dict[str, Connection]) -> list[Action]:
        """
        Get the actions for each connected MCP.
        :return: list of actions
        """
        mcp_client = MultiServerMCPClient(connections)
        tools = await mcp_client.get_tools()

        actions = []
        for tool in tools:
            actions.append(Action(name=tool.name, description=tool.description))

        return actions


async def aget_all_mcp_actions(user_id: str, connected_mcp_service: ConnectedMcpService) -> list[Action]:
    """
    Get all actions from the MCP client.
    :return: list of actions
    """
    # Assuming `self.client` is an instance of MultiServerMCPClient
    result = await connected_mcp_service.get_all_connected_mcps(user_id=user_id)
    if result.data is None or not hasattr(result.data, "connected_mcps"):
        return []
    connected_mcps = result.data.connected_mcps
    connections = {}
    for connected_mcp in connected_mcps:
        connections[f"{connected_mcp.mcp_name}"] = {
            "url": connected_mcp.url,
            "transport": connected_mcp.connection_type
        }

    actions = []
    client = MultiServerMCPClient(connections)
    tools = await client.get_tools()
    for tool in tools:
        actions.append(Action(name=tool.name, description=tool.description))

    return actions


async def aget_mcp_actions_in_a_server(
        user_id: str,
        connected_mcp_id: str,
        connected_mcp_service: ConnectedMcpService
) -> list[Action]:
    """
    Get all actions from the MCP client.
    :return: list of actions
    """
    # Assuming `self.client` is an instance of MultiServerMCPClient
    result = await connected_mcp_service.get_connected_mcp_by_id(user_id=user_id, connected_mcp_id=connected_mcp_id)
    connected_mcp = result.data

    if connected_mcp is None:
        return []

    connections = {}
    connections[f"{connected_mcp.mcp_name}"] = {"url": connected_mcp.url, "transport": connected_mcp.connection_type}

    actions = []
    client = MultiServerMCPClient(connections)
    tools = await client.get_tools()
    for tool in tools:
        actions.append(Action(name=tool.name, description=tool.description))
    return actions
