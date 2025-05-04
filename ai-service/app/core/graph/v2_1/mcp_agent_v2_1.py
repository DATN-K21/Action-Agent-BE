from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.graph.v2_1.base_v2_1 import GraphBuilderV2
from app.services.database.connected_mcp_service import ConnectedMcpService
from app.services.llm_service import get_llm_chat_model


@asynccontextmanager
async def create_mcp_agent_no_cache_v2(
        user_id: str,
        connected_mcp_service: ConnectedMcpService,
        checkpointer: AsyncPostgresSaver
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

    async with MultiServerMCPClient(connections) as client:
        tools = client.get_tools()
        agent = GraphBuilderV2(
            model=get_llm_chat_model(),
            tools=tools,
            checkpointer=checkpointer
        ).build_graph()

        yield agent
