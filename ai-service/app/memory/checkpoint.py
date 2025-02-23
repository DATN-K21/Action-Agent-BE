from typing import Optional

from fastapi import HTTPException
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


class AsyncPostgresPool:
    _async_pool: Optional[AsyncConnectionPool] = None
    _is_initialized: bool = False

    @classmethod
    async def asetup(cls) -> None:
        """Asynchronously sets up the pool."""
        if cls._async_pool is None:
            try:
                cls._async_pool = AsyncConnectionPool(
                    conninfo=f"postgresql://{env_settings.POSTGRES_URL_PATH}",
                    kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
                    open=False,
                    timeout=5,
                )
                await cls._async_pool.open()
                logger.info(f"Async Postgres connection pool created at {env_settings.POSTGRES_URL_PATH}")
            except Exception as e:
                logger.exception("Error setting up the Postgres Saver")
                raise HTTPException(status_code=500, detail="Error setting up the Postgres Saver") from e

    @classmethod
    async def atear_down(cls) -> None:
        """Clean up resources when shutting down."""
        if cls._async_pool is not None:
            try:
                logger.info("Closing connection pool...")
                await cls._async_pool.close()
                cls._async_pool = None
                logger.info("Connection pool closed.")
            except Exception as e:
                logger.exception("Error during async checkpoint teardown")
                raise HTTPException(status_code=500, detail="Error during async checkpoint teardown") from e

    @classmethod
    async def get_checkpointer(cls) -> AsyncPostgresSaver:
        """Returns the singleton instance of the checkpoint."""
        checkpoint = AsyncPostgresSaver(cls._async_pool)  # type: ignore
        if not cls._is_initialized:
            await checkpoint.setup()
            cls._is_initialized = True
        return checkpoint
