from functools import lru_cache

from app.core.cache.cached_agents import AgentCache
from app.core.cache.cached_mcp_agents import McpAgentCache


@lru_cache()
def get_agent_cache():
    """
    Get the agent cache instance.
    :return: The agent cache instance.
    """

    return AgentCache()


@lru_cache()
def get_mcp_agent_cache():
    """
    Get the MCP agent cache instance.
    :return: The MCP agent cache instance.
    """

    return McpAgentCache()
