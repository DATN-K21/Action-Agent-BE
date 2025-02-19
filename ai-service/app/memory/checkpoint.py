from typing import Optional

from fastapi import HTTPException
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

# Utility Dependencies
def get_checkpointer():
    """Get the checkpointer singleton."""
    return AsyncPostgresCheckpoint.get_instance()

class AsyncPostgresCheckpoint:
    _instance: Optional[AsyncPostgresSaver] = None
    _initialized: bool = False

    @classmethod
    def get_instance(cls) -> AsyncPostgresSaver:
        """Returns the instance of the checkpoint."""
        try:
            if cls._instance is None:
                connection_info = f"postgresql://{env_settings.POSTGRES_URL_PATH}"
                # Create pool without auto-opening
                cls._async_pool = AsyncConnectionPool(
                    conninfo=connection_info,
                    kwargs={"autocommit": True, "prepare_threshold": 0},
                    open=False,  # Disable auto-open
                    timeout=5,
                )
                cls._instance = AsyncPostgresSaver(cls._async_pool)  # type: ignore
        except Exception as e:
            logger.error(f"Error setting up the Postgres Saver: {e}")
            raise HTTPException(status_code=500, detail="Error setting up the Postgres Saver")

        return cls._instance

    @classmethod
    async def setup_async(cls) -> None:
        """Asynchronously sets up the checkpoint."""
        cls.get_instance()  # Ensure the instance is created
        if not cls._initialized:
            # Explicitly open the connection pool
            await cls._async_pool.open()
            logger.info(f"Connection pool opened: {cls._async_pool.conninfo}")

            # Proceed with instance setup
            if cls._instance is not None:
                result = await cls._instance.setup()
                logger.info(f"Checkpoint setup completed: {result}")
                cls._initialized = True
            else:
                logger.error("Error setting up the Postgres Saver")
                raise HTTPException(status_code=500, detail="Error setting up the Postgres Saver")

    @classmethod
    async def teardown_async(cls) -> None:
        """Clean up resources when shutting down"""
        if cls._initialized:
            logger.info("Closing connection pool...")
            await cls._async_pool.close()
            cls._initialized = False
            cls._instance = None
            logger.info("Connection pool closed")
