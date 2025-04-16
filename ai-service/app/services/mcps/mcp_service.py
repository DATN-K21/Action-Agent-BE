from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel


class McpInfo(BaseModel):
    """
    MCP information model.
    """
    mcp_name: str
    url: str
    connection_type: str


class McpService:
    @classmethod
    async def get_tools(cls, mcp_infos: list[McpInfo]):
        """
        Get the tools for each connected MCP.
        :param mcp_infos: list of connected MCPs
        :return: list of tools
        """
        config: dict[str, dict[str, str]] = {}
        for info in mcp_infos:
            if info.connection_type == "sse":
                mcp_name = info.mcp_name
                config[mcp_name] = {
                    "url": info.url,
                    "transport": info.connection_type,
                }

        async with MultiServerMCPClient(config) as client:
            # Get the tools for each connected MCP
            tools = client.get_tools()
            return tools
