from app.core.cache.cached_mcp_agents import McpAgentCache
from app.core.langchain_agents.agent import make_graph
from app.services.database.connected_mcp_service import ConnectedMcpService
from app.services.mcps.mcp_service import McpClient


async def create_mcp_agent(
        user_id: str,
        connected_mcp_service: ConnectedMcpService,
):
    result = await connected_mcp_service.get_all_connected_mcps(user_id=user_id)

    if result.data is None:
        raise ValueError("Invalid connected_mcp_id")

    connected_mcps = result.data.connected_mcps

    connections = {}
    for connected_mcp in connected_mcps:
        connections[f"{connected_mcp.mcp_name}"] = {
            "url": connected_mcp.url,
            "transport": connected_mcp.connection_type
        }

    client = McpClient(connections)
    await client.aconnect()

    tools = client.get_tools()
    agent = make_graph(tools=tools)

    return agent, client


async def get_mcp_agent(
        user_id: str,
        mcp_agent_cache: McpAgentCache,
        connected_mcp_service: ConnectedMcpService,
):
    agent, client = await mcp_agent_cache.aget(user_id=user_id)
    if agent is None or client is None:
        agent, client = await create_mcp_agent(
            user_id=user_id,
            connected_mcp_service=connected_mcp_service
        )

    await mcp_agent_cache.aset(user_id=user_id, agent=agent, mcp_client=client)
    return agent, client
