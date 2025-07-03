"""
Unit tests for user API endpoints.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Row

from app.core.enums import LlmProvider
from app.db_models.user_api_key import UserApiKey


class TestUserApiEndpoints:
    """Test class for user API endpoints."""

    @pytest.fixture
    def mock_db_records_with_keys(self) -> list[Row]:
        """Mock database records with API keys."""
        # Create mock row objects that mimic SQLAlchemy result rows
        row1 = MagicMock()
        row1.__getitem__ = lambda self, key: {
            "user_id": "user-123",
            "default_api_key_id": "api-key-123",
            "remain_trial_tokens": 1000,
            "api_key_id": "api-key-123",
            "provider": LlmProvider.OPENAI,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }[key]

        row2 = MagicMock()
        row2.__getitem__ = lambda self, key: {
            "user_id": "user-123",
            "default_api_key_id": "api-key-123",
            "remain_trial_tokens": 1000,
            "api_key_id": "api-key-456",
            "provider": LlmProvider.ANTHROPIC,
            "created_at": datetime(2024, 1, 2, 12, 0, 0),
        }[key]

        return [row1, row2]

    @pytest.fixture
    def mock_db_records_without_keys(self) -> list[Row]:
        """Mock database records without API keys."""
        row = MagicMock()
        row.__getitem__ = lambda self, key: {
            "user_id": "user-123",
            "default_api_key_id": None,
            "remain_trial_tokens": 1000,
            "api_key_id": None,
            "provider": None,
            "created_at": None,
        }[key]

        return [row]

    async def test_get_api_keys_success_with_keys(self, client: TestClient, mock_session: AsyncMock, mock_db_records_with_keys: list[Row]):
        """Test successful retrieval of API keys when user has keys."""
        # Setup mock result
        mock_result = AsyncMock()
        mock_result.mappings.return_value.all.return_value = mock_db_records_with_keys
        mock_session.execute.return_value = mock_result

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.get("/api/v1/user/key/get-all", headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        assert data["data"]["user_id"] == "user-123"
        assert data["data"]["default_api_key_id"] == "api-key-123"
        assert data["data"]["remain_trial_tokens"] == 1000
        assert len(data["data"]["api_keys"]) == 2
        assert data["data"]["api_keys"][0]["provider"] == LlmProvider.OPENAI
        assert data["data"]["api_keys"][1]["provider"] == LlmProvider.ANTHROPIC

    async def test_get_api_keys_success_without_keys(self, client: TestClient, mock_session: AsyncMock, mock_db_records_without_keys: list[Row]):
        """Test successful retrieval when user has no API keys."""
        # Setup mock result
        mock_result = AsyncMock()
        mock_result.mappings.return_value.all.return_value = mock_db_records_without_keys
        mock_session.execute.return_value = mock_result

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.get("/api/v1/user/key/get-all", headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        assert data["data"]["user_id"] == "user-123"
        assert data["data"]["default_api_key_id"] is None
        assert data["data"]["remain_trial_tokens"] == 1000
        assert len(data["data"]["api_keys"]) == 0

    async def test_get_api_keys_user_not_found(self, client: TestClient, mock_session: AsyncMock):
        """Test get API keys when user is not found."""
        # Setup mock result for empty records
        mock_result = AsyncMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.get("/api/v1/user/key/get-all", headers={"x-user-id": "non-existent-user"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 404
        assert data["message"] == "User not found"

    async def test_get_api_keys_database_error(self, client: TestClient, mock_session: AsyncMock):
        """Test get API keys when database error occurs."""
        # Setup mock to raise exception
        mock_session.execute.side_effect = Exception("Database connection failed")

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.get("/api/v1/user/key/get-all", headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 500
        assert data["message"] == "Internal server error"

    async def test_set_default_api_key_success_with_provider(self, client: TestClient, mock_session: AsyncMock):
        """Test successful setting of default API key with provider."""
        # Mock API key lookup
        api_key_result = AsyncMock()
        api_key_result.scalar_one_or_none.return_value = "api-key-123"

        # Mock user update
        update_result = AsyncMock()
        update_result.scalar_one_or_none.return_value = "api-key-123"

        mock_session.execute.side_effect = [api_key_result, update_result]

        request_data = {"user_id": "user-123", "provider": LlmProvider.OPENAI.value}

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.post("/api/v1/user/key/set-default", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        mock_session.commit.assert_called_once()

    async def test_set_default_api_key_success_with_null_provider(self, client: TestClient, mock_session: AsyncMock):
        """Test successful unsetting of default API key with null provider."""
        # Mock user update
        update_result = AsyncMock()
        update_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = update_result

        request_data = {"user_id": "user-123", "provider": None}

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.post("/api/v1/user/key/set-default", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        mock_session.commit.assert_called_once()

    async def test_set_default_api_key_not_found(self, client: TestClient, mock_session: AsyncMock):
        """Test set default API key when API key is not found."""
        # Mock API key lookup returning None
        api_key_result = AsyncMock()
        api_key_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = api_key_result

        request_data = {"user_id": "user-123", "provider": LlmProvider.OPENAI.value}

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.post("/api/v1/user/key/set-default", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 404
        assert data["message"] == "API key not found"

    async def test_set_default_api_key_user_not_found(self, client: TestClient, mock_session: AsyncMock):
        """Test set default API key when user is not found."""
        # Mock API key lookup
        api_key_result = AsyncMock()
        api_key_result.scalar_one_or_none.return_value = "api-key-123"

        # Mock user update returning None (user not found)
        update_result = AsyncMock()
        update_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [api_key_result, update_result]

        request_data = {"user_id": "non-existent-user", "provider": LlmProvider.OPENAI.value}

        with patch("app.core.db_session.get_async_session", return_value=mock_session):
            response = client.post("/api/v1/user/key/set-default", json=request_data, headers={"x-user-id": "non-existent-user"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 404
        assert data["message"] == "User not found"
        mock_session.rollback.assert_called_once()

    async def test_set_default_api_key_database_error(self, client: TestClient, mock_session: AsyncMock):
        """Test set default API key when database error occurs."""
        # Setup mock to raise exception
        mock_session.execute.side_effect = Exception("Database connection failed")

        request_data = {"user_id": "user-123", "provider": LlmProvider.OPENAI.value}

        with patch("app.core.db_session.get_async_session", return_value=mock_session):
            response = client.post("/api/v1/user/key/set-default", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 500
        assert data["message"] == "Internal server error"
        mock_session.rollback.assert_called_once()

    async def test_upsert_api_key_update_existing(self, client: TestClient, mock_session: AsyncMock):
        """Test successful update of existing API key."""
        # Mock existing API key lookup
        existing_key_result = AsyncMock()
        existing_key_result.scalar_one_or_none.return_value = "api-key-123"

        # Mock update result
        update_result = AsyncMock()
        update_result.mappings.return_value.one_or_none.return_value = {
            "id": "api-key-123",
            "provider": LlmProvider.OPENAI,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }

        mock_session.execute.side_effect = [existing_key_result, update_result]

        request_data = {"user_id": "user-123", "provider": LlmProvider.OPENAI.value, "encrypted_value": "new_encrypted_value"}

        with patch("app.core.db_session.get_async_session", return_value=mock_session):
            response = client.put("/api/v1/user/key/upsert", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        assert data["data"]["id"] == "api-key-123"
        assert data["data"]["provider"] == LlmProvider.OPENAI
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_api_key_create_new(self, client: TestClient, mock_session: AsyncMock):
        """Test successful creation of new API key."""
        # Mock existing API key lookup returning None
        existing_key_result = AsyncMock()
        existing_key_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = existing_key_result

        # Mock new API key object
        new_api_key = UserApiKey(
            id="api-key-456",
            user_id="user-123",
            provider=LlmProvider.ANTHROPIC,
            encrypted_value="encrypted_value",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            created_by="user-123",
            is_deleted=False,
        )

        request_data = {"user_id": "user-123", "provider": LlmProvider.ANTHROPIC.value, "encrypted_value": "encrypted_value"}

        with patch("app.api.public.v1.user.SessionDep", return_value=mock_session):
            with patch("app.api.public.v1.user.UserApiKey", return_value=new_api_key):
                response = client.put("/api/v1/user/key/upsert", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_api_key_update_not_found(self, client: TestClient, mock_session: AsyncMock):
        """Test upsert API key when update operation finds no record."""
        # Mock existing API key lookup
        existing_key_result = AsyncMock()
        existing_key_result.scalar_one_or_none.return_value = "api-key-123"

        # Mock update result returning None (record not found during update)
        update_result = AsyncMock()
        update_result.mappings.return_value.one_or_none.return_value = None

        mock_session.execute.side_effect = [existing_key_result, update_result]

        request_data = {"provider": LlmProvider.OPENAI.value, "encrypted_value": "new_encrypted_value"}

        with patch("app.api.public.v1.user.SessionDep", return_value=mock_session):
            response = client.put("/api/v1/user/key/upsert", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 404
        assert data["message"] == "API key not found"

    @pytest.mark.asyncio
    async def test_upsert_api_key_database_error(self, client: TestClient, mock_session: AsyncMock):
        """Test upsert API key when database error occurs."""
        # Setup mock to raise exception
        mock_session.execute.side_effect = Exception("Database connection failed")

        request_data = {"provider": LlmProvider.OPENAI.value, "encrypted_value": "encrypted_value"}

        with patch("app.api.public.v1.user.SessionDep", return_value=mock_session):
            response = client.put("/api/v1/user/key/upsert", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 500
        assert data["message"] == "Internal server error"
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_api_key_success(self, client: TestClient, mock_session: AsyncMock):
        """Test successful deletion of API key."""
        # Mock delete result
        delete_result = AsyncMock()
        delete_result.scalar_one_or_none.return_value = "api-key-123"

        mock_session.execute.return_value = delete_result

        request_data = {"provider": LlmProvider.OPENAI.value}

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.request("DELETE", "/api/v1/user/key/delete", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_api_key_not_found(self, client: TestClient, mock_session: AsyncMock):
        """Test delete API key when key is not found."""
        # Mock delete result returning None
        delete_result = AsyncMock()
        delete_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = delete_result

        request_data = {"provider": LlmProvider.OPENAI.value}

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.request("DELETE", "/api/v1/user/key/delete", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 404
        assert data["message"] == "API key not found"

    @pytest.mark.asyncio
    async def test_delete_api_key_database_error(self, client: TestClient, mock_session: AsyncMock):
        """Test delete API key when database error occurs."""
        # Setup mock to raise exception
        mock_session.execute.side_effect = Exception("Database connection failed")

        request_data = {"provider": LlmProvider.OPENAI.value}

        with patch("app.api.deps.get_async_session", return_value=mock_session):
            response = client.request("DELETE", "/api/v1/user/key/delete", json=request_data, headers={"x-user-id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 500
        assert data["message"] == "Internal server error"
        mock_session.rollback.assert_called_once()

    def test_invalid_provider_validation(self, client: TestClient):
        """Test validation of invalid provider in requests."""
        request_data = {"provider": "invalid_provider", "encrypted_value": "encrypted_value"}

        response = client.put("/api/v1/user/key/upsert", json=request_data, headers={"x-user-id": "user-123"})

        # Should return validation error for invalid provider
        assert response.status_code == 422

    def test_missing_encrypted_value_validation(self, client: TestClient):
        """Test validation when encrypted_value is missing."""
        request_data = {
            "provider": LlmProvider.OPENAI.value
            # encrypted_value is missing
        }

        response = client.put("/api/v1/user/key/upsert", json=request_data, headers={"x-user-id": "user-123"})

        # Should return validation error for missing encrypted_value
        assert response.status_code == 422

    def test_empty_encrypted_value_validation(self, client: TestClient):
        """Test validation when encrypted_value is empty."""
        request_data = {"provider": LlmProvider.OPENAI.value, "encrypted_value": ""}

        response = client.put("/api/v1/user/key/upsert", json=request_data, headers={"x-user-id": "user-123"})

        # Should return validation error for empty encrypted_value
        assert response.status_code == 422
