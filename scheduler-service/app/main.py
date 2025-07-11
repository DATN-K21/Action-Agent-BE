from app.core import logging

logging.configure_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.base import router
from app.core.lifespan import lifespan
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

app = FastAPI(
    title="Scheduler Service API",
    description="Job scheduling service for the Action-Executing AI Agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=env_settings.HOST,
        port=env_settings.PORT,
        reload=env_settings.DEBUG_SERVER,
    )
