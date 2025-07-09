"""
Unit tests for callback API endpoints.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.enums import ConnectionStatus
from app.db_models.connected_extension import ConnectedExtension
from app.main import app


class TestCallbackApiEndpoints:
    """Test class for callback API endpoints."""

    @pytest.fixture
    def sample_user_id(self) -> str:
        """Generate sample user ID."""
        return "user-123"

    @pytest.fixture
    def sample_connected_extension_id(self) -> str:
        """Generate sample connected extension ID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def sample_connected_extension(self, sample_user_id, sample_connected_extension_id) -> ConnectedExtension:
        """Create sample connected extension for testing."""
        return ConnectedExtension(
            id=sample_connected_extension_id,
            user_id=sample_user_id,
            extension_enum="github",
            extension_name="GitHub",
            connection_status=ConnectionStatus.PENDING,
            connected_account_id=None,
            auth_value=None,
            auth_scheme=None,
            created_at=datetime.utcnow(),
            is_deleted=False,
        )

    # ================================
    # CONNECTION SUCCESS CALLBACK TESTS
    # ================================

    async def test_connection_success_with_valid_parameters(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
        sample_connected_extension: ConnectedExtension,
    ):
        """Test successful connection callback with valid parameters."""
        # Mock the scalar_one_or_none result for finding the connected extension
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_connected_extension
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            with patch("app.core.settings.env_settings.FRONTEND_REDIRECT_URL", "http://localhost:3000/callback"):
                response = client.get(
                    f"/api/v1/callback/extension/{sample_user_id}/{sample_connected_extension_id}",
                    params={
                        "status": "success",
                        "connectedAccountId": "github-account-123",
                        "appName": "GitHub",
                    },
                )

            # Check for redirect response (307 Temporary Redirect)
            assert response.status_code == 307  # RedirectResponse status code
            assert "http://localhost:3000/callback?success=true&message=successfully%20connected" in response.headers["location"]

            # Verify that the database was updated correctly
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    async def test_connection_success_with_missing_parameters(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
        sample_connected_extension: ConnectedExtension,
    ):
        """Test connection callback with missing parameters."""
        # Mock the scalar_one_or_none result for finding the connected extension
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_connected_extension
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            with patch("app.core.settings.env_settings.FRONTEND_REDIRECT_URL", "http://localhost:3000/callback"):
                response = client.get(
                    f"/api/v1/callback/extension/{sample_user_id}/{sample_connected_extension_id}",
                    params={
                        "status": "success",
                        # Missing connectedAccountId and appName
                    },
                )

            assert response.status_code == 307  # RedirectResponse status code
            assert "http://localhost:3000/callback?success=false&message=missing%20parameters" in response.headers["location"]

            # Verify that the database was updated to FAILED status
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    async def test_connection_success_with_failed_status(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
        sample_connected_extension: ConnectedExtension,
    ):
        """Test connection callback with failed status."""
        # Mock the scalar_one_or_none result for finding the connected extension
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_connected_extension
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            with patch("app.core.settings.env_settings.FRONTEND_REDIRECT_URL", "http://localhost:3000/callback"):
                response = client.get(
                    f"/api/v1/callback/extension/{sample_user_id}/{sample_connected_extension_id}",
                    params={
                        "status": "failed",
                        "connectedAccountId": "github-account-123",
                        "appName": "GitHub",
                    },
                )

            assert response.status_code == 307  # RedirectResponse status code
            assert (
                "http://localhost:3000/callback?success=false&message=connection%20failed%20or%20is%20still%20pending" in response.headers["location"]
            )

            # Verify that the database was updated to FAILED status
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    async def test_connection_success_with_pending_status(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
        sample_connected_extension: ConnectedExtension,
    ):
        """Test connection callback with pending status."""
        # Mock the scalar_one_or_none result for finding the connected extension
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_connected_extension
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            with patch("app.core.settings.env_settings.FRONTEND_REDIRECT_URL", "http://localhost:3000/callback"):
                response = client.get(
                    f"/api/v1/callback/extension/{sample_user_id}/{sample_connected_extension_id}",
                    params={
                        "status": "pending",
                        "connectedAccountId": "github-account-123",
                        "appName": "GitHub",
                    },
                )

            assert response.status_code == 307  # RedirectResponse status code
            assert (
                "http://localhost:3000/callback?success=false&message=connection%20failed%20or%20is%20still%20pending" in response.headers["location"]
            )

            # Verify that the database was updated to FAILED status
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    async def test_connection_success_with_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
        sample_connected_extension: ConnectedExtension,
    ):
        """Test connection callback with database error."""
        # Mock the scalar_one_or_none result for finding the connected extension
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_connected_extension

        # Mock database error on execute
        mock_session.execute.side_effect = [mock_result, SQLAlchemyError("Database connection failed")]

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            with patch("app.core.settings.env_settings.FRONTEND_REDIRECT_URL", "http://localhost:3000/callback"):
                response = client.get(
                    f"/api/v1/callback/extension/{sample_user_id}/{sample_connected_extension_id}",
                    params={
                        "status": "success",
                        "connectedAccountId": "github-account-123",
                        "appName": "GitHub",
                    },
                )

            assert response.status_code == 307  # RedirectResponse status code
            assert "http://localhost:3000/callback?success=false&message=failed%20to%20establish%20connection" in response.headers["location"]

            # Verify that rollback was called due to the error
            mock_session.rollback.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    async def test_connection_success_without_query_parameters(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
        sample_connected_extension: ConnectedExtension,
    ):
        """Test connection callback without any query parameters."""
        # Mock the scalar_one_or_none result for finding the connected extension
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_connected_extension
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            with patch("app.core.settings.env_settings.FRONTEND_REDIRECT_URL", "http://localhost:3000/callback"):
                response = client.get(f"/api/v1/callback/extension/{sample_user_id}/{sample_connected_extension_id}")

            assert response.status_code == 307  # RedirectResponse status code
            assert "http://localhost:3000/callback?success=false&message=missing%20parameters" in response.headers["location"]

            # Verify that the database was updated to FAILED status
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    async def test_connection_success_with_partial_parameters(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
        sample_connected_extension: ConnectedExtension,
    ):
        """Test connection callback with only some required parameters."""
        # Mock the scalar_one_or_none result for finding the connected extension
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_connected_extension
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            with patch("app.core.settings.env_settings.FRONTEND_REDIRECT_URL", "http://localhost:3000/callback"):
                response = client.get(
                    f"/api/v1/callback/extension/{sample_user_id}/{sample_connected_extension_id}",
                    params={
                        "status": "success",
                        "connectedAccountId": "github-account-123",
                        # Missing appName
                    },
                )

            assert response.status_code == 307  # RedirectResponse status code
            assert "http://localhost:3000/callback?success=false&message=missing%20parameters" in response.headers["location"]

            # Verify that the database was updated to FAILED status
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    async def test_connection_success_url_encoding(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
        sample_connected_extension: ConnectedExtension,
    ):
        """Test that URL parameters are properly encoded in redirect URLs."""
        # Mock the scalar_one_or_none result for finding the connected extension
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_connected_extension
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            with patch("app.core.settings.env_settings.FRONTEND_REDIRECT_URL", "http://localhost:3000/callback"):
                response = client.get(
                    f"/api/v1/callback/extension/{sample_user_id}/{sample_connected_extension_id}",
                    params={
                        "status": "success",
                        "connectedAccountId": "github-account-123",
                        "appName": "GitHub",
                    },
                )

            assert response.status_code == 307
            location = response.headers["location"]

            # Check that the success message is properly URL-encoded
            assert "success=true" in location
            assert "message=successfully%20connected" in location

        finally:
            app.dependency_overrides.clear()
