"""
gRPC connection pool management for efficient resource handling.

This module provides a singleton connection pool for gRPC channels to improve
performance and resource management across the application.
"""

import asyncio
import threading
import time
from typing import Any, Dict, List, Optional

import grpc
import grpc.aio

from app.core import logging

logger = logging.get_logger(__name__)


class GRPCConnectionPool:
    """Singleton connection pool for gRPC channels to improve performance and resource management."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_channels: int = 10, channel_ttl: float = 300.0):
        """Initialize the connection pool.

        Args:
            max_channels: Maximum number of channels to maintain in the pool
            channel_ttl: Time-to-live for channels in seconds
        """
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        self.max_channels = max_channels
        self.channel_ttl = channel_ttl
        self._channels: Dict[str, Dict[str, Any]] = {}
        self._async_lock = asyncio.Lock()
        self._cleanup_task = None
        self._initialized = True

        logger.info(f"Initialized gRPC connection pool with max_channels={max_channels}, ttl={channel_ttl}s")

    async def get_channel(self, target: str, options: Optional[List] = None) -> grpc.aio.Channel:
        """Get or create a gRPC channel.

        Args:
            target: gRPC target URL
            options: gRPC channel options

        Returns:
            gRPC async channel
        """
        # Create a key based on target and options
        options_key = str(sorted(options or []))
        channel_key = f"{target}:{hash(options_key)}"

        async with self._async_lock:
            # Check if we have a valid channel
            if channel_key in self._channels:
                channel_info = self._channels[channel_key]
                channel = channel_info["channel"]

                # Check if channel is still valid
                if channel.get_state() != grpc.ChannelConnectivity.SHUTDOWN and time.time() - channel_info["created_at"] < self.channel_ttl:
                    channel_info["last_used"] = time.time()
                    channel_info["use_count"] += 1
                    logger.debug(f"Reusing gRPC channel for {target} (uses: {channel_info['use_count']})")
                    return channel
                else:
                    # Channel is invalid, remove it
                    await self._remove_channel(channel_key)

            # Create new channel
            return await self._create_channel(target, options, channel_key)

    async def _create_channel(self, target: str, options: Optional[List], channel_key: str) -> grpc.aio.Channel:
        """Create a new gRPC channel and add it to the pool."""
        # Clean up old channels if pool is full
        if len(self._channels) >= self.max_channels:
            await self._cleanup_oldest_channel()

        # Create new channel
        channel = grpc.aio.insecure_channel(target, options=options or [])

        # Store in pool
        self._channels[channel_key] = {
            "channel": channel,
            "target": target,
            "options": options or [],
            "created_at": time.time(),
            "last_used": time.time(),
            "use_count": 1,
        }

        # Start cleanup task if not already running
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        logger.debug(f"Created new gRPC channel for {target} (pool size: {len(self._channels)})")
        return channel

    async def _remove_channel(self, channel_key: str):
        """Remove and close a channel from the pool."""
        if channel_key in self._channels:
            channel_info = self._channels[channel_key]
            channel = channel_info["channel"]

            try:
                await channel.close()
            except Exception as e:
                logger.warning(f"Error closing gRPC channel: {e}")

            del self._channels[channel_key]
            logger.debug(f"Removed gRPC channel {channel_key} from pool")

    async def _cleanup_oldest_channel(self):
        """Remove the oldest channel from the pool."""
        if not self._channels:
            return

        # Find the channel with the oldest last_used time
        oldest_key = min(self._channels.keys(), key=lambda k: self._channels[k]["last_used"])
        await self._remove_channel(oldest_key)

    async def _periodic_cleanup(self):
        """Periodically clean up expired channels."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                async with self._async_lock:
                    current_time = time.time()
                    expired_keys = []

                    for key, channel_info in self._channels.items():
                        if current_time - channel_info["last_used"] > self.channel_ttl:
                            expired_keys.append(key)

                    for key in expired_keys:
                        await self._remove_channel(key)

                    if expired_keys:
                        logger.debug(f"Cleaned up {len(expired_keys)} expired gRPC channels")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in gRPC channel cleanup: {e}")

    async def close_all(self):
        """Close all channels in the pool."""
        async with self._async_lock:
            # Cancel cleanup task
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

            # Close all channels
            for channel_key in list(self._channels.keys()):
                await self._remove_channel(channel_key)

            logger.info("Closed all gRPC channels in pool")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the connection pool."""
        active_channels = len(self._channels)
        channel_details = []

        for key, info in self._channels.items():
            channel_details.append(
                {
                    "target": info["target"],
                    "created_at": info["created_at"],
                    "last_used": info["last_used"],
                    "use_count": info["use_count"],
                    "age_seconds": time.time() - info["created_at"],
                }
            )

        return {"active_channels": active_channels, "max_channels": self.max_channels, "channel_ttl": self.channel_ttl, "channels": channel_details}


# Singleton instance
_connection_pool = GRPCConnectionPool()


async def get_grpc_channel(target: str, options: Optional[List] = None) -> grpc.aio.Channel:
    """Get a gRPC channel from the singleton connection pool.

    Args:
        target: gRPC target URL
        options: gRPC channel options

    Returns:
        gRPC async channel
    """
    return await _connection_pool.get_channel(target, options)


async def close_grpc_connections():
    """Close all gRPC connections in the pool."""
    await _connection_pool.close_all()


def get_grpc_pool_stats() -> Dict[str, Any]:
    """Get statistics about the gRPC connection pool.

    Returns:
        Dictionary with pool statistics
    """
    return _connection_pool.get_stats()


def configure_grpc_pool(max_channels: int = 10, channel_ttl: float = 300.0):
    """Configure the gRPC connection pool parameters.

    Args:
        max_channels: Maximum number of channels to maintain
        channel_ttl: Time-to-live for channels in seconds

    Note:
        This only affects the configuration if called before first use.
    """
    global _connection_pool
    if not hasattr(_connection_pool, "_initialized"):
        _connection_pool = GRPCConnectionPool(max_channels, channel_ttl)
    else:
        logger.warning("gRPC pool already initialized, configuration not applied")
