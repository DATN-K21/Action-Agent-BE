"""
Unit tests for extension API endpoints.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.enums import ConnectionStatus
from app.db_models.connected_extension import ConnectedExtension
from app.main import app


# Define DeleteConnection class for mock responses
class DeleteConnection:
    """Mock class for extension disconnect response."""

    def __init__(self, status, count, message, error_code=None):
        self.status = status
        self.count = count
        self.message = message
        self.error_code = error_code


class TestExtensionApiEndpoints:
    """Test class for extension API endpoints."""

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

    # ================================
    # ACTIVE EXTENSION TESTS
    # ================================

    async def test_active_extension_success_new_connection(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
    ):
        """Test activating an extension with a new connection.

        This test verifies that when a user activates a new extension connection,
        the API correctly initializes the connection, stores it in the database,
        and returns a success response with the appropriate redirect URL.
        """
        # Setup mock for extension service manager
        from unittest.mock import patch

        from app.services.extensions.extension_service_manager import ExtensionServiceInfo

        # Mock service object with proper behavior for a GitHub extension
        mock_service = MagicMock()
        mock_service.get_app_enum.return_value = "github"
        mock_service.get_name.return_value = "GitHub"

        # Setup connection request with redirect URL for OAuth flow
        mock_connection_request = MagicMock()
        mock_connection_request.redirectUrl = "https://github.com/login/oauth/authorize"
        mock_service.initialize_connection.return_value = mock_connection_request

        # Mock service info container
        mock_service_info = MagicMock(spec=ExtensionServiceInfo)
        mock_service_info.service_object = mock_service

        # Override the database session dependency (not used by this endpoint)
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        # Define the extension_enum to use
        extension_enum = "github"

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Configure the mock to return our service info
            mock_get_service_info.return_value = mock_service_info

            try:
                # Make API request to activate extension
                response = client.post(f"/api/v1/extension/active?extension_enum={extension_enum}", headers={"x-user-id": sample_user_id})

                # Check for successful response
                assert response.status_code == 200
                response_data = response.json()

                # Verify the response structure
                assert response_data["status"] == 200
                assert "data" in response_data

                # Verify the data content shows it's a new connection with redirect URL
                data = response_data["data"]
                assert data["isExisted"] is False
                assert data["redirectUrl"] == "https://github.com/login/oauth/authorize"

                # Verify service was properly initialized
                mock_service.initialize_connection.assert_called_once_with(user_id=sample_user_id)
                mock_get_service_info.assert_called_once_with(extension_enum)

            finally:
                app.dependency_overrides.clear()

    async def test_active_extension_success_existing_connection(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
    ):
        """Test activating an extension with an existing connection.

        This test verifies that when a user attempts to activate an extension
        that already has a connection, the API returns a success response with
        isExisted=True and no redirectUrl.
        """
        # Setup mock for extension service manager
        from unittest.mock import patch

        from app.services.extensions.extension_service_manager import ExtensionServiceInfo

        # Mock service object
        mock_service = MagicMock()
        mock_service.get_app_enum.return_value = "github"
        mock_service.get_name.return_value = "GitHub"

        # Return None to simulate existing connection
        mock_service.initialize_connection.return_value = None

        # Mock service info
        mock_service_info = MagicMock(spec=ExtensionServiceInfo)
        mock_service_info.service_object = mock_service

        # Override the dependency (not used by this endpoint)
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        # Define the extension_enum to use
        extension_enum = "github"

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Configure the mock to return our service info
            mock_get_service_info.return_value = mock_service_info

            try:
                # Make API request to activate extension
                response = client.post(f"/api/v1/extension/active?extension_enum={extension_enum}", headers={"x-user-id": sample_user_id})

                # Check for successful response
                assert response.status_code == 200
                response_data = response.json()

                # Verify the response structure
                assert response_data["status"] == 200
                assert "data" in response_data

                # Verify the data content
                data = response_data["data"]
                assert data["isExisted"] is True
                assert data["redirectUrl"] is None

                # Verify service was properly called
                mock_service.initialize_connection.assert_called_once_with(user_id=sample_user_id)

            finally:
                app.dependency_overrides.clear()

    async def test_active_extension_service_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
    ):
        """Test activating an extension when the extension service is not found.

        This test verifies that when a user attempts to activate a non-existent extension,
        the API returns a 404 error with an appropriate error message.
        """
        from unittest.mock import patch

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        # Define a non-existent extension_enum
        extension_enum = "nonexistent"

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Return None to simulate service not found
            mock_get_service_info.return_value = None

            try:
                # Make API request with non-existent extension
                response = client.post(f"/api/v1/extension/active?extension_enum={extension_enum}", headers={"x-user-id": sample_user_id})

                # Check for error response
                assert response.status_code == 404
                response_data = response.json()

                # Verify the response structure contains correct error info
                assert response_data["status"] == 404
                assert response_data["message"] == "Extension Info or Extension Service not found"

                # Verify the service info was requested with the correct extension enum
                mock_get_service_info.assert_called_once_with(extension_enum)

            finally:
                app.dependency_overrides.clear()

    async def test_active_extension_service_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
    ):
        """Test activating an extension when the extension service raises an error.

        This test verifies that when the extension service raises an error during initialization,
        the API properly handles the error and returns a 500 response.
        """
        # Setup mock for extension service manager
        from unittest.mock import patch

        from app.services.extensions.extension_service_manager import ExtensionServiceInfo

        # Mock service object with necessary return values
        mock_service = MagicMock()
        mock_service.get_app_enum.return_value = "github"
        mock_service.get_name.return_value = "GitHub"

        # Setup initialize_connection to raise an error
        mock_service.initialize_connection.side_effect = Exception("Extension service error")

        # Mock service info
        mock_service_info = MagicMock(spec=ExtensionServiceInfo)
        mock_service_info.service_object = mock_service

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        # Define the extension_enum to use
        extension_enum = "github"

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Configure the mock to return our service info
            mock_get_service_info.return_value = mock_service_info

            try:
                # Make API request
                response = client.post(f"/api/v1/extension/active?extension_enum={extension_enum}", headers={"x-user-id": sample_user_id})

                # Check for error response
                assert response.status_code == 500
                response_data = response.json()

                # Verify the response structure indicates an error
                assert response_data["status"] == 500
                assert response_data["message"] == "Internal server error"

                # Verify the service method was called
                mock_service.initialize_connection.assert_called_once_with(user_id=sample_user_id)

                # Verify session rollback was called (even though no DB operations happened)
                mock_session.rollback.assert_called_once()

            finally:
                app.dependency_overrides.clear()

    # ================================
    # DISCONNECT EXTENSION TESTS
    # ================================

    async def test_disconnect_extension_success_as_user(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension: ConnectedExtension,
        sample_connected_extension_id: str,
    ):
        """Test disconnecting an extension as a regular user."""
        # Mock the extension result
        extension_result = AsyncMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=sample_connected_extension)

        # Mock successful update operation
        update_result = AsyncMock()

        # Setup mock for extension service manager
        from unittest.mock import patch

        from app.services.extensions.extension_service_manager import ExtensionServiceInfo

        # Mock service object
        mock_service = MagicMock()

        # Setup disconnect result
        mock_disconnect_result = DeleteConnection(status="success", count=1, message="Connection deleted successfully", error_code=None)
        mock_service.disconnect.return_value = mock_disconnect_result

        # Mock service info
        mock_service_info = MagicMock(spec=ExtensionServiceInfo)
        mock_service_info.service_object = mock_service

        # Configure mock session
        mock_session.execute = AsyncMock(side_effect=[extension_result, update_result])
        mock_session.commit = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Configure the mock to return our service info
            mock_get_service_info.return_value = mock_service_info

            try:
                response = client.post(
                    f"/api/v1/extension/disconnect?extension_enum={sample_connected_extension.extension_enum}",
                    headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                )

                # Check for successful response
                assert response.status_code == 200
                response_data = response.json()

                # Verify the response structure
                assert response_data["status"] == 200
                assert "data" in response_data

                # Verify the data content
                data = response_data["data"]
                assert data["status"] == "success"
                assert data["count"] == 1
                assert data["message"] == "Connection deleted successfully"

                # Verify mock calls
                mock_service.disconnect.assert_called_once_with(sample_connected_extension.connected_account_id)
                mock_session.execute.assert_called()
                mock_session.commit.assert_called_once()

            finally:
                app.dependency_overrides.clear()

    async def test_disconnect_extension_success_as_admin(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_connected_extension: ConnectedExtension,
        sample_connected_extension_id: str,
    ):
        """Test disconnecting an extension as an admin user."""
        # Mock the extension result
        extension_result = AsyncMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=sample_connected_extension)

        # Mock successful update operation
        update_result = AsyncMock()

        # Setup mock for extension service manager
        from unittest.mock import patch

        from app.services.extensions.extension_service_manager import ExtensionServiceInfo

        # Mock service object
        mock_service = MagicMock()

        # Setup disconnect result
        mock_disconnect_result = DeleteConnection(status="success", count=1, message="Connection deleted successfully", error_code=None)
        mock_service.disconnect.return_value = mock_disconnect_result

        # Mock service info
        mock_service_info = MagicMock(spec=ExtensionServiceInfo)
        mock_service_info.service_object = mock_service

        # Configure mock session
        mock_session.execute = AsyncMock(side_effect=[extension_result, update_result])
        mock_session.commit = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Configure the mock to return our service info
            mock_get_service_info.return_value = mock_service_info

            try:
                response = client.post(
                    f"/api/v1/extension/disconnect?extension_enum={sample_connected_extension.extension_enum}",
                    headers={"x-user-id": "admin-123", "x-user-role": "admin"},
                )

                # Check for successful response
                assert response.status_code == 200
                response_data = response.json()

                # Verify the response structure
                assert response_data["status"] == 200
                assert "data" in response_data

                # Verify the data content
                data = response_data["data"]
                assert data["status"] == "success"
                assert data["count"] == 1
                assert data["message"] == "Connection deleted successfully"

                # Verify mock calls
                mock_service.disconnect.assert_called_once_with(sample_connected_extension.connected_account_id)
                mock_session.execute.assert_called()
                mock_session.commit.assert_called_once()

            finally:
                app.dependency_overrides.clear()

    async def test_disconnect_extension_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
    ):
        """Test disconnecting an extension that doesn't exist."""
        # Mock the extension result (not found)
        extension_result = AsyncMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=None)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=extension_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.post(
                f"/api/v1/extension/disconnect?extension_enum=nonexistent",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 404
            response_data = response.json()

            # Verify the response structure indicates a not found error
            assert response_data["status"] == 404
            assert response_data["message"] == "Connected Extension not found"

        finally:
            app.dependency_overrides.clear()

    async def test_disconnect_extension_service_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension: ConnectedExtension,
        sample_connected_extension_id: str,
    ):
        """Test disconnecting an extension when the extension service is not found."""
        # Mock the extension result
        extension_result = AsyncMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=sample_connected_extension)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=extension_result)

        # Setup mock for extension service manager
        from unittest.mock import patch

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Return None to simulate service not found
            mock_get_service_info.return_value = None

            try:
                response = client.post(
                    f"/api/v1/extension/disconnect?extension_enum={sample_connected_extension.extension_enum}",
                    headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                )

                # Check for error response
                assert response.status_code == 404
                response_data = response.json()

                # Verify the response structure indicates a not found error
                assert response_data["status"] == 404
                assert response_data["message"] == "Extension Info or Extension Service not found"

            finally:
                app.dependency_overrides.clear()

    async def test_disconnect_extension_account_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
    ):
        """Test disconnecting an extension when the account ID is not found."""
        # Create a modified extension with no account ID
        connected_extension = ConnectedExtension(
            id=sample_connected_extension_id,
            user_id=sample_user_id,
            extension_enum="github",
            extension_name="GitHub",
            connection_status=ConnectionStatus.SUCCESS,
            connected_account_id=None,  # Missing account ID
            auth_value="oauth-token-123",
            auth_scheme="Bearer",
            created_at=datetime.utcnow(),
            is_deleted=False,
        )

        # Mock the extension result
        extension_result = AsyncMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=connected_extension)

        # Setup mock for extension service manager
        from unittest.mock import patch

        from app.services.extensions.extension_service_manager import ExtensionServiceInfo

        # Mock service object
        mock_service = MagicMock()

        # Mock service info
        mock_service_info = MagicMock(spec=ExtensionServiceInfo)
        mock_service_info.service_object = mock_service

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=extension_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Configure the mock to return our service info
            mock_get_service_info.return_value = mock_service_info

            try:
                response = client.post(
                    f"/api/v1/extension/disconnect?extension_enum={connected_extension.extension_enum}",
                    headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                )

                # Check for error response
                assert response.status_code == 404
                response_data = response.json()

                # Verify the response structure indicates a not found error
                assert response_data["status"] == 404
                assert response_data["message"] == "Account not found"

            finally:
                app.dependency_overrides.clear()

    async def test_disconnect_extension_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
    ):
        """Test disconnecting an extension when a database error occurs."""
        # Mock the database error
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))
        mock_session.rollback = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.post(
                f"/api/v1/extension/disconnect?extension_enum=github",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 500
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Internal server error"

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    # ================================
    # CHECK CONNECTION TESTS
    # ================================

    async def test_check_active_connection_success_as_user(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension: ConnectedExtension,
        sample_connected_extension_id: str,
    ):
        """Test checking an active connection as a regular user."""
        # Mock the extension result
        extension_result = AsyncMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=sample_connected_extension)

        # Setup mock for extension service manager
        from unittest.mock import patch

        from app.services.extensions.extension_service_manager import ExtensionServiceInfo

        # Mock service object
        mock_service = MagicMock()

        # Setup check_connection result
        mock_service.check_connection.return_value = True

        # Mock service info
        mock_service_info = MagicMock(spec=ExtensionServiceInfo)
        mock_service_info.service_object = mock_service

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=extension_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Configure the mock to return our service info
            mock_get_service_info.return_value = mock_service_info

            try:
                response = client.get(
                    f"/api/v1/extension/check-active?extension_enum={sample_connected_extension.extension_enum}",
                    headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                )

                # Check for successful response
                assert response.status_code == 200
                response_data = response.json()

                # Verify the response structure
                assert response_data["status"] == 200
                assert "data" in response_data

                # Verify the data content
                data = response_data["data"]
                assert data["isConnected"] is True  # Note: API returns camelCase, not snake_case

                # Verify mock calls
                mock_service.check_connection.assert_called_once_with(user_id=sample_user_id)

            finally:
                app.dependency_overrides.clear()

    async def test_check_active_connection_success_as_admin(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_connected_extension: ConnectedExtension,
        sample_connected_extension_id: str,
    ):
        """Test checking an active connection as an admin user."""
        # Mock the extension result
        extension_result = AsyncMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=sample_connected_extension)

        # Setup mock for extension service manager
        from unittest.mock import patch

        from app.services.extensions.extension_service_manager import ExtensionServiceInfo

        # Mock service object
        mock_service = MagicMock()

        # Setup check_connection result
        mock_service.check_connection.return_value = True

        # Mock service info
        mock_service_info = MagicMock(spec=ExtensionServiceInfo)
        mock_service_info.service_object = mock_service

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=extension_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Configure the mock to return our service info
            mock_get_service_info.return_value = mock_service_info

            try:
                admin_user_id = "admin-123"
                response = client.get(
                    f"/api/v1/extension/check-active?extension_enum={sample_connected_extension.extension_enum}",
                    headers={"x-user-id": admin_user_id, "x-user-role": "admin"},
                )

                # Check for successful response
                assert response.status_code == 200
                response_data = response.json()

                # Verify the response structure
                assert response_data["status"] == 200
                assert "data" in response_data

                # Verify the data content
                data = response_data["data"]
                assert data["isConnected"] is True  # Note: API returns camelCase, not snake_case

                # Verify mock calls
                mock_service.check_connection.assert_called_once_with(user_id=admin_user_id)

            finally:
                app.dependency_overrides.clear()

    async def test_check_active_connection_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
    ):
        """Test checking an active connection that doesn't exist."""
        # Mock the extension result (not found)
        extension_result = AsyncMock()
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
                f"/api/v1/extension/check-active?extension_enum=nonexistent",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 404
            response_data = response.json()

            # Verify the response structure indicates a not found error
            assert response_data["status"] == 404
            assert response_data["message"] == "Connected Extension not found"

        finally:
            app.dependency_overrides.clear()

    async def test_check_active_service_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension: ConnectedExtension,
        sample_connected_extension_id: str,
    ):
        """Test checking an active connection when the extension service is not found."""
        # Mock the extension result
        extension_result = AsyncMock()
        extension_result.scalar_one_or_none = MagicMock(return_value=sample_connected_extension)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=extension_result)

        # Setup mock for extension service manager
        from unittest.mock import patch

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        with patch(
            "app.services.extensions.extension_service_manager.extension_service_manager.aget_service_info", new_callable=AsyncMock
        ) as mock_get_service_info:
            # Return None to simulate service not found
            mock_get_service_info.return_value = None

            try:
                response = client.get(
                    f"/api/v1/extension/check-active?extension_enum={sample_connected_extension.extension_enum}",
                    headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                )

                # Check for error response
                assert response.status_code == 404
                response_data = response.json()

                # Verify the response structure indicates a not found error
                assert response_data["status"] == 404
                assert response_data["message"] == "Extension Info or Extension Service not found"

            finally:
                app.dependency_overrides.clear()

    async def test_check_active_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_extension_id: str,
    ):
        """Test checking an active connection when a database error occurs."""
        # Mock the database error
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/extension/check-active?extension_enum=github",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 500
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Internal server error"

        finally:
            app.dependency_overrides.clear()
