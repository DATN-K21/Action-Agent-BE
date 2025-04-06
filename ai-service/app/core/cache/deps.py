from functools import lru_cache

from app.core.cache.cached_agents import AgentCache


@lru_cache()
def get_agent_cache():
    """
    Get the agent cache instance.
    :return: The agent cache instance.
    """

    return AgentCache()
