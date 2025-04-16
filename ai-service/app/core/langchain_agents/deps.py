from app.core.cache.cached_agents import AgentCache
from app.core.langchain_agents.agent import make_graph
from app.services.database.connected_mcp_service import ConnectedMcpService
from app.services.mcps.mcp_service import McpService, McpInfo


async def create_mcp_agent(
        user_id: str,
        connected_mcp_id: str,
        connected_mcp_service: ConnectedMcpService,
        mcp_service: McpService,
):
    result = await connected_mcp_service.get_connected_mcp(
        user_id=user_id,
        connected_mcp_id=connected_mcp_id,
    )

    if result.data is None:
        raise ValueError("Invalid connected_mcp_id")

    info = McpInfo(
        mcp_name=result.data.mcp_name,
        url=result.data.url,
        connection_type=result.data.connection_type,
    )

    tools = await mcp_service.get_tools(mcp_infos=[info])

    agent = make_graph(tools)

    return agent


async def get_mcp_agent(
        user_id: str,
        connected_mcp_id: str,
        mcp_agent_cache: AgentCache,
        connected_mcp_service: ConnectedMcpService,
        mcp_service: McpService
):
    agent = mcp_agent_cache.get(user_id=user_id, agent_type=connected_mcp_id)
    if agent is None:
        agent = await create_mcp_agent(
            user_id=user_id,
            connected_mcp_id=connected_mcp_id,
            connected_mcp_service=connected_mcp_service,
            mcp_service=mcp_service,
        )

    mcp_agent_cache.set(user_id=user_id, agent_type=connected_mcp_id, agent=agent)

    return agent
