import threading
from collections import OrderedDict
from typing import Dict, Optional
from typing import OrderedDict as OrderedDictType

from app.core import logging
from app.core.settings import env_settings
from app.services.extensions.extension_client import ExtensionServiceInfo

logger = logging.get_logger(__name__)

# --- Constants ---
MAX_CACHED_EXTENSION_SERVICES = env_settings.MAX_CACHED_EXTENSION_SERVICES


class ExtensionServiceManager:
    """
    Manages and provides access to various extension services.
    It maintains a list of all available services and an LRU cache for frequently used active services.
    """

    def __init__(self):
        """
        Initializes the ExtensionServiceManager.
        - Loads all defined extension services.
        - Initializes an LRU cache for active services.
        - Sets up a lock for thread-safe operations.
        """
        # Stores all services that are defined and can be potentially used.
        # Key: service_enum (str), Value: ExtensionServiceInfo
        self.all_defined_services: Dict[str, ExtensionServiceInfo] = {}

        # LRU Cache for active/frequently used services.
        # Key: service_enum (str), Value: ExtensionServiceInfo
        self.active_service_cache: OrderedDictType[str, ExtensionServiceInfo] = OrderedDict()

        # Lock for ensuring thread-safety when accessing/modifying the active_service_cache.
        self.cache_lock = threading.Lock()

        if MAX_CACHED_EXTENSION_SERVICES <= 0:
            logger.info(
                "MAX_CACHED_SERVICES is non-positive. Active service caching will be disabled. Services will be fetched from all_defined_services directly.")

        self._load_all_defined_services()  # Load all ~300 services

    def _load_all_defined_services(self):
        """
        Loads all available extension services into `self.all_defined_services`.
        This method should be implemented to discover and register all your ~300 services.
        For example, services could be defined in a configuration file, database,
        or discovered by scanning specific modules/packages.

        For demonstration purposes, a few dummy services are loaded here.
        """
        pass

    def reload_all_defined_services(self):
        self._load_all_defined_services()

    def get_service_info(self, service_enum: str) -> Optional[ExtensionServiceInfo]:
        """
        Retrieves an extension service.
        If the service is in the active_service_cache, it's returned and marked as recently used.
        If not in the cache but available in all_defined_services, it's added to the cache
        (evicting the oldest if the cache is full and caching is enabled) and then returned.
        If caching is disabled (MAX_CACHED_SERVICES <= 0), it's fetched directly from all_defined_services.

        Args:
            service_enum: The unique enum of the service to retrieve.

        Returns:
            An ExtensionServiceInfo object if the service is found, otherwise None.
        """
        with self.cache_lock:  # Ensure thread-safe access to the cache
            # 1. Handle disabled cache scenario
            if MAX_CACHED_EXTENSION_SERVICES <= 0:
                if service_enum in self.all_defined_services:
                    logger.debug(f"Service caching disabled. Returning '{service_enum}' directly from defined services.")
                    # Return a copy to prevent external modification of the master record if service_object is mutable
                    # For this example, we assume ExtensionServiceInfo is mostly immutable or service_object is robust
                    return self.all_defined_services[service_enum]
                else:
                    logger.warning(f"Service '{service_enum}' not found in defined services.")
                    return None

            # 2. Caching is enabled: Check active_service_cache first
            if service_enum in self.active_service_cache:
                self.active_service_cache.move_to_end(service_enum)  # Mark as recently used
                logger.debug(f"Service '{service_enum}' found in active cache. Marked as recently used.")
                return self.active_service_cache[service_enum]

            # 3. Service not in active cache, check all_defined_services
            if service_enum in self.all_defined_services:
                # Check if cache is full before adding
                if len(self.active_service_cache) >= MAX_CACHED_EXTENSION_SERVICES:
                    # Evict the least recently used service (oldest item)
                    evicted_service_enum, _ = self.active_service_cache.popitem(last=False)
                    logger.info(
                        f"Active service cache limit ({MAX_CACHED_EXTENSION_SERVICES}) reached. "
                        f"Evicted '{evicted_service_enum}' to make space for '{service_enum}'."
                    )

                # Add the new service to the active cache
                service_to_cache = self.all_defined_services[service_enum]
                # Potentially, this is where you might instantiate or prepare the service_object
                # if `all_defined_services` only holds metadata or factories.
                # For example, if service_to_cache.service_object is a factory function:
                # actual_instance = service_to_cache.service_object()
                # service_instance_for_cache = service_to_cache.copy(update={'service_object': actual_instance})
                # self.active_service_cache[service_enum] = service_instance_for_cache
                self.active_service_cache[service_enum] = service_to_cache
                logger.info(f"Service '{service_enum}' loaded from defined services into active cache.")
                return service_to_cache

            # 4. Service not found anywhere
            logger.warning(f"Service '{service_enum}' not found in defined services or active cache.")
            return None

    def get_all_available_services_info(self) -> Dict[str, ExtensionServiceInfo]:
        """
        Returns information about all defined extension services.
        This provides a snapshot of all services the manager knows about, not just active ones.

        Returns:
            A dictionary copy of all defined services.
        """
        # `all_defined_services` is populated at init and then typically read-only.
        # Returning a copy is good practice if there's any chance of modification.
        return self.all_defined_services.copy()

    def get_active_cached_services_info(self) -> Dict[str, ExtensionServiceInfo]:
        """
        Returns information about all currently active and cached extension services.

        Returns:
            A dictionary copy of the active service cache.
        """
        with self.cache_lock:
            return self.active_service_cache.copy()

    def clear_active_service_cache(self):
        """
        Clears all services from the active service cache.
        """
        with self.cache_lock:
            self.active_service_cache.clear()
            logger.info("Active service cache has been cleared.")


extension_service_manager = ExtensionServiceManager()