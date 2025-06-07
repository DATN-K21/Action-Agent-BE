import importlib
import os
import re
import threading
from collections import OrderedDict
from typing import Any, Dict

from langchain.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper

from app.core import logging
from app.core.models import ToolInfo
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

# --- Constants ---
MAX_PERSONAL_TOOLS_PER_USER = env_settings.MAX_PERSONAL_TOOLS_PER_USER
MAX_CACHED_USERS = env_settings.MAX_CACHED_USERS
DEFAULT_TOOLS_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))


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
    processed_text = re.sub(r'[\s_]+', '-', processed_text)

    # Remove any character that is not a lowercase letter, a digit, or a hyphen
    processed_text = re.sub(r'[^a-z0-9-]', '', processed_text)

    # Replace multiple consecutive hyphens with a single hyphen
    processed_text = re.sub(r'-+', '-', processed_text)

    # Remove leading or trailing hyphens
    processed_text = processed_text.strip('-')

    return processed_text


def create_unique_key(skill_id: str, skill_name: str) -> str:
    """
    Creates a unique and standardized personal skill name.
    It joins a standardized skill_id and a standardized, lowercase skill_name.
    """
    if not skill_id:
        raise ValueError("skill_id cannot be empty.")

    standardized_id = _standardize_name_part(skill_id)
    standardized_name = _standardize_name_part(skill_name)  # skill_name part is already lowercased by _standardize_name_part

    if not standardized_id and not standardized_name:
        # This could happen if both inputs consist only of characters that are removed
        raise ValueError("Both skill_id and skill_name resulted in empty strings after standardization.")

    if not standardized_id:  # If skill_id became empty after standardization (e.g. "!!!")
        return standardized_name  # Return only the name part if it's valid

    if not standardized_name:  # If skill_name became empty after standardization
        return standardized_id  # Return only the id part

    return f"{standardized_id}-{standardized_name}"


class ToolManager:
    def __init__(self, tools_package_path: str = DEFAULT_TOOLS_PACKAGE_PATH):
        # tool_key -> ToolInfo
        self.global_tools: Dict[str, ToolInfo] = {}
        # user_id -> tool_key -> ToolInfo
        self.personal_tool_cache: OrderedDict[str, OrderedDict[str, ToolInfo]] = OrderedDict()
        self.tools_package_path = tools_package_path

        # Initialize the lock
        self.cache_lock = threading.Lock()  # For asyncio, this would be asyncio.Lock()

        if MAX_CACHED_USERS <= 0:
            logger.warning("Warning: MAX_CACHED_USERS non-positive. Personal user caching disabled.")
        if MAX_PERSONAL_TOOLS_PER_USER <= 0:
            logger.warning("Warning: MAX_PERSONAL_TOOLS_PER_USER non-positive. Per-user tool caching disabled.")

        self._load_initial_global_tools()  # Assumed to be called before concurrent access begins

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
            if not hasattr(package_module, '__path__'):
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
                                    credentials_module = importlib.import_module(
                                        cred_module_name, package=self.tools_package_path
                                    )
                                    if hasattr(credentials_module, "get_credentials"):
                                        raw_credentials = credentials_module.get_credentials()
                                        credentials = {
                                            k: {**v, "value": ""} for k, v in raw_credentials.items()
                                        }
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
                description="Searches web via DuckDuckGo.",
                tool=DuckDuckGoSearchRun(),
                display_name="DuckDuckGo Search",
                input_parameters={"query": {"type": "string", "required": True, "description": "Search query."}},
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

    def add_personal_tool(self, user_id: str, tool_key: str, tool_info: ToolInfo):
        # For asyncio: async def add_personal_tool(self, ...):
        # For asyncio:     async with self.cache_lock:
        with self.cache_lock:  # Acquire lock
            if MAX_CACHED_USERS <= 0:
                return

            user_specific_cache: OrderedDict[str, ToolInfo]
            if user_id in self.personal_tool_cache:
                user_specific_cache = self.personal_tool_cache[user_id]
                self.personal_tool_cache.move_to_end(user_id)
            else:
                if len(self.personal_tool_cache) >= MAX_CACHED_USERS:
                    lru_user_id, _ = self.personal_tool_cache.popitem(last=False)
                    logger.warning(f"User cache limit ({MAX_CACHED_USERS}) hit. Evicted: '{lru_user_id}'.")
                user_specific_cache = OrderedDict()
                self.personal_tool_cache[user_id] = user_specific_cache

            if MAX_PERSONAL_TOOLS_PER_USER <= 0:
                return

            if tool_key in user_specific_cache:
                user_specific_cache.move_to_end(tool_key)
            user_specific_cache[tool_key] = tool_info

            while len(user_specific_cache) > MAX_PERSONAL_TOOLS_PER_USER:
                dropped_tool_key, _ = user_specific_cache.popitem(last=False)
                logger.warning(f"Tool limit ({MAX_PERSONAL_TOOLS_PER_USER}) for '{user_id}' hit. Evicted: '{dropped_tool_key}'.")
        # Lock is released automatically when exiting 'with' block

    def get_personal_tool(self, user_id: str, tool_key: str) -> ToolInfo:
        # For asyncio: async def get_personal_tool(self, ...):
        # For asyncio:     async with self.cache_lock:
        with self.cache_lock:  # Acquire lock
            if user_id in self.personal_tool_cache:
                self.personal_tool_cache.move_to_end(user_id)
                user_specific_cache = self.personal_tool_cache[user_id]

                if tool_key in user_specific_cache:
                    user_specific_cache.move_to_end(tool_key)
                    return user_specific_cache[tool_key]
            raise KeyError(f"Personal tool '{tool_key}' for user '{user_id}' not found in cache.")
        # Lock is released

    def get_tools_for_user(self, user_id: str) -> Dict[str, ToolInfo]:
        # This method involves both read (global_tools) and potential read/write (personal_tool_cache)
        available_tools = self.global_tools.copy()  # Read-only access to global_tools after init is safe
        user_personal_tools_snapshot: Dict[str, ToolInfo] = {}

        # For asyncio: async with self.cache_lock:
        with self.cache_lock:  # Acquire lock for operations on personal_tool_cache
            if MAX_CACHED_USERS > 0 and user_id in self.personal_tool_cache:
                self.personal_tool_cache.move_to_end(user_id)
                user_lru_cache = self.personal_tool_cache[user_id]

                if MAX_PERSONAL_TOOLS_PER_USER > 0:
                    for name_key in list(user_lru_cache.keys()):
                        tool_data = user_lru_cache[name_key]
                        user_lru_cache.move_to_end(name_key)
                        user_personal_tools_snapshot[name_key] = tool_data
        # Lock is released

        available_tools.update(user_personal_tools_snapshot)
        return available_tools

    def get_global_tools(self) -> Dict[str, ToolInfo]:
        # Reading global_tools is safe as it's populated at init and then read-only.
        return self.global_tools.copy()

    def clear_personal_tool_cache(self, user_id: str | None = None):
        # For asyncio: async def clear_personal_tool_cache(self, ...):
        # For asyncio:     async with self.cache_lock:
        with self.cache_lock:  # Acquire lock
            if user_id:
                if user_id in self.personal_tool_cache:
                    del self.personal_tool_cache[user_id]
                    logger.info(f"Cleared personal tool cache for user '{user_id}'.")
            else:
                self.personal_tool_cache.clear()
                logger.info("Cleared all personal tool caches.")
        # Lock is released


tool_manager = ToolManager()
global_tools = tool_manager.get_global_tools()
