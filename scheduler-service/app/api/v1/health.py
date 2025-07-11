from fastapi import APIRouter
from pydantic import BaseModel

from app.core.database import get_db_health
from app.core.scheduler import scheduler_manager

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    scheduler_running: bool
    database_status: str
    message: str


@router.get("/", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """
    Health check endpoint for the scheduler service.
    """
    scheduler_running = scheduler_manager._running
    db_health = await get_db_health()
    
    overall_healthy = scheduler_running and db_health["status"] == "healthy"
    
    return HealthResponse(
        status="healthy" if overall_healthy else "unhealthy",
        scheduler_running=scheduler_running,
        database_status=db_health["status"],
        message="All services are running" if overall_healthy else "Some services are not running properly"
    )


@router.get("/ping", summary="Ping")
async def ping():
    """
    Simple ping endpoint.
    """
    return {"message": "pong"}


@router.get("/database", summary="Database Health Check")
async def database_health():
    """
    Detailed database health check endpoint.
    """
    return await get_db_health()
