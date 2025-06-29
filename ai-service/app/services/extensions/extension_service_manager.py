import asyncio
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
    It maintains an LRU cache for frequently used services and fetches services
    on-demand from the extension service when not cached.
    """

    def __init__(self):
        """
        Initializes the ExtensionServiceManager.
        - Initializes an LRU cache for services.
        - Sets up a lock for async-safe operations.
        """
        # LRU Cache for services.
        # Key: service_enum (str), Value: ExtensionServiceInfo
        self.service_cache: OrderedDictType[str, ExtensionServiceInfo] = OrderedDict()

        # Lock for ensuring async-safety when accessing/modifying the service_cache.
        self.cache_lock = asyncio.Lock()

        if MAX_CACHED_EXTENSION_SERVICES <= 0:
            logger.warning("MAX_CACHED_EXTENSION_SERVICES is non-positive. Cache will be disabled.")

    async def aget_service_info(self, service_enum: str) -> Optional[ExtensionServiceInfo]:
        """
        Retrieves an extension service.
        First checks the cache, if not found, fetches from extension service and adds to cache.
        Uses LRU eviction when cache is full.

        Args:
            service_enum: The unique enum of the service to retrieve.

        Returns:
            An ExtensionServiceInfo object if the service is found, otherwise None.
        """
        service_enum = service_enum.lower()  # Normalize service_enum to lowercase for consistency

        async with self.cache_lock:  # Ensure async-safe access to the cache
            # 1. Handle disabled cache scenario
            if MAX_CACHED_EXTENSION_SERVICES <= 0:
                logger.debug(f"Service caching disabled. Fetching '{service_enum}' directly from extension service.")
                try:
                    from app.services.extensions.extension_client import extension_client

                    return await extension_client.aget_extension_service_info(service_enum)
                except Exception as e:
                    logger.error(f"Failed to fetch service '{service_enum}': {str(e)}")
                    return None

            # 2. Check cache first
            if service_enum in self.service_cache:
                self.service_cache.move_to_end(service_enum)  # Mark as recently used
                logger.debug(f"Service '{service_enum}' found in cache. Marked as recently used.")
                return self.service_cache[service_enum]

            # 3. Service not in cache, fetch from extension service
            try:
                from app.services.extensions.extension_client import extension_client

                logger.debug(f"Service '{service_enum}' not in cache. Fetching from extension service.")
                service_info = await extension_client.aget_extension_service_info(service_enum)

                if not service_info:
                    logger.warning(f"Service '{service_enum}' not found in extension service.")
                    return None

                # 4. Add to cache with LRU eviction if needed
                if len(self.service_cache) >= MAX_CACHED_EXTENSION_SERVICES:
                    # Evict the least recently used service (oldest item)
                    evicted_service_enum, _ = self.service_cache.popitem(last=False)
                    logger.info(
                        f"Service cache limit ({MAX_CACHED_EXTENSION_SERVICES}) reached. "
                        f"Evicted '{evicted_service_enum}' to make space for '{service_enum}'."
                    )

                # Add the new service to the cache
                self.service_cache[service_enum] = service_info
                logger.info(f"Service '{service_enum}' fetched and added to cache.")
                return service_info

            except Exception as e:
                logger.error(f"Failed to fetch service '{service_enum}' from extension service: {str(e)}")
                return None

    async def get_fresh_service_info(self, service_enum: str) -> Optional[ExtensionServiceInfo]:
        """
        Get fresh service information directly from the extension service,
        and update the cache with the fresh info.

        Args:
            service_enum: The unique enum of the service to retrieve.

        Returns:
            An ExtensionServiceInfo object if the service is found, otherwise None.
        """
        service_enum = service_enum.lower()

        try:
            from app.services.extensions.extension_client import extension_client

            logger.debug(f"Fetching fresh service info for '{service_enum}' from extension service")
            fresh_service_info = await extension_client.aget_extension_service_info(service_enum)

            if fresh_service_info:
                logger.debug(f"Successfully retrieved fresh service info for '{service_enum}'")
                # Update the cache with fresh info
                async with self.cache_lock:
                    if service_enum in self.service_cache:
                        self.service_cache[service_enum] = fresh_service_info
                        self.service_cache.move_to_end(service_enum)  # Mark as recently used
                        logger.debug(f"Updated cached service info for '{service_enum}'")
            else:
                logger.warning(f"Fresh service info not found for '{service_enum}'")

            return fresh_service_info

        except Exception as e:
            logger.error(f"Failed to get fresh service info for '{service_enum}': {str(e)}")
            return None

    async def get_cached_services_info(self) -> Dict[str, ExtensionServiceInfo]:
        """
        Returns information about all currently cached extension services.

        Returns:
            A dictionary copy of the service cache.
        """
        async with self.cache_lock:
            return self.service_cache.copy()

    async def clear_service_cache(self):
        """
        Clears all services from the service cache.
        """
        async with self.cache_lock:
            self.service_cache.clear()
            logger.info("Service cache has been cleared.")

    async def remove_service_from_cache(self, service_enum: str) -> bool:
        """
        Removes a specific service from the cache.

        Args:
            service_enum: The unique enum of the service to remove.

        Returns:
            True if the service was removed, False if it wasn't in the cache.
        """
        service_enum = service_enum.lower()

        async with self.cache_lock:
            if service_enum in self.service_cache:
                del self.service_cache[service_enum]
                logger.info(f"Service '{service_enum}' removed from cache.")
                return True
            else:
                logger.debug(f"Service '{service_enum}' not found in cache.")
                return False

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        return {
            "cached_services_count": len(self.service_cache),
            "max_cached_services": MAX_CACHED_EXTENSION_SERVICES,
            "cache_enabled": MAX_CACHED_EXTENSION_SERVICES > 0,
        }


extension_service_manager = ExtensionServiceManager()