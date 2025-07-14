"""
Unit tests for thread API endpoints.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.graph.messages import ChatResponse
from app.db_models.assistant import Assistant
from app.db_models.thread import Thread
from app.main import app
from app.schemas.thread import (
    CreateThreadRequest,
    UpdateThreadRequest,
)


class TestThreadApiEndpoints:
    """Test class for thread API endpoints."""

    @pytest.fixture
    def sample_user_id(self) -> str:
        """Generate sample user ID."""
        return "user-123"

    @pytest.fixture
    def sample_thread_id(self) -> str:
        """Generate sample thread ID."""
        return "thread-456"

    @pytest.fixture
    def sample_assistant_id(self) -> str:
        """Generate sample assistant ID."""
        return "assistant-789"

    @pytest.fixture
    def sample_assistant(self, sample_assistant_id, sample_user_id) -> Assistant:
        """Create sample assistant for testing."""
        assistant = Assistant(
            id=sample_assistant_id,
            user_id=sample_user_id,
            name="Test Assistant",
            description="Test assistant description",
            system_prompt="You are a helpful assistant",
            created_at=datetime.utcnow(),
            is_deleted=False,
        )
        # Add missing fields that the API expects
        assistant.provider = "openai"
        assistant.model_name = "gpt-3.5-turbo"
        assistant.temperature = 0.1
        return assistant

    @pytest.fixture
    def sample_thread(self, sample_thread_id, sample_user_id, sample_assistant_id) -> Thread:
        """Create sample thread for testing."""
        return Thread(
            id=sample_thread_id,
            user_id=sample_user_id,
            title="Test Thread",
            assistant_id=sample_assistant_id,
            created_at=datetime.utcnow(),
            is_deleted=False,
        )

    @pytest.fixture
    def sample_threads(self, sample_user_id, sample_assistant_id) -> list[Thread]:
        """Create a list of sample threads for testing."""
        return [
            Thread(
                id=f"thread-{i}",
                user_id=sample_user_id,
                title=f"Test Thread {i}",
                assistant_id=sample_assistant_id,
                created_at=datetime.utcnow(),
                is_deleted=False,
            )
            for i in range(1, 4)
        ]

    @pytest.fixture
    def create_thread_request(self, sample_assistant_id) -> CreateThreadRequest:
        """Create sample request for creating thread."""
        return CreateThreadRequest(
            title="New Thread",
            assistant_id=sample_assistant_id,
        )

    @pytest.fixture
    def update_thread_request(self) -> UpdateThreadRequest:
        """Create sample request for updating thread."""
        return UpdateThreadRequest(
            title="Updated Thread Title",
            assistant_id=None,
        )

    # ================================
    # GET ALL THREADS TESTS
    # ================================

    # async def test_get_all_threads_success(
    #     self,
    #     client: TestClient,
    #     mock_session: AsyncMock,
    #     sample_threads: list[Thread],
    #     sample_assistant: Assistant,
    # ):
    #     """Test successful retrieval of all threads."""
    #     # Add assistant to each thread
    #     for thread in sample_threads:
    #         thread.assistant = sample_assistant

    #     # Mock the scalars result for the data query
    #     mock_scalars = MagicMock()
    #     mock_scalars.all.return_value = sample_threads

    #     # Mock the result for the data query
    #     mock_result = AsyncMock()
    #     mock_result.scalars = MagicMock(return_value=mock_scalars)

    #     # Set up session mock
    #     mock_session.execute.return_value = mock_result

    #     # Override the dependency
    #     from app.core.db_session import get_async_session

    #     async def mock_get_async_session():
    #         yield mock_session

    #     app.dependency_overrides[get_async_session] = mock_get_async_session

    #     try:
    #         response = client.get(
    #             "/api/v1/thread/get-all",
    #             headers={"x-user-id": "user-123"},
    #         )

    #         assert response.status_code == 200
    #         data = response.json()
    #         assert data["status"] == 200
    #         assert len(data["data"]["threads"]) == 3
    #         assert data["data"]["threads"][0]["title"] == "Test Thread 1"
    #         assert data["data"]["threads"][0]["assistant"]["name"] == "Test Assistant"
    #     finally:
    #         # Clean up the dependency override
    #         app.dependency_overrides.clear()

    # async def test_get_all_threads_with_pagination(
    #     self,
    #     client: TestClient,
    #     mock_session: AsyncMock,
    #     sample_threads: list[Thread],
    #     sample_assistant: Assistant,
    # ):
    #     """Test retrieval of threads with pagination parameters."""
    #     # Add assistant to each thread
    #     for thread in sample_threads:
    #         thread.assistant = sample_assistant

    #     # Mock the scalars result for the data query
    #     mock_scalars = MagicMock()
    #     mock_scalars.all.return_value = sample_threads[:2]  # Return only first 2 threads

    #     # Mock the result for the data query
    #     mock_result = AsyncMock()
    #     mock_result.scalars = MagicMock(return_value=mock_scalars)

    #     # Set up session mock
    #     mock_session.execute.return_value = mock_result

    #     # Override the dependency
    #     from app.core.db_session import get_async_session

    #     async def mock_get_async_session():
    #         yield mock_session

    #     app.dependency_overrides[get_async_session] = mock_get_async_session

    #     try:
    #         response = client.get(
    #             "/api/v1/thread/get-all?cursor=2023-01-01T00:00:00&max_per_page=2",
    #             headers={"x-user-id": "user-123"},
    #         )

    #         assert response.status_code == 200
    #         data = response.json()
    #         assert data["status"] == 200
    #         assert len(data["data"]["threads"]) == 2
    #     finally:
    #         # Clean up the dependency override
    #         app.dependency_overrides.clear()

    # async def test_get_all_threads_internal_error(
    #     self,
    #     client: TestClient,
    #     mock_session: AsyncMock,
    # ):
    #     """Test get all threads with internal server error."""
    #     # Make sure the exception is raised during the session.execute call
    #     mock_session.execute.side_effect = Exception("Database error")

    #     # Override the dependency
    #     from app.core.db_session import get_async_session

    #     async def mock_get_async_session():
    #         yield mock_session

    #     app.dependency_overrides[get_async_session] = mock_get_async_session

    #     try:
    #         response = client.get(
    #             "/api/v1/thread/get-all",
    #             headers={"x-user-id": "user-123"},
    #         )

    #         # The HTTP status code is still 200 since FastAPI returns a 200 by default,
    #         # but the response wrapper should contain a status field of 500
    #         assert response.status_code == 200
    #         assert response.json()["status"] == 500
    #         assert "Internal server error" in response.json()["message"]
    #     finally:
    #         # Clean up the dependency override
    #         app.dependency_overrides.clear()

    # ================================
    # CREATE THREAD TESTS
    # ================================

    async def test_create_thread_success(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        create_thread_request: CreateThreadRequest,
        sample_thread: Thread,
        sample_user_id: str,
    ):
        """Test successful thread creation."""
        # Mock add method to capture the thread instance
        captured_thread = None
        original_add = mock_session.add

        def mock_add(obj):
            nonlocal captured_thread
            captured_thread = obj
            # Replace with our sample thread properties
            obj.id = sample_thread.id
            obj.created_at = sample_thread.created_at
            obj.title = sample_thread.title
            return original_add(obj)

        mock_session.add = MagicMock(side_effect=mock_add)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.post(
                "/api/v1/thread/create",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                json=create_thread_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 200
            assert data["data"]["title"] == sample_thread.title
            assert data["data"]["id"] == sample_thread.id
            mock_session.add.assert_called_once()
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    async def test_create_thread_internal_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        create_thread_request: CreateThreadRequest,
        sample_user_id: str,
    ):
        """Test thread creation with internal server error."""
        # Mock add method to simulate database error
        mock_session.add = MagicMock(side_effect=Exception("Database error"))
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.post(
                "/api/v1/thread/create",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                json=create_thread_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 500
            assert "Internal server error" in data["message"]
            mock_session.add.assert_called_once()
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    # ================================
    # GET THREAD DETAILS TESTS
    # ================================

    async def test_get_thread_by_id_success(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_thread: Thread,
        sample_assistant: Assistant,
    ):
        """Test successful retrieval of thread by ID."""
        # Setup thread with assistant
        sample_thread.assistant = sample_assistant

        # Mock the result for thread retrieval
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_thread)

        # Set up session mock
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/thread/{sample_thread.id}/get-detail",
                headers={"x-user-id": "user-123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 200
            assert data["data"]["title"] == "Test Thread"
            assert data["data"]["assistant"]["name"] == "Test Assistant"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    async def test_get_thread_by_id_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
    ):
        """Test retrieval of a non-existent thread."""
        # Mock the result to return None (thread not found)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)

        # Set up session mock
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                "/api/v1/thread/nonexistent-thread/get-detail",
                headers={"x-user-id": "user-123"},
            )

            assert response.status_code == 200  # API returns 200 even for errors
            data = response.json()
            assert data["status"] == 404  # Check the status in the JSON response
            assert data["message"] == "Thread not found"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    async def test_get_thread_by_id_internal_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_thread_id: str,
    ):
        """Test get thread by ID with internal server error."""
        # Make sure the exception is raised during the session.execute call
        mock_session.execute.side_effect = Exception("Database error")

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/thread/{sample_thread_id}/get-detail",
                headers={"x-user-id": "user-123"},
            )

            # HTTP status is still 200, but the JSON response contains status 500
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 500
            assert "Internal server error" in data["message"]
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    # ================================
    # UPDATE THREAD TESTS
    # ================================

    async def test_update_thread_success(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_thread: Thread,
        update_thread_request: UpdateThreadRequest,
    ):
        """Test successful thread update."""
        # Mock the result for thread check
        mock_check_result = AsyncMock()
        mock_check_result.scalar_one_or_none = MagicMock(return_value=sample_thread)

        # Mock the result for update query
        mock_update_result = AsyncMock()

        # Mock the result for fetching updated thread
        mock_updated_result = AsyncMock()
        # Updated thread should have new title
        updated_thread = sample_thread
        updated_thread.title = update_thread_request.title
        mock_updated_result.scalar_one = MagicMock(return_value=updated_thread)

        # Set up session mock to return these results in sequence
        mock_session.execute.side_effect = [mock_check_result, mock_update_result, mock_updated_result]
        mock_session.commit = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.patch(
                f"/api/v1/thread/{sample_thread.id}/update",
                headers={"x-user-id": "user-123"},
                json=update_thread_request.model_dump(),
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 200
            assert data["data"]["title"] == "Updated Thread Title"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    async def test_update_thread_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        update_thread_request: UpdateThreadRequest,
    ):
        """Test update of non-existent thread."""
        # Mock the result to return None (thread not found)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)

        # Set up session mock
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.patch(
                "/api/v1/thread/nonexistent-thread/update",
                headers={"x-user-id": "user-123"},
                json=update_thread_request.model_dump(),
            )

            assert response.status_code == 200  # API returns 200 even for errors
            data = response.json()
            assert data["status"] == 404  # Check the status in the JSON response
            assert data["message"] == "Thread not found"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    async def test_update_thread_internal_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_thread_id: str,
        update_thread_request: UpdateThreadRequest,
    ):
        """Test update thread with internal server error."""
        # Make sure the exception is raised during the session.execute call
        mock_session.execute.side_effect = Exception("Database error")

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.patch(
                f"/api/v1/thread/{sample_thread_id}/update",
                headers={"x-user-id": "user-123"},
                json=update_thread_request.model_dump(),
            )

            # HTTP status is still 200, but the JSON response contains status 500
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 500
            assert "Internal server error" in data["message"]
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    # ================================
    # DELETE THREAD TESTS
    # ================================

    async def test_delete_thread_success(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_thread_id: str,
    ):
        """Test successful thread deletion."""
        # Mock the result for update query (soft delete)
        mock_result = AsyncMock()

        # Set up session mock
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.delete(
                f"/api/v1/thread/{sample_thread_id}/delete",
                headers={"x-user-id": "user-123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 200
            assert data["data"]["message"] == "Thread deleted successfully"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    async def test_delete_thread_internal_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_thread_id: str,
    ):
        """Test delete thread with internal server error."""
        # Make sure the exception is raised during the session.execute call
        mock_session.execute.side_effect = Exception("Database error")

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.delete(
                f"/api/v1/thread/{sample_thread_id}/delete",
                headers={"x-user-id": "user-123"},
            )

            # HTTP status is still 200, but the JSON response contains status 500
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 500
            assert "Internal server error" in data["message"]
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    # ================================
    # GENERATE TITLE TESTS
    # ================================

    async def test_generate_title_success_with_messages(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_thread: Thread,
    ):
        """Test successful title generation with messages."""
        # Mock the result for thread retrieval
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_thread)

        # Mock the updated thread
        mock_updated_result = AsyncMock()
        updated_thread = sample_thread
        updated_thread.title = "Generated Title"
        mock_updated_result.scalar_one = MagicMock(return_value=updated_thread)

        # Set up session mock to return these results in sequence
        mock_session.execute.side_effect = [mock_result, AsyncMock(), mock_updated_result]
        mock_session.commit = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            # Mock the checkpoint tuples function
            with patch("app.api.public.v1.thread.get_checkpoint_tuples") as mock_get_checkpoint_tuples:
                # Mock the return value for checkpoint tuples
                mock_get_checkpoint_tuples.return_value = ("checkpoint", "data")

                # Mock the convert function
                with patch("app.api.public.v1.thread.convert_checkpoint_tuple_to_messages") as mock_convert:
                    # Mock chat messages
                    mock_convert.return_value = [
                        ChatResponse(type="human", id="msg1", name="User", content="Hello"),
                        ChatResponse(type="ai", id="msg2", name="Assistant", content="Hi there"),
                    ]

                    # Mock the LLM chain construction and execution
                    with patch("app.api.public.v1.thread.get_llm_chat_model") as mock_get_llm:
                        # Create a mock LLM model that will be returned by get_llm_chat_model
                        mock_llm_model = MagicMock()
                        mock_get_llm.return_value = mock_llm_model

                        # Create a mock response with content attribute
                        mock_response = MagicMock()
                        mock_response.content = "Generated Title"

                        # Create mock chain
                        mock_chain = MagicMock()
                        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

                        # Make the | operator return our mock chain
                        mock_prompt_result = MagicMock()
                        mock_prompt_result.__or__.return_value = mock_chain

                        # Mock the PromptTemplate
                        with patch("app.api.public.v1.thread.PromptTemplate") as mock_prompt_class:
                            mock_prompt_class.return_value = mock_prompt_result

                            response = client.post(
                                f"/api/v1/thread/{sample_thread.id}/generate-title",
                                headers={"x-user-id": "user-123"},
                            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 200
            assert data["data"]["title"] == "Generated Title"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    async def test_generate_title_success_no_messages(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_thread: Thread,
    ):
        """Test successful title generation with no messages."""
        # Mock the result for thread retrieval
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_thread)

        # Mock the updated thread
        mock_updated_result = AsyncMock()
        updated_thread = sample_thread
        updated_thread.title = "New thread"
        mock_updated_result.scalar_one = MagicMock(return_value=updated_thread)

        # Set up session mock to return these results in sequence
        mock_session.execute.side_effect = [mock_result, AsyncMock(), mock_updated_result]
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            # Mock the checkpoint tuples function to return None (no messages)
            with patch("app.api.public.v1.thread.get_checkpoint_tuples") as mock_get_checkpoint_tuples:
                mock_get_checkpoint_tuples.return_value = None

                response = client.post(
                    f"/api/v1/thread/{sample_thread.id}/generate-title",
                    headers={"x-user-id": "user-123"},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 200
            assert data["data"]["title"] == "New thread"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    async def test_generate_title_thread_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
    ):
        """Test title generation for non-existent thread."""
        # Mock the result to return None (thread not found)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)

        # Set up session mock
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.post(
                "/api/v1/thread/nonexistent-thread/generate-title",
                headers={"x-user-id": "user-123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 404
            assert data["message"] == "Thread not found"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    # ================================
    # GET THREAD HISTORY TESTS
    # ================================

    async def test_get_thread_history_success(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_thread: Thread,
    ):
        """Test successful retrieval of thread history."""
        # Mock the result for thread retrieval
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_thread)

        # Set up session mock
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            # Mock the checkpoint tuples function
            with patch("app.api.public.v1.thread.get_checkpoint_tuples") as mock_get_checkpoint_tuples:
                # Mock the return value for checkpoint tuples
                mock_get_checkpoint_tuples.return_value = ("checkpoint", "data")

                # Mock the convert function
                with patch("app.api.public.v1.thread.convert_checkpoint_tuple_to_messages") as mock_convert:
                    # Mock chat messages
                    mock_messages = [
                        ChatResponse(type="human", id="msg1", name="User", content="Hello"),
                        ChatResponse(type="ai", id="msg2", name="Assistant", content="Hi there"),
                    ]
                    mock_convert.return_value = mock_messages

                    response = client.post(
                        f"/api/v1/thread/{sample_thread.id}/get-history",
                        headers={"x-user-id": "user-123"},
                    )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == 200
            assert data["data"]["threadId"] == sample_thread.id  # Using threadId (camelCase)
            assert data["data"]["assistantId"] == sample_thread.assistant_id  # Using assistantId (camelCase)
            assert len(data["data"]["messages"]) == 2
            assert data["data"]["messages"][0]["type"] == "human"
            assert data["data"]["messages"][0]["content"] == "Hello"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    async def test_get_thread_history_thread_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
    ):
        """Test thread history retrieval for non-existent thread."""
        # Mock the result to return None (thread not found)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)

        # Set up session mock
        mock_session.execute.return_value = mock_result

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.post(
                "/api/v1/thread/nonexistent-thread/get-history",
                headers={"x-user-id": "user-123"},
            )

            assert response.status_code == 200  # API returns 200 even for errors
            data = response.json()
            assert data["status"] == 404  # Check the status in the JSON response
            assert data["message"] == "Thread not found"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    # async def test_get_thread_history_no_messages(
    #     self,
    #     client: TestClient,
    #     mock_session: AsyncMock,
    #     sample_thread: Thread,
    # ):
    #     """Test thread history retrieval with no messages."""
    #     # Mock the result for thread retrieval
    #     mock_result = AsyncMock()
    #     mock_result.scalar_one_or_none = MagicMock(return_value=sample_thread)

    #     # Set up session mock
    #     mock_session.execute.return_value = mock_result

    #     # Override the dependency
    #     from app.core.db_session import get_async_session

    #     async def mock_get_async_session():
    #         yield mock_session

    #     app.dependency_overrides[get_async_session] = mock_get_async_session

    #     try:
    #         # Mock the checkpoint tuples function to return None (no messages)
    #         with patch("app.api.public.v1.thread.get_checkpoint_tuples") as mock_get_checkpoint_tuples:
    #             mock_get_checkpoint_tuples.return_value = None

    #             response = client.post(
    #                 f"/api/v1/thread/{sample_thread.id}/get-history",
    #                 headers={"x-user-id": "user-123"},
    #             )

    #         assert response.status_code == 404
    #         data = response.json()
    #         assert data["status"] == 404
    #         assert data["message"] == "Thread not found"
    #     finally:
    #         # Clean up the dependency override
    #         app.dependency_overrides.clear()

    # async def test_get_thread_history_internal_error(
    #     self,
    #     client: TestClient,
    #     mock_session: AsyncMock,
    #     sample_thread_id: str,
    # ):
    #     """Test get thread history with internal server error."""
    #     # Make sure the exception is raised during the session.execute call
    #     mock_session.execute.side_effect = Exception("Database error")

    #     # Override the dependency
    #     from app.core.db_session import get_async_session

    #     async def mock_get_async_session():
    #         yield mock_session

    #     app.dependency_overrides[get_async_session] = mock_get_async_session

    #     try:
    #         response = client.post(
    #             f"/api/v1/thread/{sample_thread_id}/get-history",
    #             headers={"x-user-id": "user-123"},
    #         )

    #         # We should get a 500 status code when there's an internal error
    #         assert response.status_code == 500
    #     finally:
    #         # Clean up the dependency override
    #         app.dependency_overrides.clear()
