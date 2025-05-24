from typing import AsyncGenerator

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

# Create async engine (Lazy connection pooling)
DATABASE_URL = f"postgresql+asyncpg://{env_settings.POSTGRES_URL_PATH}"
engine = create_async_engine(DATABASE_URL, echo=env_settings.DEBUG_SQLALCHEMY)

# Create session factory
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=True)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda connection: None)  # Test connection
            yield session
        except (IntegrityError, OperationalError, SQLAlchemyError) as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
