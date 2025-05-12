import time
from collections import OrderedDict
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union


class AgentCache:
    def __init__(self, ttl: Optional[int] = None, max_size: Optional[int] = None):
        """
        Initialize the cache with an optional time-to-live (TTL) and a maximum size limit.
        :param ttl: Time in seconds before an agent is considered expired.
        :param max_size: Maximum number of agents in the cache.
        """
        self.cache: OrderedDict[Tuple[str, Union[str, List[str]]], Dict[str, Any]] = OrderedDict()
        self.ttl = ttl
        self.max_size = max_size

    def set(self, user_id: str, agent_type: Union[str, List[str]], agent: Any):
        """
        Store an agent in the cache with LRU eviction if necessary.
        :param user_id: Unique identifier for the user.
        :param agent_type: Type of the agent.
        :param agent: The agent object to cache.
        """
        key = (user_id, agent_type)

        # Update timestamp and move to end if key exists
        if key in self.cache:
            self.cache[key]["timestamp"] = time.time()
            self.cache.move_to_end(key)
        else:
            self.cache[key] = {"agent": agent, "timestamp": time.time()}

        if self.max_size and len(self.cache) > self.max_size:
            self.cache.popitem(last=False)  # Remove the oldest item (LRU strategy)

    def get(self, user_id: str, agent_type: Union[str, List[str]]) -> Optional[Any]:
        """
        Retrieve an agent from the cache if it exists and is not expired.
        :param user_id: Unique identifier for the user.
        :param agent_type: Type of the agent.
        :return: The cached agent data or None if expired/missing.
        """
        key = (user_id, agent_type)
        if key in self.cache:
            entry = self.cache[key]
            if self.ttl is None or (time.time() - entry["timestamp"] < self.ttl):
                # Update timestamp and move to end to mark as recently used
                entry["timestamp"] = time.time()
                self.cache.move_to_end(key)
                return entry["agent"]
            else:
                self.delete(user_id, agent_type)  # Remove expired agent
        return None

    def delete(self, user_id: str, agent_type: Union[str, List[str]]):
        """
        Remove an agent from the cache.
        :param user_id: Unique identifier for the user.
        :param agent_type: Type of the agent.
        """
        key = (user_id, agent_type)
        self.cache.pop(key, None)

    def clear(self):
        """
        Clear all cached agents.
        """
        self.cache.clear()

@lru_cache()
def get_agent_cache():
    """
    Get the agent cache instance.
    :return: The agent cache instance.
    """

    return AgentCache()