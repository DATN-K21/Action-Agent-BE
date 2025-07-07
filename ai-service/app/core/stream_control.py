"""
Stream control module for managing active streaming connections.

This module provides async-safe operations for managing streaming session state,
including stop flags and active connection tracking with memory-aware caching.
"""

import asyncio

from app.core import logging
from app.core.cache import CacheConfig, EvictionPolicy, global_cache_manager
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

# Memory-aware cache for active streaming connections
_connections_cache = None
_cache_initialized = False


async def _initialize_connections_cache():
    """Initialize the memory-aware cache for streaming connections."""
    global _connections_cache, _cache_initialized

    if _cache_initialized:
        return

    # Configure cache for streaming connections
    cache_config = CacheConfig(
        max_entries=env_settings.STREAMING_CONNECTIONS_CACHE_MAX_ENTRIES,  # Maximum concurrent connections
        max_memory_mb=env_settings.STREAMING_CONNECTIONS_CACHE_MAX_MEMORY_MB,  # x MB for connection tracking
        ttl_seconds=env_settings.CACHE_TTL_SECONDS,  #  x seconds TTL for inactive connections
        eviction_policy=EvictionPolicy.MEMORY_PRESSURE,
        memory_check_interval=env_settings.CACHE_MEMORY_CHECK_INTERVAL,  # Check every x seconds (reduced frequency)
        memory_threshold=env_settings.CACHE_MEMORY_THRESHOLD,  # Use configurable threshold
        cleanup_ratio=env_settings.CACHE_CLEANUP_RATIO,  # Use configurable cleanup ratio
        enable_size_tracking=True,
    )

    _connections_cache = await global_cache_manager.create_cache("streaming_connections", cache_config)
    _cache_initialized = True

    logger.info(
        f"Initialized memory-aware cache for streaming connections: "
        f"max_entries={cache_config.max_entries}, "
        f"max_memory_mb={cache_config.max_memory_mb}"
    )


async def acreate_stop_event(user_id: str, thread_id: str) -> asyncio.Event:
    """
    Create a stop event for a specific user and thread combination.

    Args:
        user_id: The user identifier
        thread_id: The thread identifier

    Returns:
        asyncio.Event: The stop event for this connection
    """
    connection_key = f"{user_id}:{thread_id}"
    stop_event = asyncio.Event()

    await _initialize_connections_cache()
    if _connections_cache is not None:
        await _connections_cache.put(connection_key, stop_event)
        logger.debug(f"Created stop event for connection '{connection_key}'")

    return stop_event


async def atrigger_stop(user_id: str, thread_id: str) -> bool:
    """
    Trigger stop for a specific user and thread combination.

    Args:
        user_id: The user identifier
        thread_id: The thread identifier

    Returns:
        bool: True if the connection was found and stop was triggered, False otherwise
    """
    connection_key = f"{user_id}:{thread_id}"

    await _initialize_connections_cache()
    if _connections_cache is None:
        return False

    stop_event = await _connections_cache.get(connection_key)
    if stop_event is not None:
        stop_event.set()
        logger.debug(f"Triggered stop for connection '{connection_key}'")
        return True

    return False


async def acleanup_connection(user_id: str, thread_id: str) -> None:
    """
    Clean up a connection after streaming is complete.

    Args:
        user_id: The user identifier
        thread_id: The thread identifier
    """
    connection_key = f"{user_id}:{thread_id}"

    await _initialize_connections_cache()
    if _connections_cache is not None:
        removed = await _connections_cache.remove(connection_key)
        if removed:
            logger.debug(f"Cleaned up connection '{connection_key}'")


async def ais_stop_requested(user_id: str, thread_id: str) -> bool:
    """
    Check if stop has been requested for a specific connection.

    Args:
        user_id: The user identifier
        thread_id: The thread identifier

    Returns:
        bool: True if stop was requested, False otherwise
    """
    connection_key = f"{user_id}:{thread_id}"

    await _initialize_connections_cache()
    if _connections_cache is None:
        return False

    stop_event = await _connections_cache.get(connection_key)
    if stop_event is not None:
        return stop_event.is_set()

    return False


async def aget_active_connections_count() -> int:
    """
    Get the number of active streaming connections.

    Returns:
        int: Number of active connections
    """
    await _initialize_connections_cache()
    if _connections_cache is None:
        return 0

    stats = await _connections_cache.get_stats()
    return stats["entries_count"]


async def aget_connections_stats() -> dict:
    """
    Get detailed statistics about streaming connections.

    Returns:
        dict: Connection statistics including memory usage and cache performance
    """
    await _initialize_connections_cache()
    if _connections_cache is None:
        return {"active_connections": 0, "cache_enabled": False}

    stats = await _connections_cache.get_stats()

    return {
        "active_connections": stats["entries_count"],
        "cache_enabled": True,
        "cache_memory_mb": stats["cache_memory_mb"],
        "hit_rate": stats["hit_rate"],
        "total_hits": stats["total_hits"],
        "total_misses": stats["total_misses"],
        "total_evictions": stats["total_evictions"],
        "memory_pressure_events": stats["memory_pressure_events"],
        "expired_connections": stats["expired_entries"],
    }


async def aclear_all_connections() -> None:
    """
    Clear all active connections from the cache.
    Useful for maintenance or shutdown procedures.
    """
    await _initialize_connections_cache()
    if _connections_cache is not None:
        await _connections_cache.clear()
        logger.info("Cleared all streaming connections from cache")
