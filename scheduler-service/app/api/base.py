from fastapi import APIRouter

from app.api.v1.jobs import router as jobs_router
from app.api.v1.health import router as health_router
from app.core.settings import env_settings

# Create main API router
api_router = APIRouter()

# Include routers
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])

# Create versioned router
router = APIRouter()
router.include_router(api_router, prefix=env_settings.API_V1_PREFIX)
