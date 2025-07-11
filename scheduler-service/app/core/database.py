from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core import logging
from app.core.settings import env_settings
from app.models.base import Base

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
    """Get async database session with proper error handling and cleanup."""
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
    """Get sync database session with proper error handling and cleanup."""
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


async def init_db():
    """Initialize database tables and schema."""
    logger.info("Initializing database...")
    
    try:
        async with async_engine.begin() as conn:
            # Create the scheduler schema if it doesn't exist
            logger.info(f"Creating schema '{env_settings.POSTGRES_SCHEMA}' if not exists...")
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {env_settings.POSTGRES_SCHEMA}"))
            
            # Create all tables defined in models
            logger.info("Creating application tables...")
            await conn.run_sync(Base.metadata.create_all)
            
            # Create APScheduler tables for SQLAlchemy job store
            # These tables will be created automatically by APScheduler when needed
            logger.info("APScheduler tables will be created automatically when scheduler starts")
            
            logger.info("Database initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def create_scheduler_schema():
    """Create scheduler schema in the database."""
    try:
        logger.info(f"Ensuring schema '{env_settings.POSTGRES_SCHEMA}' exists...")
        async with async_engine.begin() as conn:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {env_settings.POSTGRES_SCHEMA}"))
            logger.info(f"Schema '{env_settings.POSTGRES_SCHEMA}' created or already exists")
    except Exception as e:
        logger.error(f"Failed to create schema '{env_settings.POSTGRES_SCHEMA}': {e}")
        raise


async def close_db_connections():
    """Close all database connections and cleanup resources."""
    try:
        logger.info("Closing database connections...")
        
        # Dispose async engine
        await async_engine.dispose()
        logger.info("Async database engine disposed")
        
        # Dispose sync engine
        sync_engine.dispose()
        logger.info("Sync database engine disposed")
        
        logger.info("All database connections closed successfully")
        
    except Exception as e:
        # Log error but don't raise to avoid breaking shutdown process
        logger.error(f"Error during database cleanup: {e}")


async def get_db_health() -> dict:
    """Check database connection health."""
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
