import socket
from contextlib import asynccontextmanager

import urllib3.util.connection as urllib3_conn
from fastapi import FastAPI

from app.api.v1 import router
from app.core import logging
from app.core.settings import env_settings
from app.memory.checkpoint import AsyncPostgresCheckpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logging.configure_logging()
        # Force IPv4: increase the speed when fetching data from Composio server
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
        await AsyncPostgresCheckpoint.setup_async()
        yield
    finally:
        await AsyncPostgresCheckpoint.teardown_async()


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
