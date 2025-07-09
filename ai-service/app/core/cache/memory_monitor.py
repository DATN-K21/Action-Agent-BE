"""
Memory monitoring utilities for cache management.

This module provides detailed memory monitoring and logging capabilities
for tracking cache memory usage, system memory pressure, and performance metrics.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict

import psutil

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a specific time."""

    timestamp: float
    cache_name: str
    cache_entries: int
    cache_memory_mb: float
    cache_memory_percent: float
    process_memory_mb: float
    system_memory_percent: float
    system_memory_used_gb: float
    system_memory_total_gb: float

    @classmethod
    def create(
        cls, cache_name: str, cache_entries: int, cache_memory_mb: float, max_cache_memory_mb: float, process_memory_mb: float
    ) -> "MemorySnapshot":
        """Create a memory snapshot with current system information."""
        system_memory = psutil.virtual_memory()

        return cls(
            timestamp=time.time(),
            cache_name=cache_name,
            cache_entries=cache_entries,
            cache_memory_mb=cache_memory_mb,
            cache_memory_percent=(cache_memory_mb / max_cache_memory_mb * 100) if max_cache_memory_mb > 0 else 0,
            process_memory_mb=process_memory_mb,
            system_memory_percent=system_memory.percent,
            system_memory_used_gb=system_memory.used / 1024 / 1024 / 1024,
            system_memory_total_gb=system_memory.total / 1024 / 1024 / 1024,
        )


class MemoryMonitor:
    """
    Advanced memory monitoring for cache systems.

    Provides detailed logging, alerting, and memory pressure detection
    with configurable thresholds and reporting intervals.
    """

    def __init__(self, name: str = "MemoryMonitor"):
        """Initialize the memory monitor."""
        self.name = name
        self.snapshots: Dict[str, MemorySnapshot] = {}  # Latest snapshot per cache
        self.lock = asyncio.Lock()

        # Configuration from environment settings
        self.enable_logging = env_settings.CACHE_ENABLE_MEMORY_LOGGING
        self.system_memory_threshold = env_settings.SYSTEM_MEMORY_THRESHOLD
        self.detailed_logging_interval = env_settings.CACHE_DETAILED_LOGGING_INTERVAL

        # Internal state
        self.last_detailed_log = 0.0
        self.high_memory_alerts_sent = set()  # Track which caches have sent alerts

    async def log_memory_check(
        self, cache_name: str, cache_entries: int, cache_memory_mb: float, max_cache_memory_mb: float, process_memory_mb: float
    ) -> MemorySnapshot:
        """
        Log memory check information and return a snapshot.

        Args:
            cache_name: Name of the cache being monitored
            cache_entries: Number of entries in cache
            cache_memory_mb: Current cache memory usage in MB
            max_cache_memory_mb: Maximum allowed cache memory in MB
            process_memory_mb: Current process memory usage in MB

        Returns:
            MemorySnapshot of current state
        """
        async with self.lock:
            # Create memory snapshot
            snapshot = MemorySnapshot.create(
                cache_name=cache_name,
                cache_entries=cache_entries,
                cache_memory_mb=cache_memory_mb,
                max_cache_memory_mb=max_cache_memory_mb,
                process_memory_mb=process_memory_mb,
            )

            # Store latest snapshot for this cache
            self.snapshots[cache_name] = snapshot

            # Always log basic info if logging is enabled
            if self.enable_logging:
                self._log_basic_memory_info(snapshot)

            # Log detailed info periodically
            current_time = time.time()
            if current_time - self.last_detailed_log > self.detailed_logging_interval:
                await self._log_detailed_memory_info()
                self.last_detailed_log = current_time

            # Check for memory pressure and alerts
            await self._check_memory_alerts(snapshot)

            return snapshot

    def _log_basic_memory_info(self, snapshot: MemorySnapshot) -> None:
        """Log basic memory information."""
        log_msg = (
            f"Memory check for cache '{snapshot.cache_name}': "
            f"entries={snapshot.cache_entries}, "
            f"cache_memory={snapshot.cache_memory_mb:.2f}MB "
            f"({snapshot.cache_memory_percent:.1f}%), "
            f"process_memory={snapshot.process_memory_mb:.2f}MB, "
            f"system_memory={snapshot.system_memory_percent:.1f}% "
            f"({snapshot.system_memory_used_gb:.2f}GB/{snapshot.system_memory_total_gb:.2f}GB)"
        )

        logger.info(log_msg)

    async def _log_detailed_memory_info(self) -> None:
        """Log detailed memory information across all monitored caches."""
        if not self.snapshots:
            return

        total_cache_memory = sum(s.cache_memory_mb for s in self.snapshots.values())
        total_entries = sum(s.cache_entries for s in self.snapshots.values())

        # Log summary
        logger.info(f"=== Detailed Memory Report ({len(self.snapshots)} caches) ===")
        logger.info(f"Total cache memory: {total_cache_memory:.2f}MB across {total_entries} entries")

        # Log per-cache details
        for cache_name, snapshot in sorted(self.snapshots.items()):
            logger.info(f"  {cache_name}: {snapshot.cache_entries} entries, {snapshot.cache_memory_mb:.2f}MB ({snapshot.cache_memory_percent:.1f}%)")

        # Log system info
        if self.snapshots:
            latest_snapshot = next(iter(self.snapshots.values()))
            logger.info(
                f"System: {latest_snapshot.system_memory_percent:.1f}% used "
                f"({latest_snapshot.system_memory_used_gb:.2f}GB/"
                f"{latest_snapshot.system_memory_total_gb:.2f}GB), "
                f"Process: {latest_snapshot.process_memory_mb:.2f}MB"
            )

        logger.info("=== End Memory Report ===")

    async def _check_memory_alerts(self, snapshot: MemorySnapshot) -> None:
        """Check for memory pressure and send alerts if needed."""
        cache_name = snapshot.cache_name

        # Check cache memory threshold (warning at 80%, critical at 90%)
        if snapshot.cache_memory_percent > 90:
            if f"{cache_name}_critical" not in self.high_memory_alerts_sent:
                logger.critical(
                    f"CRITICAL: Cache '{cache_name}' memory usage is very high: "
                    f"{snapshot.cache_memory_percent:.1f}% ({snapshot.cache_memory_mb:.2f}MB)"
                )
                self.high_memory_alerts_sent.add(f"{cache_name}_critical")
        elif snapshot.cache_memory_percent > 80:
            if f"{cache_name}_warning" not in self.high_memory_alerts_sent:
                logger.warning(
                    f"WARNING: Cache '{cache_name}' memory usage is high: {snapshot.cache_memory_percent:.1f}% ({snapshot.cache_memory_mb:.2f}MB)"
                )
                self.high_memory_alerts_sent.add(f"{cache_name}_warning")
        else:
            # Clear alerts when memory usage drops
            self.high_memory_alerts_sent.discard(f"{cache_name}_warning")
            self.high_memory_alerts_sent.discard(f"{cache_name}_critical")

        # Check system memory threshold
        if snapshot.system_memory_percent > self.system_memory_threshold:
            if "system_memory" not in self.high_memory_alerts_sent:
                logger.warning(
                    f"WARNING: System memory usage is high: {snapshot.system_memory_percent:.1f}% (threshold: {self.system_memory_threshold:.1f}%)"
                )
                self.high_memory_alerts_sent.add("system_memory")
        else:
            self.high_memory_alerts_sent.discard("system_memory")

    async def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report for all monitored caches."""
        async with self.lock:
            if not self.snapshots:
                return {"error": "No memory snapshots available"}

            # Aggregate statistics
            total_cache_memory = sum(s.cache_memory_mb for s in self.snapshots.values())
            total_entries = sum(s.cache_entries for s in self.snapshots.values())
            avg_cache_utilization = sum(s.cache_memory_percent for s in self.snapshots.values()) / len(self.snapshots)

            # Get latest system info
            latest_snapshot = max(self.snapshots.values(), key=lambda s: s.timestamp)

            cache_details = []
            for cache_name, snapshot in sorted(self.snapshots.items()):
                cache_details.append(
                    {
                        "name": cache_name,
                        "entries": snapshot.cache_entries,
                        "memory_mb": snapshot.cache_memory_mb,
                        "memory_percent": snapshot.cache_memory_percent,
                        "age_seconds": time.time() - snapshot.timestamp,
                    }
                )

            return {
                "monitor_name": self.name,
                "total_caches": len(self.snapshots),
                "total_entries": total_entries,
                "total_cache_memory_mb": total_cache_memory,
                "average_cache_utilization_percent": avg_cache_utilization,
                "system_memory_percent": latest_snapshot.system_memory_percent,
                "system_memory_used_gb": latest_snapshot.system_memory_used_gb,
                "system_memory_total_gb": latest_snapshot.system_memory_total_gb,
                "process_memory_mb": latest_snapshot.process_memory_mb,
                "active_alerts": list(self.high_memory_alerts_sent),
                "cache_details": cache_details,
                "last_detailed_log": self.last_detailed_log,
                "logging_enabled": self.enable_logging,
            }

    async def clear_cache_snapshot(self, cache_name: str) -> bool:
        """Clear snapshot for a specific cache (e.g., when cache is removed)."""
        async with self.lock:
            if cache_name in self.snapshots:
                del self.snapshots[cache_name]
                # Clear any alerts for this cache
                self.high_memory_alerts_sent.discard(f"{cache_name}_warning")
                self.high_memory_alerts_sent.discard(f"{cache_name}_critical")
                logger.debug(f"Cleared memory snapshot for cache '{cache_name}'")
                return True
            return False

    async def reset_alerts(self) -> None:
        """Reset all memory alerts (useful for testing or after resolving issues)."""
        async with self.lock:
            alert_count = len(self.high_memory_alerts_sent)
            self.high_memory_alerts_sent.clear()
            logger.info(f"Reset {alert_count} memory alerts")


# Global memory monitor instance
global_memory_monitor = MemoryMonitor("GlobalMemoryMonitor")
