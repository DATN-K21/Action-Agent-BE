"""
Test configuration and fixtures for the AI service tests.
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db_models.base_entity import Base
from app.db_models.user import User
from app.db_models.user_api_key import UserApiKey
from app.main import app

# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    """Create async database engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    async_session_maker = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client() -> TestClient:
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_user() -> User:
    """Create sample user for testing."""
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        language="en-US",
        default_api_key_id=None,
        remain_trial_tokens=1000,
        created_at=datetime.utcnow(),
        created_by="system",
        is_deleted=False,
    )


@pytest.fixture
def sample_api_key() -> UserApiKey:
    """Create sample API key for testing."""
    return UserApiKey(
        id="api-key-123",
        user_id="user-123",
        provider="openai",
        encrypted_value="encrypted_api_key_value",
        created_at=datetime.utcnow(),
        created_by="user-123",
        is_deleted=False,
    )


@pytest.fixture
def sample_user_with_default_key() -> User:
    """Create sample user with default API key for testing."""
    return User(
        id="user-456",
        username="testuser2",
        email="test2@example.com",
        first_name="Test",
        last_name="User2",
        language="en-US",
        default_api_key_id="api-key-456",
        remain_trial_tokens=500,
        created_at=datetime.utcnow(),
        created_by="system",
        is_deleted=False,
    )
