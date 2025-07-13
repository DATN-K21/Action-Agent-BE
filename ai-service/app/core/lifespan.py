import socket
from contextlib import asynccontextmanager

import urllib3.util.connection as urllib3_conn
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core import logging
from app.core.cache.memory_cache_manager import global_cache_manager
from app.core.db_session import async_engine
from app.core.settings import env_settings
from app.db_models import Base
from app.memory.checkpoint import AsyncPostgresPool

logger = logging.get_logger(__name__)


# =============================================================================
# Lifespan event handler for FastAPI
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Force IPv4: increase the speed when fetching data from Composio server
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET

        # Setup database, PostgreSQL connection pool
        await _setup_database()
        await AsyncPostgresPool.asetup()

        # Manually resolve dependencies at startup
        # checkpointer = await get_checkpointer()

        yield
    finally:
        # Shutdown cache manager first to cleanup all caches
        await global_cache_manager.shutdown()

        # Then shutdown database connections
        await AsyncPostgresPool.atear_down()


# =============================================================================
# Private Helper Methods
# =============================================================================
async def _setup_database():
    """Setup database schema and tables."""
    await _create_database_schema()
    await _create_database_tables()
    logger.info(f"Database schema/tables created/verified. Schema = {env_settings.POSTGRES_SCHEMA}")


async def _create_database_schema():
    """Create the database schema if it doesn't exist."""
    temp_async_engine = create_async_engine(
        f"postgresql+asyncpg://{env_settings.POSTGRES_URL_PATH}",
        pool_pre_ping=True,
        echo=env_settings.DEBUG_SQLALCHEMY,
    )
    try:
        async with temp_async_engine.begin() as conn:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {env_settings.POSTGRES_SCHEMA}"))

    finally:
        await temp_async_engine.dispose()


async def _create_database_tables():
    """Create database tables using SQLAlchemy."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
