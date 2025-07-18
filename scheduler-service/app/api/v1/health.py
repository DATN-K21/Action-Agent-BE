from fastapi import APIRouter

from app.core.database import get_db_health
from app.core.scheduler import scheduler_manager
from app.schemas.base import MessageResponse, ResponseWrapper
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter()


@router.get("/", summary="Health Check")
async def health_check():
    """
    Health check endpoint for the scheduler service.
    """
    scheduler_running = scheduler_manager._running
    db_health = await get_db_health()
    
    overall_healthy = scheduler_running and db_health["status"] == "healthy"
    
    health_data = HealthResponse(
        status="healthy" if overall_healthy else "unhealthy",
        scheduler_running=scheduler_running,
        database_status=db_health["status"],
        message="All services are running" if overall_healthy else "Some services are not running properly"
    )
    
    return ResponseWrapper.wrap(
        status=200 if overall_healthy else 503,
        data=health_data,
        message="Health check completed"
    )


@router.get("/ping", summary="Ping")
async def ping():
    """
    Simple ping endpoint.
    """
    return ResponseWrapper.wrap(
        status=200,
        data=MessageResponse(message="pong"),
        message="Ping successful"
    )


@router.get("/database", summary="Database Health Check")
async def database_health():
    """
    Detailed database health check endpoint.
    """
    db_health = await get_db_health()
    
    health_data = DatabaseHealthResponse(
        status=db_health["status"],
        message=db_health.get("message"),
        connection_count=db_health.get("connection_count")
    )
    
    return ResponseWrapper.wrap(
        status=200 if db_health["status"] == "healthy" else 503,
        data=health_data,
        message="Database health check completed"
    )
