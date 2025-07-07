"""
Memory-aware cache manager with automatic memory monitoring and cleanup.

This module provides a sophisticated caching system that monitors memory usage
and automatically evicts cached objects when memory pressure is detected.
"""

import asyncio
import gc
import sys
import time
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, TypeVar

import psutil

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

# Type variable for cached objects
T = TypeVar("T")


class EvictionPolicy(Enum):
    """Cache eviction policies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    SIZE = "size"  # Size-based
    MEMORY_PRESSURE = "memory_pressure"  # Memory pressure based


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""

    value: Any
    access_count: int = 0
    size_bytes: int = 0
    created_at: float = 0.0
    last_accessed: float = 0.0
    ttl_seconds: Optional[float] = None

    def __post_init__(self):
        """Initialize timestamps after creation."""
        current_time = time.time()
        if self.created_at == 0.0:
            self.created_at = current_time
        if self.last_accessed == 0.0:
            self.last_accessed = current_time

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass
class CacheConfig:
    """Configuration for cache behavior."""

    max_entries: int = 1000
    max_memory_mb: float = 512.0  # Maximum memory usage in MB
    ttl_seconds: Optional[float] = 3600.0  # Default TTL: 1 hour
    eviction_policy: EvictionPolicy = EvictionPolicy.MEMORY_PRESSURE
    memory_check_interval: float = 30.0  # Check memory every 30 seconds
    memory_threshold: float = 0.8  # Trigger cleanup at 80% of max memory
    cleanup_ratio: float = 0.3  # Remove 30% of entries during cleanup
    enable_size_tracking: bool = True
    enable_weak_references: bool = False


class MemoryCacheManager:
    """
    Memory-aware cache manager with automatic cleanup and monitoring.

    Features:
    - Memory usage monitoring and automatic cleanup
    - Multiple eviction policies (LRU, LFU, TTL, Size-based, Memory pressure)
    - TTL support with automatic expiration
    - Detailed memory usage logging
    - Async-safe operations
    - Configurable memory thresholds
    - Automatic garbage collection integration
    """

    def __init__(self, name: str, config: CacheConfig):
        """
        Initialize the memory cache manager.

        Args:
            name: Name of the cache for logging purposes
            config: Cache configuration
        """
        self.name = name
        self.config = config
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = asyncio.Lock()

        # Memory monitoring
        self.process = psutil.Process()
        self.last_memory_check = 0.0
        self.total_memory_allocated = 0.0

        # Startup grace period to avoid immediate cleanup
        self.startup_time = time.time()
        self.startup_grace_period = env_settings.CACHE_STARTUP_GRACE_PERIOD  # Use configurable grace period

        # Statistics
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "cleanups": 0, "memory_pressure_events": 0, "expired_entries": 0}

        # Background cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self._should_stop = False

        logger.info(
            f"Initialized MemoryCacheManager '{self.name}' with config: "
            f"max_entries={config.max_entries}, max_memory_mb={config.max_memory_mb}, "
            f"ttl_seconds={config.ttl_seconds}, eviction_policy={config.eviction_policy.value}"
        )

    async def start_background_cleanup(self) -> None:
        """Start the background cleanup task."""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._background_cleanup())
            logger.info(f"Started background cleanup task for cache '{self.name}'")

    async def stop_background_cleanup(self) -> None:
        """Stop the background cleanup task."""
        self._should_stop = True
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info(f"Stopped background cleanup task for cache '{self.name}'")

    async def _background_cleanup(self) -> None:
        """Background task for periodic cleanup."""
        # Wait for grace period before starting cleanup
        grace_remaining = self.startup_grace_period - (time.time() - self.startup_time)
        if grace_remaining > 0:
            logger.info(f"Cache '{self.name}' waiting {grace_remaining:.1f}s before starting background cleanup")
            await asyncio.sleep(grace_remaining)

        while not self._should_stop:
            try:
                await asyncio.sleep(self.config.memory_check_interval)
                await self._check_and_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background cleanup for cache '{self.name}': {e}")
                await asyncio.sleep(5.0)  # Wait before retrying

    def _calculate_object_size(self, obj: Any) -> int:
        """
        Calculate the approximate size of an object in bytes.

        Args:
            obj: Object to measure

        Returns:
            Size in bytes
        """
        if not self.config.enable_size_tracking:
            return 0

        try:
            # Use sys.getsizeof for basic size, with recursion for containers
            size = sys.getsizeof(obj)

            # Add size of referenced objects for common container types
            if isinstance(obj, dict):
                size += sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in obj.items())
            elif isinstance(obj, (list, tuple, set)):
                size += sum(sys.getsizeof(item) for item in obj)
            elif hasattr(obj, "__dict__"):
                size += sys.getsizeof(obj.__dict__)
                size += sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in obj.__dict__.items())

            return size
        except Exception as e:
            logger.warning(f"Failed to calculate object size in cache '{self.name}': {e}")
            return 0

    def _get_current_memory_usage_mb(self) -> float:
        """Get current memory usage of the process in MB."""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert bytes to MB
        except Exception:
            return 0.0

    def _get_cache_memory_usage_mb(self) -> float:
        """Get estimated memory usage of the cache in MB."""
        total_size = sum(entry.size_bytes for entry in self.cache.values())
        return total_size / 1024 / 1024

    async def _check_memory_pressure(self) -> bool:
        """Check if system is under memory pressure."""
        current_time = time.time()
        if current_time - self.last_memory_check < self.config.memory_check_interval:
            return False

        # Skip memory pressure check during startup grace period
        if current_time - self.startup_time < self.startup_grace_period:
            logger.debug(f"Skipping memory pressure check during startup grace period for cache '{self.name}'")
            return False

        self.last_memory_check = current_time

        # Get detailed memory information
        cache_memory_mb = self._get_cache_memory_usage_mb()
        process_memory_mb = self._get_current_memory_usage_mb()

        # Get system memory info
        system_memory = None
        try:
            system_memory = psutil.virtual_memory()
        except Exception as e:
            logger.warning(f"Failed to get system memory info: {e}")

        # Log detailed memory usage information
        log_msg = (
            f"Memory check for cache '{self.name}': "
            f"cache_entries={len(self.cache)}, "
            f"cache_memory={cache_memory_mb:.2f}MB/{self.config.max_memory_mb:.2f}MB "
            f"({(cache_memory_mb / self.config.max_memory_mb * 100):.1f}%), "
            f"process_memory={process_memory_mb:.2f}MB"
        )

        if system_memory:
            log_msg += (
                f", system_memory={system_memory.percent:.1f}% "
                f"({system_memory.used / 1024 / 1024 / 1024:.2f}GB/{system_memory.total / 1024 / 1024 / 1024:.2f}GB)"
            )

        # Only log if memory logging is enabled in settings
        if env_settings.CACHE_ENABLE_MEMORY_LOGGING:
            logger.info(log_msg)

        # Check cache memory usage
        cache_threshold_mb = self.config.max_memory_mb * self.config.memory_threshold
        if cache_memory_mb > cache_threshold_mb:
            logger.warning(f"Cache '{self.name}' memory usage ({cache_memory_mb:.2f}MB) exceeds threshold ({cache_threshold_mb:.2f}MB)")
            return True

        # Check system memory usage
        if system_memory and system_memory.percent > env_settings.SYSTEM_MEMORY_THRESHOLD:
            logger.warning(f"System memory usage is high: {system_memory.percent:.1f}%")
            return True

        return False

    async def _evict_entries(self, count: int) -> int:
        """
        Evict entries based on the configured eviction policy.

        Args:
            count: Number of entries to evict

        Returns:
            Number of entries actually evicted
        """
        if not self.cache or count <= 0:
            return 0

        evicted = 0
        entries_to_remove = []

        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Evict least recently used entries
            sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].last_accessed)
            entries_to_remove = [key for key, _ in sorted_entries[:count]]

        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Evict least frequently used entries
            sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].access_count)
            entries_to_remove = [key for key, _ in sorted_entries[:count]]

        elif self.config.eviction_policy == EvictionPolicy.SIZE:
            # Evict largest entries first
            sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].size_bytes, reverse=True)
            entries_to_remove = [key for key, _ in sorted_entries[:count]]

        elif self.config.eviction_policy == EvictionPolicy.TTL:
            # Evict oldest entries first
            sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].created_at)
            entries_to_remove = [key for key, _ in sorted_entries[:count]]

        else:  # MEMORY_PRESSURE - hybrid approach
            # First evict expired entries, then LRU
            expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]

            entries_to_remove.extend(expired_keys[:count])
            remaining_count = count - len(entries_to_remove)

            if remaining_count > 0:
                # Then evict LRU entries
                non_expired = {k: v for k, v in self.cache.items() if k not in expired_keys}
                sorted_entries = sorted(non_expired.items(), key=lambda x: x[1].last_accessed)
                entries_to_remove.extend([key for key, _ in sorted_entries[:remaining_count]])

        # Remove selected entries
        for key in entries_to_remove:
            if key in self.cache:
                entry = self.cache[key]
                del self.cache[key]
                evicted += 1
                logger.debug(
                    f"Evicted entry '{key}' from cache '{self.name}' (size: {entry.size_bytes} bytes, age: {time.time() - entry.created_at:.1f}s)"
                )

        if evicted > 0:
            self.stats["evictions"] += evicted
            logger.info(f"Evicted {evicted} entries from cache '{self.name}'")

        return evicted

    async def _check_and_cleanup(self) -> None:
        """Check cache state and perform cleanup if necessary."""
        async with self.lock:
            await self._remove_expired_entries()

            # Check if cleanup is needed
            memory_pressure = await self._check_memory_pressure()
            entries_over_limit = len(self.cache) > self.config.max_entries

            if memory_pressure or entries_over_limit:
                self.stats["cleanups"] += 1
                if memory_pressure:
                    self.stats["memory_pressure_events"] += 1

                # Calculate how many entries to evict
                if entries_over_limit:
                    excess_entries = len(self.cache) - self.config.max_entries
                    evict_count = max(excess_entries, int(len(self.cache) * self.config.cleanup_ratio))
                else:
                    evict_count = int(len(self.cache) * self.config.cleanup_ratio)

                await self._evict_entries(evict_count)

                # Force garbage collection after cleanup
                gc.collect()

                # Log cleanup results
                cache_memory_mb = self._get_cache_memory_usage_mb()
                logger.info(f"Cleanup completed for cache '{self.name}': entries={len(self.cache)}, memory_usage={cache_memory_mb:.2f}MB")

    async def _remove_expired_entries(self) -> int:
        """Remove expired entries from cache."""
        if self.config.ttl_seconds is None:
            return 0

        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            self.stats["expired_entries"] += len(expired_keys)
            logger.debug(f"Removed {len(expired_keys)} expired entries from cache '{self.name}'")

        return len(expired_keys)

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        async with self.lock:
            if key not in self.cache:
                self.stats["misses"] += 1
                return None

            entry = self.cache[key]

            # Check if expired
            if entry.is_expired():
                del self.cache[key]
                self.stats["misses"] += 1
                self.stats["expired_entries"] += 1
                return None

            # Update access metadata
            entry.touch()

            # Move to end for LRU
            self.cache.move_to_end(key)

            self.stats["hits"] += 1
            return entry.value

    async def put(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """
        Put a value into the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (overrides default)
        """
        async with self.lock:
            # Calculate object size
            size_bytes = self._calculate_object_size(value)

            # Use provided TTL or default
            effective_ttl = ttl_seconds if ttl_seconds is not None else self.config.ttl_seconds

            # Create cache entry
            entry = CacheEntry(value=value, size_bytes=size_bytes, ttl_seconds=effective_ttl)

            # If key exists, remove old entry first
            if key in self.cache:
                old_entry = self.cache[key]
                logger.debug(f"Updating existing entry '{key}' in cache '{self.name}' (old_size: {old_entry.size_bytes}, new_size: {size_bytes})")

            # Add to cache
            self.cache[key] = entry
            self.cache.move_to_end(key)  # Mark as most recently used

            logger.debug(f"Added entry '{key}' to cache '{self.name}' (size: {size_bytes} bytes, ttl: {effective_ttl}s)")

            # Check if immediate cleanup is needed
            if len(self.cache) > self.config.max_entries or await self._check_memory_pressure():
                await self._check_and_cleanup()

    async def remove(self, key: str) -> bool:
        """
        Remove a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was found and removed, False otherwise
        """
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                del self.cache[key]
                logger.debug(f"Removed entry '{key}' from cache '{self.name}' (size: {entry.size_bytes} bytes)")
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        async with self.lock:
            entry_count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared {entry_count} entries from cache '{self.name}'")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self.lock:
            cache_memory_mb = self._get_cache_memory_usage_mb()
            system_memory_mb = self._get_current_memory_usage_mb()

            hit_rate = 0.0
            total_requests = self.stats["hits"] + self.stats["misses"]
            if total_requests > 0:
                hit_rate = self.stats["hits"] / total_requests

            return {
                "name": self.name,
                "entries_count": len(self.cache),
                "max_entries": self.config.max_entries,
                "cache_memory_mb": cache_memory_mb,
                "max_memory_mb": self.config.max_memory_mb,
                "system_memory_mb": system_memory_mb,
                "hit_rate": hit_rate,
                "total_hits": self.stats["hits"],
                "total_misses": self.stats["misses"],
                "total_evictions": self.stats["evictions"],
                "total_cleanups": self.stats["cleanups"],
                "memory_pressure_events": self.stats["memory_pressure_events"],
                "expired_entries": self.stats["expired_entries"],
                "eviction_policy": self.config.eviction_policy.value,
                "ttl_seconds": self.config.ttl_seconds,
            }

    async def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information."""
        async with self.lock:
            entries_by_size = sorted(self.cache.items(), key=lambda x: x[1].size_bytes, reverse=True)

            total_size = sum(entry.size_bytes for entry in self.cache.values())
            avg_size = total_size / len(self.cache) if self.cache else 0

            top_entries = []
            for key, entry in entries_by_size[:5]:  # Top 5 largest entries
                top_entries.append(
                    {
                        "key": key,
                        "size_mb": entry.size_bytes / 1024 / 1024,
                        "age_seconds": time.time() - entry.created_at,
                        "access_count": entry.access_count,
                    }
                )

            return {
                "cache_name": self.name,
                "total_entries": len(self.cache),
                "total_size_mb": total_size / 1024 / 1024,
                "average_size_mb": avg_size / 1024 / 1024,
                "largest_entries": top_entries,
                "system_memory_percent": psutil.virtual_memory().percent,
            }


class GlobalCacheManager:
    """Global manager for all memory-aware caches."""

    def __init__(self):
        """Initialize the global cache manager."""
        self.caches: Dict[str, MemoryCacheManager] = {}
        self.lock = asyncio.Lock()

        logger.info("Initialized GlobalCacheManager")

    async def create_cache(self, name: str, config: CacheConfig, start_background_cleanup: bool = True) -> MemoryCacheManager:
        """
        Create a new memory-aware cache.

        Args:
            name: Unique name for the cache
            config: Cache configuration
            start_background_cleanup: Whether to start background cleanup

        Returns:
            Created cache manager

        Raises:
            ValueError: If cache with same name already exists
        """
        async with self.lock:
            if name in self.caches:
                raise ValueError(f"Cache with name '{name}' already exists")

            cache = MemoryCacheManager(name, config)
            self.caches[name] = cache

            if start_background_cleanup:
                await cache.start_background_cleanup()

            logger.info(f"Created cache '{name}' with configuration: {config}")
            return cache

    async def get_cache(self, name: str) -> Optional[MemoryCacheManager]:
        """Get an existing cache by name."""
        async with self.lock:
            return self.caches.get(name)

    async def remove_cache(self, name: str) -> bool:
        """Remove a cache and stop its background tasks."""
        async with self.lock:
            if name not in self.caches:
                return False

            cache = self.caches[name]
            await cache.stop_background_cleanup()
            await cache.clear()
            del self.caches[name]

            logger.info(f"Removed cache '{name}'")
            return True

    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches."""
        async with self.lock:
            stats = {}
            for name, cache in self.caches.items():
                stats[name] = await cache.get_stats()
            return stats

    async def get_global_memory_info(self) -> Dict[str, Any]:
        """Get global memory information across all caches."""
        async with self.lock:
            total_entries = 0
            total_memory_mb = 0.0
            cache_info = []

            for name, cache in self.caches.items():
                stats = await cache.get_stats()
                cache_info.append(
                    {"name": name, "entries": stats["entries_count"], "memory_mb": stats["cache_memory_mb"], "hit_rate": stats["hit_rate"]}
                )
                total_entries += stats["entries_count"]
                total_memory_mb += stats["cache_memory_mb"]

            # System memory info
            system_memory = psutil.virtual_memory()
            process_memory = psutil.Process().memory_info()

            return {
                "total_caches": len(self.caches),
                "total_entries": total_entries,
                "total_cache_memory_mb": total_memory_mb,
                "system_memory_total_gb": system_memory.total / 1024 / 1024 / 1024,
                "system_memory_used_percent": system_memory.percent,
                "process_memory_mb": process_memory.rss / 1024 / 1024,
                "cache_details": cache_info,
            }

    async def cleanup_all_caches(self) -> None:
        """Force cleanup on all caches."""
        async with self.lock:
            for cache in self.caches.values():
                await cache._check_and_cleanup()

            # Force global garbage collection
            gc.collect()
            logger.info("Completed cleanup on all caches")

    async def shutdown(self) -> None:
        """Shutdown all caches and cleanup resources."""
        async with self.lock:
            for name, cache in list(self.caches.items()):
                await cache.stop_background_cleanup()
                await cache.clear()

            self.caches.clear()
            logger.info("Shutdown completed for all caches")


# Global instance
global_cache_manager = GlobalCacheManager()
