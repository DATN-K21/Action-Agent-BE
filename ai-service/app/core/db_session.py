from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

ASYNC_URL = f"postgresql+asyncpg://{env_settings.POSTGRES_URL_PATH}"
SYNC_URL = f"postgresql+psycopg2://{env_settings.POSTGRES_URL_PATH}"

async_engine = create_async_engine(
    ASYNC_URL,
    pool_pre_ping=True,
    echo=env_settings.DEBUG_SQLALCHEMY,
    connect_args={"server_settings": {"search_path": env_settings.POSTGRES_SCHEMA}},
    pool_size=10,  # Limit connection pool size
    max_overflow=20,  # Maximum overflow connections
    pool_recycle=3600,  # Recycle connections every hour
    pool_timeout=30,  # Connection timeout
)
sync_engine = create_engine(
    SYNC_URL,
    pool_pre_ping=True,
    echo=env_settings.DEBUG_SQLALCHEMY,
    connect_args={"options": f"-csearch_path={env_settings.POSTGRES_SCHEMA}"},
    pool_size=5,  # Smaller pool for sync operations
    max_overflow=10,
    pool_recycle=3600,
    pool_timeout=30,
)

AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False, autoflush=False, autocommit=False)
SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False, autoflush=False, autocommit=False)

# --- FastAPI dependencies ---------------------------------------------------


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except SQLAlchemyError:
            logger.exception("Async DB error")
            await db.rollback()
            raise
        finally:
            # Explicitly close the session to ensure cleanup
            await db.close()


def get_sync_session() -> Generator[Session, None, None]:
    db: Session = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        logger.exception("Sync DB error")
        db.rollback()
        raise
    finally:
        db.close()
