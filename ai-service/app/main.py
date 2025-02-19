from fastapi import FastAPI

from app.api.v1 import router
from app.core.life_span import lifespan
from app.core.settings import env_settings

app = FastAPI(
    debug=env_settings.DEBUG,
    title="Action-Executing AI Service API",
    description="This is a AI Service API using FastAPI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.include_router(router)
