import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core import logging as custom_logging
from app.core.settings import env_settings

logger = logging.getLogger(__name__)


async def create_database_schema():
    """Create the database schema if it doesn't exist."""
    try:
        # Build the connection URL properly
        db_url = f"postgresql+asyncpg://{env_settings.PGVECTOR_POSTGRES_URL_PATH}"

        # Create engine without the problematic options parameter for asyncpg
        temp_async_engine = create_async_engine(
            db_url,
            echo=env_settings.DEBUG_MODE,
            pool_pre_ping=True,
        )

        async with temp_async_engine.begin() as conn:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {env_settings.PGVECTOR_POSTGRES_SCHEMA}"))
            logger.info(f"Schema '{env_settings.PGVECTOR_POSTGRES_SCHEMA}' created/verified")
    except Exception as e:
        logger.warning(f"Could not create database schema: {e}")
        logger.info("Database schema creation skipped - will be created on first use")
    finally:
        try:
            await temp_async_engine.dispose()
        except Exception:
            pass


def initialize_service():
    """Initialize the service by setting up logging and database."""
    custom_logging.configure_logging()
    logger.info("Ingest Service (Celery Worker) starting up...")

    # Try to create database schema, but don't fail if it doesn't work
    try:
        asyncio.run(create_database_schema())
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.info("Continuing without database schema creation...")

    # Return success indicator
    return True
