import socket
from contextlib import asynccontextmanager

import urllib3.util.connection as urllib3_conn
from fastapi import FastAPI

from app.core import logging
from app.core.db_session import async_engine
from app.db_models import Base
from app.memory.checkpoint import AsyncPostgresPool

logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Force IPv4: increase the speed when fetching data from Composio server
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET

        # Manually set up the PostgreSQL connection pool
        await AsyncPostgresPool.asetup()

        # Create database tables using SQLAlchemy
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/updated")

        # Manually resolve dependencies at startup
        # checkpointer = await get_checkpointer()

        yield
    finally:
        await AsyncPostgresPool.atear_down()
