from typing import Optional

from fastapi import HTTPException
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from app.core import logging
from app.core.settings import env_settings

Conn = AsyncConnection[DictRow] | AsyncConnectionPool[AsyncConnection[DictRow]]

logger = logging.get_logger(__name__)


class AsyncPostgresPool:
    _async_pool: Optional[Conn] = None
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
                logger.info("Connection pool set up successfully")
            except Exception as e:
                logger.exception("Error setting up connection pool: %s", e)
                raise HTTPException(status_code=500, detail="Error setting up connection pool") from e

    @classmethod
    async def atear_down(cls) -> None:
        """
        Clean up resources when shutting down.
        """
        if cls._async_pool is not None:
            try:
                await cls._async_pool.close()
                cls._async_pool = None
                logger.info("Connection pool torn down successfully")
            except Exception as e:
                logger.exception("Error tearing down connection pool: %s", e)
                raise HTTPException(status_code=500, detail="Error tearing down connection pool") from e

    @classmethod
    async def get_checkpointer(cls) -> AsyncPostgresSaver:
        """
        Returns the singleton instance of the checkpoint.
        """
        if cls._async_pool is None:
            raise HTTPException(status_code=500, detail="Connection pool not set up. Please call asetup() first.")
        checkpoint = AsyncPostgresSaver(cls._async_pool)
        if not cls._is_initialized:
            await checkpoint.setup()
            cls._is_initialized = True
        return checkpoint


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get the checkpointer singleton.
    """
    return await AsyncPostgresPool.get_checkpointer()