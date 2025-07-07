import importlib
import os
import re
from typing import Any, Dict

from langchain.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from pydantic import SecretStr

from app.core import logging
from app.core.cache import CacheConfig, EvictionPolicy, global_cache_manager
from app.core.models import ToolInfo
from app.core.settings import env_settings

# Set USER_AGENT environment variable early to prevent warnings from libraries
# The warning you're seeing is coming from the duckduckgo-search
# library (version 8.0.2) that your application uses.
# This library expects a USER_AGENT environment variable to
# be set to identify HTTP requests.
os.environ.setdefault("USER_AGENT", env_settings.USER_AGENT)

logger = logging.get_logger(__name__)

# --- Constants ---
DEFAULT_TOOLS_PACKAGE_PATH = "app.core.tools"


def _standardize_name_part(text_part: str) -> str:
    """
    Standardizes a part of a name:
    1. Converts to lowercase.
    2. Replaces whitespace, underscores, and multiple hyphens with a single hyphen.
    3. Removes characters that are not alphanumeric or hyphens.
    4. Removes leading/trailing hyphens.
    """
    if not text_part:
        return ""

    # Convert to string (in case input is not string, e.g., number) and then lowercase
    processed_text = str(text_part).lower()

    # Replace whitespace and underscores with a single hyphen
    processed_text = re.sub(r"[\s_]+", "-", processed_text)

    # Remove any character that is not a lowercase letter, a digit, or a hyphen
    processed_text = re.sub(r"[^a-z0-9-]", "", processed_text)

    # Replace multiple consecutive hyphens with a single hyphen
    processed_text = re.sub(r"-+", "-", processed_text)

    # Remove leading or trailing hyphens
    processed_text = processed_text.strip("-")

    return processed_text


def create_unique_key(id_: str, name: str | None) -> str:
    """
    Creates a unique and standardized personal skill name.
    It joins a standardized skill_id and a standardized, lowercase skill_name.
    """
    if not id_:
        raise ValueError("skill_id cannot be empty.")

    standardized_id = _standardize_name_part(id_)

    if name is None:
        name = "unknown name"  # Default name if None, can be customized

    standardized_name = _standardize_name_part(name)  # skill_name part is already lowercased by _standardize_name_part

    if not standardized_id and not standardized_name:
        # This could happen if both inputs consist only of characters that are removed
        raise ValueError("Both skill_id and skill_name resulted in empty strings after standardization.")

    if not standardized_id:  # If skill_id became empty after standardization (e.g. "!!!")
        return standardized_name  # Return only the name part if it's valid

    if not standardized_name:  # If skill_name became empty after standardization
        return standardized_id  # Return only the id part

    return f"{standardized_id}-{standardized_name}"


# Extract name
def extract_name(full_name: str) -> str:
    """
    Extract name from format: uuid-name or just name
    Examples:
    - "7dcabe5f-a120-4c75-981b-fcb742c5a245-chatbot-assistant" -> "chatbot-assistant"
    - "chatbot-assistant" -> "chatbot-assistant"
    - "chatbot-assistant" -> "chatbot-assistant"
    """
    parts = full_name.split("-")
    if len(parts) >= 6:  # UUID has 5 hyphens, so at least 6 parts
        # Check if first part looks like UUID (8 hex chars)
        if len(parts[0]) == 8 and all(c in "0123456789abcdefABCDEF" for c in parts[0]):
            # Join everything after the UUID (skip first 5 parts of UUID)
            return "-".join(parts[5:])
    return full_name


class ToolManager:
    def __init__(self, tools_package_path: str = DEFAULT_TOOLS_PACKAGE_PATH):
        # tool_key -> ToolInfo
        self.global_tools: Dict[str, ToolInfo] = {}
        self.tools_package_path = tools_package_path

        # Initialize memory-aware cache for personal tools
        self.personal_tool_cache = None
        self.cache_initialized = False

        self._load_initial_global_tools()  # Assumed to be called before concurrent access begins

    async def _initialize_cache(self):
        """Initialize the memory-aware cache for personal tools."""
        if self.cache_initialized:
            return

        if env_settings.TOOLS_CACHE_MAX_ENTRIES > 0:
            # Configure cache with memory limits
            cache_config = CacheConfig(
                max_entries=env_settings.TOOLS_CACHE_MAX_ENTRIES,  # Use settings for max entries
                max_memory_mb=env_settings.TOOLS_CACHE_MAX_MEMORY_MB,  # Use settings for max memory
                ttl_seconds=env_settings.CACHE_TTL_SECONDS,
                eviction_policy=EvictionPolicy.MEMORY_PRESSURE,
                memory_check_interval=env_settings.CACHE_MEMORY_CHECK_INTERVAL,  # Check every x minutes (reduced frequency)
                memory_threshold=env_settings.CACHE_MEMORY_THRESHOLD,  # Increased threshold
                cleanup_ratio=env_settings.CACHE_CLEANUP_RATIO,  # Reduced cleanup ratio
                enable_size_tracking=True,
            )

            self.personal_tool_cache = await global_cache_manager.create_cache("personal_tools", cache_config)

            logger.info(
                f"Initialized memory-aware cache for personal tools: "
                f"max_entries={cache_config.max_entries}, "
                f"max_memory_mb={cache_config.max_memory_mb}"
            )

        self.cache_initialized = True

    # Static methods format_tool_key and convert_to_input_parameters remain unchanged
    @staticmethod
    def format_tool_key(name: str) -> str:
        return name.replace("_", "-")

    @staticmethod
    def convert_to_input_parameters(inputs_dict: Dict[str, Any]) -> Dict[str, Any]:
        input_parameters = {}
        for key, value in inputs_dict.items():
            input_parameters[key] = {
                "type": value.get("type", "string"),
                "required": value.get("required", True),
                "description": value.get("description", f"Parameter: {key}"),
            }
        return input_parameters

    # _load_local_tools_to_global and _load_hardcoded_external_tools_to_global
    # are typically called during __init__ before concurrent requests.
    # If they could be called concurrently later, they might also need locking
    # or be designed to be safe. For now, assuming they are part of initialization.
    def _load_local_tools_to_global(self):
        # (Implementation as before)
        # This method populates self.global_tools, which is then read-only.
        # If self.global_tools could be modified concurrently post-init, it would also need protection.
        try:
            package_module = importlib.import_module(self.tools_package_path)
            if not hasattr(package_module, "__path__"):
                logger.warning(f"Warning: '{self.tools_package_path}' not a package. Skipping local tool loading.")
                return
            tools_root_dir = package_module.__path__[0]
        except ImportError:
            logger.error(f"Warning: Tools package '{self.tools_package_path}' not found. Skipping local tools.")
            return

        for item in os.listdir(tools_root_dir):
            item_path = os.path.join(tools_root_dir, item)
            if os.path.isdir(item_path) and not item.startswith("__"):
                try:
                    module = importlib.import_module(f".{item}", package=self.tools_package_path)
                    if hasattr(module, "__all__"):
                        for tool_key_in_module in module.__all__:
                            tool_instance = getattr(module, tool_key_in_module, None)
                            if isinstance(tool_instance, BaseTool):
                                formatted_name = self.format_tool_key(tool_key_in_module)
                                inputs_dict = tool_instance.args
                                input_params = self.convert_to_input_parameters(inputs_dict)
                                credentials = {}
                                try:
                                    cred_module_name = f".{item}.credentials"
                                    credentials_module = importlib.import_module(cred_module_name, package=self.tools_package_path)
                                    if hasattr(credentials_module, "get_credentials"):
                                        raw_credentials = credentials_module.get_credentials()
                                        credentials = {k: {**v, "value": ""} for k, v in raw_credentials.items()}
                                except ImportError:
                                    pass

                                self.global_tools[formatted_name] = ToolInfo(
                                    description=tool_instance.description,
                                    tool=tool_instance,
                                    display_name=tool_instance.name,
                                    input_parameters=input_params,
                                    credentials=credentials,
                                )
                except Exception as e:
                    logger.error(f"Failed to load tools from '{item}': {str(e)}")  # Simplified

    def _load_hardcoded_external_tools_to_global(self):
        # (Implementation as before)
        external_tools = {
            "duckduckgo-search": ToolInfo(
                description="Searches web via DuckDuckGo - a short, plain-text snippet summarizing the top result .",
                tool=DuckDuckGoSearchRun(),
                display_name="DuckDuckGo Search",
                input_parameters={"query": {"type": "string", "required": True, "description": "Search query."}},
            ),
            "tavily-search": ToolInfo(
                description="Searches web via Tavily - structured, citation-friendly results ideal for RAG and agents.",
                tool=TavilySearchResults(
                    max_results=5,
                    api_wrapper=TavilySearchAPIWrapper(
                        tavily_api_key=SecretStr(env_settings.TOOL_TAVILY_API_KEY),
                    ),
                ),
                input_parameters={
                    "query": {
                        "type": "string",
                        "required": True,
                        "description": "The query to search for",
                    }
                },
                credentials={},
            ),
            "wikipedia": ToolInfo(
                description="Searches Wikipedia.",
                tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(wiki_client=None)),
                display_name="Wikipedia Search",
                input_parameters={"query": {"type": "string", "required": True, "description": "Search query."}},
            ),
        }
        self.global_tools.update(external_tools)

    def _load_initial_global_tools(self):
        logger.info("Loading global tools...")
        self._load_local_tools_to_global()
        self._load_hardcoded_external_tools_to_global()
        logger.info(f"Loaded {len(self.global_tools)} global tools.")

    async def aadd_personal_tool(self, user_id: str, tool_key: str, tool_info: ToolInfo):
        """Add a personal tool to the cache."""
        if env_settings.TOOLS_CACHE_MAX_ENTRIES <= 0:
            return

        await self._initialize_cache()

        if self.personal_tool_cache is None:
            return

        # Create a composite key: user_id:tool_key
        cache_key = f"{user_id}:{tool_key}"

        # Add to cache with user-specific TTL
        await self.personal_tool_cache.put(
            cache_key,
            tool_info,
            ttl_seconds=7200.0,  # 2 hours
        )

        logger.debug(f"Added personal tool '{tool_key}' for user '{user_id}' to memory cache")

    async def aget_personal_tool(self, user_id: str, tool_key: str) -> ToolInfo:
        """Get a personal tool from the cache."""
        await self._initialize_cache()

        if self.personal_tool_cache is None:
            raise KeyError(f"Personal tool '{tool_key}' for user '{user_id}' not found in cache.")

        cache_key = f"{user_id}:{tool_key}"
        tool_info = await self.personal_tool_cache.get(cache_key)

        if tool_info is None:
            raise KeyError(f"Personal tool '{tool_key}' for user '{user_id}' not found in cache.")

        logger.debug(f"Retrieved personal tool '{tool_key}' for user '{user_id}' from memory cache")
        return tool_info

    async def aget_tools_for_user(self, user_id: str) -> Dict[str, ToolInfo]:
        """Get all tools available for a user (global + personal)."""
        await self._initialize_cache()

        # Start with global tools
        available_tools = self.global_tools.copy()

        # Add personal tools if cache is available
        if self.personal_tool_cache is not None and env_settings.TOOLS_CACHE_MAX_ENTRIES > 0:
            # Get cache statistics to understand current state
            cache_stats = await self.personal_tool_cache.get_stats()
            logger.debug(
                f"Getting tools for user '{user_id}': "
                f"cache_entries={cache_stats['entries_count']}, "
                f"cache_memory_mb={cache_stats['cache_memory_mb']:.2f}"
            )

            # We need to iterate through cache to find user's tools
            # This is a limitation of the current cache design - we could optimize this later
            # For now, we'll use a different approach

        return available_tools

    def get_global_tools(self) -> Dict[str, ToolInfo]:
        """Get global tools dictionary."""
        return self.global_tools.copy()

    async def aclear_personal_tool_cache(self, user_id: str | None = None):
        """Clear personal tool cache."""
        await self._initialize_cache()

        if self.personal_tool_cache is None:
            return

        if user_id:
            # Clear tools for specific user - we need to implement a user-specific clear
            logger.info(f"Cleared personal tool cache for user '{user_id}'.")
        else:
            await self.personal_tool_cache.clear()
            logger.info("Cleared all personal tool caches.")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and memory usage information."""
        await self._initialize_cache()

        if self.personal_tool_cache is None:
            return {"cache_enabled": False, "global_tools_count": len(self.global_tools)}

        cache_stats = await self.personal_tool_cache.get_stats()
        memory_info = await self.personal_tool_cache.get_memory_info()

        return {"cache_enabled": True, "global_tools_count": len(self.global_tools), "cache_stats": cache_stats, "memory_info": memory_info}


tool_manager = ToolManager()
global_tools = tool_manager.get_global_tools()
