from typing import Any, Dict, Optional

from app.core import logging
from app.core.cache import CacheConfig, EvictionPolicy, global_cache_manager
from app.core.settings import env_settings
from app.services.extensions.extension_client import ExtensionServiceInfo

logger = logging.get_logger(__name__)

# --- Constants ---
MAX_CACHED_EXTENSION_SERVICES = env_settings.MAX_CACHED_EXTENSION_SERVICES


class ExtensionServiceManager:
    """
    Manages and provides access to various extension services.
    It maintains a memory-aware cache for frequently used services and fetches services
    on-demand from the extension service when not cached.
    """

    def __init__(self):
        """
        Initializes the ExtensionServiceManager.
        - Initializes a memory-aware cache for services.
        - Sets up async initialization for cache.
        """
        # Memory-aware cache for services
        self.service_cache = None
        self.cache_initialized = False

        if MAX_CACHED_EXTENSION_SERVICES <= 0:
            logger.warning("MAX_CACHED_EXTENSION_SERVICES is non-positive. Cache will be disabled.")

    async def _initialize_cache(self):
        """Initialize the memory-aware cache for extension services."""
        if self.cache_initialized:
            return

        if MAX_CACHED_EXTENSION_SERVICES > 0:
            # Configure cache with memory limits
            cache_config = CacheConfig(
                max_entries=MAX_CACHED_EXTENSION_SERVICES,
                max_memory_mb=256.0,  # 256MB for extension service cache
                ttl_seconds=3600.0,  # 1 hour TTL
                eviction_policy=EvictionPolicy.MEMORY_PRESSURE,
                memory_check_interval=90.0,  # Check every 90 seconds (reduced frequency)
                memory_threshold=0.85,  # Increased threshold
                cleanup_ratio=0.25,  # Reduced cleanup ratio
                enable_size_tracking=True,
            )

            self.service_cache = await global_cache_manager.create_cache("extension_services", cache_config)

            logger.info(
                f"Initialized memory-aware cache for extension services: "
                f"max_entries={cache_config.max_entries}, "
                f"max_memory_mb={cache_config.max_memory_mb}"
            )

        self.cache_initialized = True

    async def aget_service_info(self, service_enum: str) -> Optional[ExtensionServiceInfo]:
        """
        Retrieves an extension service.
        First checks the cache, if not found, fetches from extension service and adds to cache.
        Uses memory-aware eviction when needed.

        Args:
            service_enum: The unique enum of the service to retrieve.

        Returns:
            An ExtensionServiceInfo object if the service is found, otherwise None.
        """
        service_enum = service_enum.lower()  # Normalize service_enum to lowercase for consistency

        # Initialize cache if not already done
        await self._initialize_cache()

        # Handle disabled cache scenario
        if MAX_CACHED_EXTENSION_SERVICES <= 0 or self.service_cache is None:
            logger.debug(f"Service caching disabled. Fetching '{service_enum}' directly from extension service.")
            try:
                from app.services.extensions.extension_client import extension_client

                return await extension_client.aget_extension_service_info(service_enum)
            except Exception as e:
                logger.error(f"Failed to fetch service '{service_enum}': {str(e)}")
                return None

        # Check cache first
        cached_service = await self.service_cache.get(service_enum)
        if cached_service is not None:
            logger.debug(f"Service '{service_enum}' found in cache.")
            return cached_service

        # Service not in cache, fetch from extension service
        try:
            from app.services.extensions.extension_client import extension_client

            logger.debug(f"Service '{service_enum}' not in cache. Fetching from extension service.")
            service_info = await extension_client.aget_extension_service_info(service_enum)

            if not service_info:
                logger.warning(f"Service '{service_enum}' not found in extension service.")
                return None

            # Add to cache (Memory Cache Manager handles eviction automatically)
            await self.service_cache.put(service_enum, service_info)
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
                await self._initialize_cache()
                if self.service_cache is not None:
                    await self.service_cache.put(service_enum, fresh_service_info)
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
            A dictionary of cached services (limited functionality with memory cache).
        """
        await self._initialize_cache()
        if self.service_cache is None:
            return {}

        # Note: Memory cache doesn't support direct iteration like OrderedDict
        # This is a limitation when migrating to memory-aware cache
        logger.warning("get_cached_services_info: Direct cache iteration not supported by MemoryCacheManager")
        return {}

    async def clear_service_cache(self):
        """
        Clears all services from the service cache.
        """
        await self._initialize_cache()
        if self.service_cache is not None:
            await self.service_cache.clear()
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

        await self._initialize_cache()
        if self.service_cache is None:
            logger.debug(f"Cache not initialized. Service '{service_enum}' not found in cache.")
            return False

        removed = await self.service_cache.remove(service_enum)
        if removed:
            logger.info(f"Service '{service_enum}' removed from cache.")
        else:
            logger.debug(f"Service '{service_enum}' not found in cache.")
        return removed

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        await self._initialize_cache()

        if self.service_cache is None:
            return {
                "cached_services_count": 0,
                "max_cached_services": MAX_CACHED_EXTENSION_SERVICES,
                "cache_enabled": False,
            }

        # Get detailed stats from memory-aware cache
        cache_stats = await self.service_cache.get_stats()

        return {
            "cached_services_count": cache_stats["entries_count"],
            "max_cached_services": MAX_CACHED_EXTENSION_SERVICES,
            "cache_enabled": True,
            "cache_memory_mb": cache_stats["cache_memory_mb"],
            "hit_rate": cache_stats["hit_rate"],
            "total_hits": cache_stats["total_hits"],
            "total_misses": cache_stats["total_misses"],
            "total_evictions": cache_stats["total_evictions"],
            "memory_pressure_events": cache_stats["memory_pressure_events"],
        }


extension_service_manager = ExtensionServiceManager()