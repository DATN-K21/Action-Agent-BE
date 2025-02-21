from typing import Optional

from fastapi import HTTPException
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

class AsyncPostgresCheckpoint:
    _instance: Optional[AsyncPostgresSaver] = None
    _async_pool: Optional[AsyncConnectionPool[AsyncConnection[DictRow]]] = None
    _initialized: bool = False

    @classmethod
    def get_instance(cls) -> AsyncPostgresSaver:
        """Returns the singleton instance of the checkpoint."""
        if cls._instance is None:
            try:
                if cls._async_pool is None:
                    cls._async_pool = AsyncConnectionPool(
                        conninfo=f"postgresql://{env_settings.POSTGRES_URL_PATH}",
                        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
                        open=True,
                        timeout=5,
                    )
                    logger.info("Async Postgres connection pool created.")
                cls._instance = AsyncPostgresSaver(cls._async_pool)
                logger.info("Async Postgres Saver instance created.")
            except Exception as e:
                logger.exception("Error setting up the Postgres Saver")
                raise HTTPException(status_code=500, detail="Error setting up the Postgres Saver") from e
        return cls._instance

    @classmethod
    async def setup_async(cls) -> None:
        """Asynchronously sets up the checkpoint."""
        if not cls._initialized:
            try:
                cls.get_instance()  # Ensure the instance is created
                if cls._async_pool is not None:
                    await cls._async_pool.open()
                    logger.info(f"Connection pool opened: {env_settings.POSTGRES_URL_PATH}")
                if cls._instance is not None:
                    result = await cls._instance.setup()
                    logger.info(f"Checkpoint setup completed: {result}")
                    cls._initialized = True
            except Exception as e:
                logger.exception("Error during async checkpoint setup")
                raise HTTPException(status_code=500, detail="Error during async checkpoint setup") from e

    @classmethod
    async def teardown_async(cls) -> None:
        """Clean up resources when shutting down."""
        if cls._initialized and cls._async_pool is not None:
            try:
                logger.info("Closing connection pool...")
                await cls._async_pool.close()
                cls._initialized = False
                cls._instance = None
                cls._async_pool = None
                logger.info("Connection pool closed.")
            except Exception as e:
                logger.exception("Error during async checkpoint teardown")
                raise HTTPException(status_code=500, detail="Error during async checkpoint teardown") from e


# Utility Dependencies
def get_checkpointer() -> AsyncPostgresSaver:
    """Get the checkpointer singleton."""
    return AsyncPostgresCheckpoint.get_instance()
