import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient, StdioConnection, SSEConnection


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

    def get_tools(self):
        """
        Get the tools for each connected MCP.
        :return: list of tools
        """
        tools = self.client.get_tools()
        return tools

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
