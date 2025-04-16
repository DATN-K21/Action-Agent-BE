from functools import lru_cache

from app.services.mcps.mcp_service import McpService


@lru_cache
def get_mcp_service() -> McpService:
    return McpService()
