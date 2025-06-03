from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.graph.v2.base_v2 import build_basic_agent
from app.services.database.connected_mcp_service import ConnectedMcpService
from app.services.llm_service import get_llm_chat_model


@asynccontextmanager
async def create_mcp_agent_no_cache(
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

    client = MultiServerMCPClient(connections)
    tools = await client.get_tools()
    agent = build_basic_agent(
        name="mcps-agent",
        model=get_llm_chat_model(),
        tools=tools,
        checkpointer=checkpointer,
        prompt="You are a helpful assistant.",
        interrupt_before=None,
    )

    yield agent
