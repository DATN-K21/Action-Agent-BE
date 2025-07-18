"""
Unit tests for connected extension API endpoints.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.enums import ConnectionStatus
from app.db_models.connected_extension import ConnectedExtension
from app.main import app


class TestConnectedExtensionApiEndpoints:
    """Test class for connected extension API endpoints."""

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
            connection_status=ConnectionStatus.SUCCESS,
            connected_account_id="github-account-123",
            auth_value="oauth-token-123",
            auth_scheme="Bearer",
            created_at=datetime.utcnow(),
            is_deleted=False,
        )

    @pytest.fixture
    def sample_connected_extensions(self, sample_user_id) -> list[ConnectedExtension]:
        """Create a list of sample connected extensions for testing."""
        return [
            ConnectedExtension(
                id=str(uuid.uuid4()),
                user_id=sample_user_id,
                extension_enum="github",
                extension_name="GitHub",
                connection_status=ConnectionStatus.SUCCESS,
                connected_account_id="github-account-123",
                auth_value="oauth-token-123",
                auth_scheme="Bearer",
                created_at=datetime.utcnow(),
                is_deleted=False,
            ),
            ConnectedExtension(
                id=str(uuid.uuid4()),
                user_id=sample_user_id,
                extension_enum="gitlab",
                extension_name="GitLab",
                connection_status=ConnectionStatus.PENDING,
                connected_account_id=None,
                auth_value=None,
                auth_scheme=None,
                created_at=datetime.utcnow(),
                is_deleted=False,
            ),
            ConnectedExtension(
                id=str(uuid.uuid4()),
                user_id=sample_user_id,
                extension_enum="jira",
                extension_name="Jira",
                connection_status=ConnectionStatus.FAILED,
                connected_account_id=None,
                auth_value=None,
                auth_scheme=None,
                created_at=datetime.utcnow(),
                is_deleted=False,
            ),
        ]

    # ================================
    # GET ALL CONNECTED EXTENSIONS TESTS
    # ================================

    async def test_get_all_connected_extensions_as_regular_user(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extensions: list[ConnectedExtension],
    ):
        """Test getting all connected extensions as a regular user."""
        # Mock the count result
        from unittest.mock import MagicMock

        count_result = MagicMock()
        count_result.scalar_one = MagicMock(return_value=len(sample_connected_extensions))

        # Mock the extensions result
        extensions_result = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=sample_connected_extensions)
        extensions_result.scalars = MagicMock(return_value=scalars_mock)

        # Configure mock session to return different results for different calls
        mock_session.execute = AsyncMock(side_effect=[count_result, extensions_result])

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                "/api/v1/connected-extension/get-all",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                params={"page_number": 1, "max_per_page": 10},
            )

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data

            # Verify the data content
            data = response_data["data"]
            assert data["pageNumber"] == 1
            assert data["maxPerPage"] == 10
            assert data["totalPage"] == 1
            assert len(data["connectedExtensions"]) == len(sample_connected_extensions)

            # Verify the extensions data
            for i, extension in enumerate(data["connectedExtensions"]):
                assert extension["extensionName"] == sample_connected_extensions[i].extension_name
                assert extension["connectionStatus"] == sample_connected_extensions[i].connection_status.value

        finally:
            app.dependency_overrides.clear()

    async def test_get_all_connected_extensions_as_admin(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extensions: list[ConnectedExtension],
    ):
        """Test getting all connected extensions as an admin user."""
        # Mock the count result
        from unittest.mock import MagicMock

        count_result = MagicMock()
        count_result.scalar_one = MagicMock(return_value=len(sample_connected_extensions))

        # Mock the extensions result
        extensions_result = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=sample_connected_extensions)
        extensions_result.scalars = MagicMock(return_value=scalars_mock)

        # Configure mock session to return different results for different calls
        mock_session.execute = AsyncMock(side_effect=[count_result, extensions_result])

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                "/api/v1/connected-extension/get-all",
                headers={"x-user-id": sample_user_id, "x-user-role": "admin"},
                params={"page_number": 1, "max_per_page": 10},
            )

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data

            # Verify the data content
            data = response_data["data"]
            assert data["pageNumber"] == 1
            assert data["maxPerPage"] == 10
            assert data["totalPage"] == 1
            assert len(data["connectedExtensions"]) == len(sample_connected_extensions)

        finally:
            app.dependency_overrides.clear()

    async def test_get_all_connected_extensions_empty_result(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
    ):
        """Test getting all connected extensions when no extensions exist."""
        # Mock the count result
        from unittest.mock import MagicMock

        count_result = MagicMock()
        count_result.scalar_one = MagicMock(return_value=0)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=count_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                "/api/v1/connected-extension/get-all",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                params={"page_number": 1, "max_per_page": 10},
            )

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data

            # Verify the data content shows empty results
            data = response_data["data"]
            assert data["pageNumber"] == 1
            assert data["maxPerPage"] == 10
            assert data["totalPage"] == 0
            assert len(data["connectedExtensions"]) == 0

        finally:
            app.dependency_overrides.clear()

    async def test_get_all_connected_extensions_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
    ):
        """Test getting all connected extensions when a database error occurs."""
        # Mock the database error
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                "/api/v1/connected-extension/get-all",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                params={"page_number": 1, "max_per_page": 10},
            )

            data = response.json()
            print("[data]", data)

            # Check for error response
            assert response.status_code == 500
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Database error occurred"

        finally:
            app.dependency_overrides.clear()

    # ================================
    # GET CONNECTED EXTENSION DETAIL TESTS
    # ================================

    async def test_get_connected_extension_detail_as_regular_user(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension: ConnectedExtension,
        sample_connected_extension_id: str,
    ):
        """Test getting a specific connected extension detail as a regular user."""
        # Mock the extension result
        from unittest.mock import MagicMock

        extension_result = MagicMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=sample_connected_extension)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=extension_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/connected-extension/{sample_connected_extension_id}/get-detail-by-id",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data

            # Verify the extension data
            data = response_data["data"]
            assert data["id"] == sample_connected_extension.id
            assert data["userId"] == sample_connected_extension.user_id
            assert data["extensionEnum"] == sample_connected_extension.extension_enum
            assert data["extensionName"] == sample_connected_extension.extension_name
            assert data["connectionStatus"] == sample_connected_extension.connection_status.value
            assert data["connectedAccountId"] == sample_connected_extension.connected_account_id
            assert data["authScheme"] == sample_connected_extension.auth_scheme

        finally:
            app.dependency_overrides.clear()

    async def test_get_connected_extension_detail_as_admin(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension: ConnectedExtension,
        sample_connected_extension_id: str,
    ):
        """Test getting a specific connected extension detail as an admin user."""
        # Mock the extension result
        from unittest.mock import MagicMock

        extension_result = MagicMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=sample_connected_extension)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=extension_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/connected-extension/{sample_connected_extension_id}/get-detail-by-id",
                headers={"x-user-id": "admin-user", "x-user-role": "admin"},
            )

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data

            # Verify the extension data
            data = response_data["data"]
            assert data["id"] == sample_connected_extension.id
            assert data["extensionName"] == sample_connected_extension.extension_name

        finally:
            app.dependency_overrides.clear()

    async def test_get_connected_extension_detail_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
    ):
        """Test getting a connected extension that doesn't exist."""
        # Mock the extension result (not found)
        from unittest.mock import MagicMock

        extension_result = MagicMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=None)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=extension_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/connected-extension/{sample_connected_extension_id}/get-detail-by-id",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 404  # API returns 404 for not found errors
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 404
            assert response_data["message"] == "Connected extension not found"

        finally:
            app.dependency_overrides.clear()

    async def test_get_connected_extension_detail_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
    ):
        """Test getting a connected extension when a database error occurs."""
        # Mock the database error
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/connected-extension/{sample_connected_extension_id}/get-detail-by-id",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 500  # API returns 500 for database errors
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Database error occurred"

        finally:
            app.dependency_overrides.clear()
