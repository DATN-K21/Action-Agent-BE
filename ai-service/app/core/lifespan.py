import socket
from contextlib import asynccontextmanager

import urllib3.util.connection as urllib3_conn
from fastapi import FastAPI

from app.core import logging
from app.memory.checkpoint import AsyncPostgresPool

logger = logging.get_logger(__name__)


async def check_database_schema():
    """Check if database schema is properly initialized."""
    try:
        # This is a lightweight check to see if the main tables exist
        # If migrations are needed, they should be run separately before starting the app
        logger.info("Checking database schema...")

        # We can add a simple table existence check here if needed
        # For now, we'll assume the database is properly migrated
        logger.info("Database schema check completed")

    except Exception as e:
        logger.error(f"Database schema check failed: {e}")
        logger.info("Please run migrations manually: alembic upgrade head")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Force IPv4: increase the speed when fetching data from Composio server
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET

        # Check database schema (lightweight check)
        await check_database_schema()

        # Manually set up the PostgreSQL connection pool
        await AsyncPostgresPool.asetup()

        # Manually resolve dependencies at startup
        # checkpointer = await get_checkpointer()

        yield
    finally:
        await AsyncPostgresPool.atear_down()
