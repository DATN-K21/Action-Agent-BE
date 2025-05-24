import asyncio

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient, StdioConnection, SSEConnection

from app.core.utils.models import Action
from app.services.database.connected_mcp_service import ConnectedMcpService


class McpClient:
    def __init__(self, connections: dict[str, StdioConnection | SSEConnection]):
        """
        Initialize the MCP service.
        """
        self.client = MultiServerMCPClient()
        self.client.connections = connections

    def set_connections(self, connections: dict[str, dict[str, str]]):
        """
        Set the connections for each MCP.
        :param connections: dictionary of connections
        """
        self.client.connections = connections

    def get_tools(self) -> list[BaseTool]:
        """
        Get the tools for each connected MCP.
        :return: list of tools
        """
        tools = self.client.get_tools()
        return tools

    def get_actions(self) -> list[Action]:
        """
        Get the actions for each connected MCP.
        :return: list of actions
        """
        tools = self.client.get_tools()
        actions = []
        for tool in tools:
            actions.append(
                Action(
                    name=tool.name,
                    description=tool.description
                )
            )

        return actions

    async def aconnect(self):
        """
        Connect to the MCPs.
        """
        try:
            connections = self.client.connections or {}
            for server_name, connection in connections.items():
                connection_dict = connection.copy()
                transport = connection_dict.pop("transport")
                if transport == "stdio":
                    await self.client.connect_to_server_via_stdio(server_name, **connection_dict)
                elif transport == "sse":
                    await self.client.connect_to_server_via_sse(server_name, **connection_dict)
                else:
                    raise ValueError(
                        f"Unsupported transport: {transport}. Must be 'stdio' or 'sse'"
                    )
            return self
        except Exception:
            await self.client.exit_stack.aclose()
            raise

    async def aclose(self):
        await self.client.exit_stack.aclose()

    def __del__(self):
        if hasattr(self, 'client') and hasattr(self.client, 'exit_stack'):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.aclose())
                else:
                    loop.run_until_complete(self.aclose())
            except Exception as e:
                print(f"[Warning] Exception during __del__: {e}")


async def aget_all_mcp_actions(user_id: str, connected_mcp_service: ConnectedMcpService) -> list[Action]:
    """
    Get all actions from the MCP client.
    :return: list of actions
    """
    # Assuming `self.client` is an instance of MultiServerMCPClient
    result = await connected_mcp_service.get_all_connected_mcps(user_id=user_id)
    connected_mcps = result.data.connected_mcps
    connections = {}
    for connected_mcp in connected_mcps:
        connections[f"{connected_mcp.mcp_name}"] = {
            "url": connected_mcp.url,
            "transport": connected_mcp.connection_type
        }

    actions = []
    async with MultiServerMCPClient(connections) as client:
        tools = client.get_tools()
        for tool in tools:
            actions.append(
                Action(
                    name=tool.name,
                    description=tool.description
                )
            )

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
    connected_mcps = result.data

    actions = []
    async with MultiServerMCPClient({
        f"{connected_mcps.mcp_name}": {
            "url": connected_mcps.url,
            "transport": connected_mcps.connection_type
        }
    }) as client:
        tools = client.get_tools()
        for tool in tools:
            actions.append(
                Action(
                    name=tool.name,
                    description=tool.description
                )
            )

    return actions
