# graph.py
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from app.services.model_service import get_openai_model


@asynccontextmanager
async def make_graph():
    async with MultiServerMCPClient(
            {
                "gmail": {
                    "url": "https://mcp.composio.dev/gmail/incalculable-plain-byte-8uChoo",
                    "transport": "sse",
                },
                "google_maps": {
                    "url": "https://mcp.composio.dev/google_maps/incalculable-plain-byte-8uChoo",
                    "transport": "sse",
                },
                "youtube": {
                    "url": "https://mcp.composio.dev/youtube/incalculable-plain-byte-8uChoo",
                    "transport": "sse",
                },
            }
    ) as client:
        tools = client.get_tools()
        agent = create_react_agent(get_openai_model(), tools)
        yield agent
