"""
Memory monitoring API endpoints for cache management.

These endpoints provide real-time visibility into cache memory usage,
system performance, and memory pressure alerts.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.core import logging
from app.core.cache.memory_cache_manager import global_cache_manager
from app.core.cache.memory_monitor import global_memory_monitor

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["Memory Monitoring"])


@router.get("/caches", response_model=Dict[str, Any])
async def get_cache_statistics():
    """Get statistics for all active caches."""
    try:
        stats = await global_cache_manager.get_all_stats()
        return {"success": True, "data": stats, "total_caches": len(stats)}
    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")


@router.get("/global", response_model=Dict[str, Any])
async def get_global_memory_info():
    """Get comprehensive global memory information."""
    try:
        info = await global_cache_manager.get_global_memory_info()
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Failed to get global memory info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get global memory info: {str(e)}")


@router.get("/monitor", response_model=Dict[str, Any])
async def get_memory_monitor_report():
    """Get detailed memory monitoring report with alerts and trends."""
    try:
        report = await global_memory_monitor.get_memory_report()
        return {"success": True, "data": report}
    except Exception as e:
        logger.error(f"Failed to get memory monitor report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory monitor report: {str(e)}")


@router.get("/cache/{cache_name}", response_model=Dict[str, Any])
async def get_cache_details(cache_name: str):
    """Get detailed information about a specific cache."""
    try:
        cache = await global_cache_manager.get_cache(cache_name)
        if cache is None:
            raise HTTPException(status_code=404, detail=f"Cache '{cache_name}' not found")

        stats = await cache.get_stats()
        memory_info = await cache.get_memory_info()

        return {"success": True, "data": {"statistics": stats, "memory_info": memory_info}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cache details for '{cache_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache details: {str(e)}")


@router.post("/cleanup", response_model=Dict[str, Any])
async def trigger_cache_cleanup():
    """Manually trigger cleanup on all caches."""
    try:
        await global_cache_manager.cleanup_all_caches()
        return {"success": True, "message": "Cache cleanup triggered successfully"}
    except Exception as e:
        logger.error(f"Failed to trigger cache cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")


@router.post("/monitor/reset-alerts", response_model=Dict[str, Any])
async def reset_memory_alerts():
    """Reset all memory pressure alerts."""
    try:
        await global_memory_monitor.reset_alerts()
        return {"success": True, "message": "Memory alerts reset successfully"}
    except Exception as e:
        logger.error(f"Failed to reset memory alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset alerts: {str(e)}")


@router.delete("/cache/{cache_name}", response_model=Dict[str, Any])
async def remove_cache(cache_name: str):
    """Remove a specific cache and all its data."""
    try:
        success = await global_cache_manager.remove_cache(cache_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Cache '{cache_name}' not found")

        return {"success": True, "message": f"Cache '{cache_name}' removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove cache '{cache_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove cache: {str(e)}")
