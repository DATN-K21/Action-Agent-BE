import os
import logging
from typing import Optional
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AsyncPostgresCheckpoint:
    _instance: Optional[AsyncPostgresSaver] = None
    _initialized: bool = False

    @classmethod
    def get_instance(cls) -> AsyncPostgresSaver:
        """Returns the instance of the checkpoint."""
        try:
            if cls._instance is None:
                connection_info = (
                    f"postgresql://{os.environ['POSTGRES_USER']}:"
                    f"{os.environ['POSTGRES_PASSWORD']}@"
                    f"{os.environ['POSTGRES_HOST']}:"
                    f"{os.environ['POSTGRES_PORT']}/"
                    f"{os.environ['POSTGRES_DB']}"
                )
                cls._async_pool = AsyncConnectionPool(
                    conninfo=connection_info,
                    kwargs={"autocommit": True, "prepare_threshold": 0},
                )
                cls._instance = AsyncPostgresSaver(cls._async_pool)
        except Exception as e:
            logger.error(f"Error setting up the Postgres Saver: {e}")
            raise HTTPException(status_code=500, detail=f"Error setting up the Postgres Saver")

        return cls._instance


    @classmethod
    async def setup_async(cls) -> None:
        """Asynchronously sets up the checkpoint."""
        cls.get_instance()  # Ensure the instance is created
        if not cls._initialized:
            logger.log(level=logging.INFO,msg="Setting up the checkpoint asynchronously...")
            await cls._instance.setup()
            logger.log(level=logging.INFO,msg="Checkpoint setup complete.")
            cls._initialized = True

