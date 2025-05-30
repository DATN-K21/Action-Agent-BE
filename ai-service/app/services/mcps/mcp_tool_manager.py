import threading
from collections import OrderedDict
from typing import Any, Dict, OrderedDict as OrderedDictType, Callable

from langchain.tools import BaseTool  # Assuming BaseTool is the base for tools fetched
from pydantic import BaseModel, Field


# --- Mock or Import MultiServerMCPClient and ToolInfo ---
# If langchain_mcp_adapters is available, uncomment the next line
# from langchain_mcp_adapters import MultiServerMCPClient

# For demonstration purposes, let's define a mock MultiServerMCPClient
# if the actual one is not available or for testing.
class MockMultiServerMCPClient:
    def __init__(self, server_id: str, user_id: str):
        self.server_id = server_id
        self.user_id = user_id
        self.is_connected = True
        print(f"MockMultiServerMCPClient created for user '{user_id}' to server '{server_id}'")

    def get_tools(self) -> Dict[str, BaseTool]:
        """Simulates fetching tools from the server."""
        print(f"Fetching tools using client for server '{self.server_id}' by user '{self.user_id}'")

        # Simulate some tools
        class SampleTool(BaseTool):
            name: str = "sample_mcp_tool"
            description: str = "A sample tool from MCP server"

            def _run(self, query: str) -> str:
                return f"Sample tool executed with query: {query} via {self.server_id}"

            async def _arun(self, query: str) -> str:
                return f"Sample tool executed asynchronously with query: {query} via {self.server_id}"

        return {f"mcp_tool_{self.server_id.replace('.', '_')}": SampleTool()}

    def close(self):
        self.is_connected = False
        print(f"MockMultiServerMCPClient for user '{self.user_id}' to server '{self.server_id}' closed.")


# Use the mock if the real one isn't available.
# Replace 'MockMultiServerMCPClient' with 'MultiServerMCPClient' if using the actual library.
MultiServerMCPClient = MockMultiServerMCPClient


# Re-using ToolInfo from your example for consistency
class ToolInfo(BaseModel):
    description: str
    tool: BaseTool
    display_name: str = "NO NAME PROVIDED"
    input_parameters: Dict[str, Any] | None = None
    credentials: Dict[str, Any] | None = None


# --- Constants ---
# These would typically come from environment settings like your env_settings
MAX_CACHED_MCP_USERS = 50  # Example: Maximum number of users whose clients are cached
MAX_MCP_CLIENT_INSTANCES_PER_USER = 5  # Example: Max MCP client instances per user


# --- MCP Tool Manager Structures ---

class MCPClientInstanceInfo(BaseModel):
    """
    Stores an MCP client instance and the tools fetched through it.
    """
    client: MultiServerMCPClient = Field(..., description="The MCP client instance.")
    # Stores ToolInfo objects, keyed by tool name
    fetched_tools: Dict[str, ToolInfo] = Field(default=dict, description="Tools fetched via this client.")

    class Config:
        arbitrary_types_allowed = True  # To allow MultiServerMCPClient


class MCPToolManager:
    """
    Manages and caches MultiServerMCPClient instances and their fetched tools for users.
    """

    def __init__(self):
        """
        Initializes the MCPToolManager.
        """
        # Cache structure:
        # {
        #   user_id_1: OrderedDict({
        #                server_id_A: MCPClientInstanceInfo,
        #                server_id_B: MCPClientInstanceInfo
        #              }),
        #   user_id_2: OrderedDict({ ... })
        # }
        self.user_clients_cache: OrderedDictType[str, OrderedDictType[str, MCPClientInstanceInfo]] = OrderedDict()
        self.cache_lock = threading.Lock()  # Thread safety for cache operations

        if MAX_CACHED_MCP_USERS <= 0:
            print("Warning: MAX_CACHED_MCP_USERS is non-positive. User-level client caching will be disabled.")
        if MAX_MCP_CLIENT_INSTANCES_PER_USER <= 0:
            print(
                "Warning: MAX_MCP_CLIENT_INSTANCES_PER_USER is non-positive. Client instance caching per user will be disabled.")

    def get_or_create_client(
            self,
            user_id: str,
            server_identifier: str,
            client_factory: Callable[[], MultiServerMCPClient]
    ) -> MultiServerMCPClient | None:
        """
        Retrieves an existing MultiServerMCPClient for the given user and server identifier,
        or creates and caches a new one using the provided client_factory.

        Manages LRU eviction for users and for client instances within a user's cache.

        Args:
            user_id: The unique identifier for the user.
            server_identifier: A unique string identifying the server connection (e.g., URL, alias).
            client_factory: A callable that takes no arguments and returns a new
                            MultiServerMCPClient instance, configured and ready to use.

        Returns:
            The MultiServerMCPClient instance, or None if caching is disabled or creation fails.
        """
        if MAX_CACHED_MCP_USERS <= 0:
            # If user caching is disabled, create a new client directly without caching
            print(
                f"User caching disabled. Creating a new client for user '{user_id}' and server '{server_identifier}'.")
            try:
                return client_factory()
            except Exception as e:
                print(f"Error creating client via factory for user '{user_id}', server '{server_identifier}': {e}")
                return None

        with self.cache_lock:
            user_specific_clients: OrderedDictType[str, MCPClientInstanceInfo]

            if user_id in self.user_clients_cache:
                user_specific_clients = self.user_clients_cache[user_id]
                self.user_clients_cache.move_to_end(user_id)  # Mark user as recently used
            else:
                # New user, check if user cache limit is reached
                if len(self.user_clients_cache) >= MAX_CACHED_MCP_USERS:
                    lru_user_id, _ = self.user_clients_cache.popitem(last=False)
                    print(f"MCP user cache limit ({MAX_CACHED_MCP_USERS}) hit. Evicted user: '{lru_user_id}'.")
                user_specific_clients = OrderedDict()
                self.user_clients_cache[user_id] = user_specific_clients

            # Now handle client instance for this user
            if MAX_MCP_CLIENT_INSTANCES_PER_USER <= 0:
                # If client instance caching per user is disabled, create directly
                print(
                    f"Client instance caching for user '{user_id}' disabled. Creating new client for server '{server_identifier}'.")
                try:
                    return client_factory()
                except Exception as e:
                    print(f"Error creating client via factory for user '{user_id}', server '{server_identifier}': {e}")
                    return None

            if server_identifier in user_specific_clients:
                user_specific_clients.move_to_end(server_identifier)  # Mark client as recently used
                print(f"Returning cached client for user '{user_id}', server '{server_identifier}'.")
                return user_specific_clients[server_identifier].client
            else:
                # Client not found for this user and server, create and cache it
                if len(user_specific_clients) >= MAX_MCP_CLIENT_INSTANCES_PER_USER:
                    lru_server_id, evicted_client_info = user_specific_clients.popitem(last=False)
                    print(
                        f"MCP client instance limit ({MAX_MCP_CLIENT_INSTANCES_PER_USER}) for user '{user_id}' hit. Evicted client for server: '{lru_server_id}'.")
                    # Optionally, attempt to close the client if it has a close method
                    if hasattr(evicted_client_info.client, 'close'):
                        try:
                            evicted_client_info.client.close()
                        except Exception as e:
                            print(f"Error closing evicted client for server '{lru_server_id}': {e}")

                print(f"Creating and caching new client for user '{user_id}', server '{server_identifier}'.")
                try:
                    new_client = client_factory()
                    client_info = MCPClientInstanceInfo(client=new_client, fetched_tools=OrderedDict())
                    user_specific_clients[server_identifier] = client_info
                    return new_client
                except Exception as e:
                    print(f"Error creating client via factory for user '{user_id}', server '{server_identifier}': {e}")
                    return None

    def add_tools_for_client(
            self,
            user_id: str,
            server_identifier: str,
            tools: Dict[str, ToolInfo]
    ) -> bool:
        """
        Adds fetched tools to the cache for a specific client instance of a user.
        The client instance must already exist in the cache (i.e., created via get_or_create_client).

        Args:
            user_id: The user's identifier.
            server_identifier: The server's identifier.
            tools: A dictionary of tool_name -> ToolInfo to be added.

        Returns:
            True if tools were successfully added, False otherwise (e.g., client not found).
        """
        if MAX_CACHED_MCP_USERS <= 0 or MAX_MCP_CLIENT_INSTANCES_PER_USER <= 0:
            print("Caching disabled. Cannot add tools.")
            return False

        with self.cache_lock:
            if user_id not in self.user_clients_cache:
                print(f"Cannot add tools: User '{user_id}' not found in cache.")
                return False

            user_specific_clients = self.user_clients_cache[user_id]
            if server_identifier not in user_specific_clients:
                print(f"Cannot add tools: Server '{server_identifier}' for user '{user_id}' not found in cache.")
                return False

            client_instance_info = user_specific_clients[server_identifier]
            # Update existing tools or add new ones.
            # This simple update overwrites tools with the same name if re-added.
            client_instance_info.fetched_tools.update(tools)

            # Ensure this client and user are marked as recently used
            user_specific_clients.move_to_end(server_identifier)
            self.user_clients_cache.move_to_end(user_id)

            print(f"Added/updated {len(tools)} tools for user '{user_id}', server '{server_identifier}'.")
            return True

    def get_client(self, user_id: str, server_identifier: str) -> MultiServerMCPClient | None:
        """
        Retrieves a specific client instance for a user and server.

        Args:
            user_id: The user's identifier.
            server_identifier: The server's identifier.

        Returns:
            The MultiServerMCPClient instance if found, else None.
        """
        if MAX_CACHED_MCP_USERS <= 0 or MAX_MCP_CLIENT_INSTANCES_PER_USER <= 0:
            return None

        with self.cache_lock:
            if user_id in self.user_clients_cache:
                user_specific_clients = self.user_clients_cache[user_id]
                if server_identifier in user_specific_clients:
                    # Mark as recently used
                    user_specific_clients.move_to_end(server_identifier)
                    self.user_clients_cache.move_to_end(user_id)
                    return user_specific_clients[server_identifier].client
        return None

    def get_tools_for_client(self, user_id: str, server_identifier: str) -> Dict[str, ToolInfo] | None:
        """
        Retrieves the tools associated with a specific client instance for a user.

        Args:
            user_id: The user's identifier.
            server_identifier: The server's identifier.

        Returns:
            A dictionary of tool_name -> ToolInfo if the client and tools exist, else None.
            Returns a copy to prevent external modification of the cache.
        """
        if MAX_CACHED_MCP_USERS <= 0 or MAX_MCP_CLIENT_INSTANCES_PER_USER <= 0:
            return None

        with self.cache_lock:
            if user_id in self.user_clients_cache:
                user_specific_clients = self.user_clients_cache[user_id]
                if server_identifier in user_specific_clients:
                    # Mark as recently used
                    user_specific_clients.move_to_end(server_identifier)
                    self.user_clients_cache.move_to_end(user_id)
                    # Return a copy of the tools dictionary
                    return user_specific_clients[server_identifier].fetched_tools.copy()
        return None

    def get_all_tools_for_user(self, user_id: str) -> Dict[str, ToolInfo]:
        """
        Retrieves all tools from all active client instances for a given user.
        Tool names from different servers might overwrite each other if they are identical.
        A common approach is to prefix tool names with server_identifier if global uniqueness is needed.
        For this implementation, we'll do a simple merge, where later servers' tools might override earlier ones.

        Args:
            user_id: The user's identifier.

        Returns:
            A dictionary consolidating all tools (tool_name -> ToolInfo) for the user.
            Returns an empty dict if the user is not found or has no tools.
        """
        all_user_tools: Dict[str, ToolInfo] = {}
        if MAX_CACHED_MCP_USERS <= 0 or MAX_MCP_CLIENT_INSTANCES_PER_USER <= 0:
            return all_user_tools

        with self.cache_lock:
            if user_id in self.user_clients_cache:
                user_specific_clients = self.user_clients_cache[user_id]
                # Iterate in order of use (though for merging, order might not matter unless preferring specific server's tools)
                # To make it LRU, iterate and move_to_end each server_id as accessed.
                # For this aggregation, we just need the data.
                for server_id in list(user_specific_clients.keys()):  # Iterate over a copy of keys for safe move_to_end
                    client_info = user_specific_clients[server_id]
                    all_user_tools.update(client_info.fetched_tools)  # Simple merge
                    user_specific_clients.move_to_end(server_id)  # Mark this client connection as used

                self.user_clients_cache.move_to_end(user_id)  # Mark user as recently accessed
        return all_user_tools

    def remove_client(self, user_id: str, server_identifier: str) -> bool:
        """
        Removes a specific client instance and its tools from the cache.
        Attempts to call close() on the client if the method exists.

        Args:
            user_id: The user's identifier.
            server_identifier: The server's identifier.

        Returns:
            True if the client was found and removed, False otherwise.
        """
        with self.cache_lock:
            if user_id in self.user_clients_cache:
                user_specific_clients = self.user_clients_cache[user_id]
                if server_identifier in user_specific_clients:
                    evicted_client_info = user_specific_clients.pop(server_identifier)
                    print(f"Removed client for server '{server_identifier}' for user '{user_id}'.")

                    # Optionally, attempt to close the client
                    if hasattr(evicted_client_info.client, 'close'):
                        try:
                            evicted_client_info.client.close()
                            print(f"Closed client for server '{server_identifier}'.")
                        except Exception as e:
                            print(f"Error closing client for server '{server_identifier}': {e}")

                    if not user_specific_clients:  # If this was the last client for the user
                        del self.user_clients_cache[user_id]
                        print(f"User '{user_id}' has no more cached clients, removed from user cache.")
                    return True
        print(f"Client for server '{server_identifier}' for user '{user_id}' not found for removal.")
        return False

    def clear_user_cache(self, user_id: str):
        """
        Clears all client instances and tools for a specific user.
        Attempts to close all clients for that user.
        """
        with self.cache_lock:
            if user_id in self.user_clients_cache:
                user_specific_clients = self.user_clients_cache.pop(user_id)
                for server_id, client_info in user_specific_clients.items():
                    if hasattr(client_info.client, 'close'):
                        try:
                            client_info.client.close()
                        except Exception as e:
                            print(f"Error closing client for server '{server_id}' during user cache clear: {e}")
                print(f"Cleared all MCP client caches for user '{user_id}'.")
            else:
                print(f"No cache found for user '{user_id}' to clear.")

    def clear_all_caches(self):
        """
        Clears the entire cache of users and their client instances.
        Attempts to close all cached clients.
        """
        with self.cache_lock:
            for user_id, user_specific_clients in list(self.user_clients_cache.items()):
                for server_id, client_info in user_specific_clients.items():
                    if hasattr(client_info.client, 'close'):
                        try:
                            client_info.client.close()
                        except Exception as e:
                            print(
                                f"Error closing client for server '{server_id}' for user '{user_id}' during all cache clear: {e}")
            self.user_clients_cache.clear()
            print("Cleared all MCP user client caches.")
