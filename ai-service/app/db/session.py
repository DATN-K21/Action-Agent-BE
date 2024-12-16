import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


# Create an async engine with SQLAlchemy's async support
DATABASE_URL = (f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
                f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}")
print(DATABASE_URL)
engine = create_async_engine(DATABASE_URL, echo=True)

# Create an AsyncSessionLocal class (session factory)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Dependency function to get a database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session  # This will yield the session to the route function
        await session.commit()  # Commit any changes if necessary (on successful request)

