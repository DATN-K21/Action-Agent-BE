import time
from collections import OrderedDict
from typing import Any, Dict, Optional

from app.services.mcps.mcp_service import McpClient


class McpAgentCache:
    def __init__(self, ttl: Optional[int] = None, max_size: Optional[int] = None):
        """
        Initialize the cache with an optional time-to-live (TTL) and a maximum size limit.
        :param ttl: Time in seconds before an agent is considered expired.
        :param max_size: Maximum number of agents in the cache.
        """
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.ttl = ttl
        self.max_size = max_size

    async def aset(self, user_id: str, agent: Any, mcp_client: McpClient):
        """
        Store an agent in the cache with LRU eviction if necessary.
        :param user_id: Unique identifier for the user.
        :param agent: The agent object to cache.
        """
        key = user_id

        # Update timestamp and move to end if key exists
        if key in self.cache:
            self.cache[key]["timestamp"] = time.time()
            self.cache.move_to_end(key)
        else:
            self.cache[key] = {"mcp_agent": agent, "mcp_client": mcp_client, "timestamp": time.time()}

        if self.max_size and len(self.cache) > self.max_size:
            # get first item in self.cache to release connection
            item = next(iter(self.cache.items()))
            await item[1]["mcp_client"].aclose()
            self.cache.popitem(last=False)  # Remove the oldest item (LRU strategy)

    async def aget(self, user_id: str):
        """
        Retrieve an agent from the cache if it exists and is not expired.
        :param user_id: Unique identifier for the user.
        :return: The cached agent data or None if expired/missing.
        """
        key = user_id
        if key in self.cache:
            entry = self.cache[key]
            if self.ttl is None or (time.time() - entry["timestamp"] < self.ttl):
                # Update timestamp and move to end to mark as recently used
                entry["timestamp"] = time.time()
                self.cache.move_to_end(key)
                return entry["mcp_agent"], entry["mcp_client"]
            else:
                await entry["mcp_client"].aclose()
                await self.adelete(user_id)  # Remove expired agent
        return None, None

    async def adelete(self, user_id: str):
        """
        Remove an agent from the cache.
        :param user_id: Unique identifier for the user.
        """
        key = user_id
        if key in self.cache:
            await self.cache[key]["mcp_client"].aclose()
            self.cache.pop(key, None)

    async def aclear(self):
        """
        Clear all cached agents.
        """
        for key in self.cache.keys():
            if key in self.cache:
                await self.cache[key]["mcp_client"].aclose()
        self.cache.clear()
