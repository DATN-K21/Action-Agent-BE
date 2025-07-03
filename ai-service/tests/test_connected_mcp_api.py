"""
Unit tests for connected MCP API endpoints.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from langchain.tools.base import BaseTool
from sqlalchemy.exc import SQLAlchemyError

from app.core.enums import McpTransport
from app.core.models import ToolInfo
from app.db_models.connected_mcp import ConnectedMcp
from app.main import app


class TestConnectedMcpApiEndpoints:
    """Test class for connected MCP API endpoints."""

    @pytest.fixture
    def sample_user_id(self) -> str:
        """Generate sample user ID."""
        return "user-123"

    @pytest.fixture
    def sample_connected_mcp_id(self) -> str:
        """Generate sample connected MCP ID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def sample_connected_mcp(self, sample_user_id, sample_connected_mcp_id) -> ConnectedMcp:
        """Create sample connected MCP for testing."""
        return ConnectedMcp(
            id=sample_connected_mcp_id,
            user_id=sample_user_id,
            mcp_name="Sample MCP",
            url="https://sample-mcp.com/api",
            transport=McpTransport.STREAMABLE_HTTP,
            description="A sample MCP for testing",
            created_at=datetime.utcnow(),
            is_deleted=False,
        )

    @pytest.fixture
    def sample_connected_mcps(self, sample_user_id) -> list[ConnectedMcp]:
        """Create a list of sample connected MCPs for testing."""
        return [
            ConnectedMcp(
                id=str(uuid.uuid4()),
                user_id=sample_user_id,
                mcp_name="Sample MCP 1",
                url="https://sample-mcp1.com/api",
                transport=McpTransport.STREAMABLE_HTTP,
                description="A sample MCP 1 for testing",
                created_at=datetime.utcnow(),
                is_deleted=False,
            ),
            ConnectedMcp(
                id=str(uuid.uuid4()),
                user_id=sample_user_id,
                mcp_name="Sample MCP 2",
                url="https://sample-mcp2.com/api",
                transport=McpTransport.SSE,
                description="A sample MCP 2 for testing",
                created_at=datetime.utcnow(),
                is_deleted=False,
            ),
            ConnectedMcp(
                id=str(uuid.uuid4()),
                user_id=sample_user_id,
                mcp_name="Sample MCP 3",
                url="https://sample-mcp3.com/api",
                transport=McpTransport.WEBSOCKET,
                description="A sample MCP 3 for testing",
                created_at=datetime.utcnow(),
                is_deleted=False,
            ),
        ]

    # Simple class for wrapping ToolInfo for testing
    class ToolInfoWrapper:
        def __init__(self, tool_info, name, parameters):
            self.tool_info = tool_info
            self.name = name
            self.parameters = parameters
            self.description = tool_info.description

    @pytest.fixture
    def sample_tool_infos(self) -> list:
        """Create sample tool information for testing."""
        # Create mock BaseTool instances
        tool1 = MagicMock(spec=BaseTool)
        tool1.name = "tool1"
        tool1.description = "Sample tool 1"

        tool2 = MagicMock(spec=BaseTool)
        tool2.name = "tool2"
        tool2.description = "Sample tool 2"

        # Create ToolInfo objects for test compatibility
        info1 = ToolInfo(tool=tool1, description="Sample tool 1", input_parameters={"name": "param1", "type": "string", "description": "Parameter 1"})

        info2 = ToolInfo(
            tool=tool2,
            description="Sample tool 2",
            input_parameters={
                "parameters": [
                    {"name": "param1", "type": "string", "description": "Parameter 1"},
                    {"name": "param2", "type": "number", "description": "Parameter 2"},
                ]
            },
        )

        return [info1, info2]

    # ================================
    # GET ALL CONNECTED MCPS TESTS
    # ================================

    async def test_get_all_connected_mcps_as_regular_user(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcps: list[ConnectedMcp],
    ):
        """Test getting all connected MCPs as a regular user."""
        # Mock the count result
        count_result = AsyncMock()
        count_result.scalar_one = MagicMock(return_value=len(sample_connected_mcps))

        # Mock the MCPs result
        mcps_result = AsyncMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=sample_connected_mcps)
        mcps_result.scalars = MagicMock(return_value=scalars_mock)

        # Configure mock session to return different results for different calls
        mock_session.execute = AsyncMock(side_effect=[count_result, mcps_result])

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                "/api/v1/mcp/get-all",
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
            assert len(data["connectedMcps"]) == len(sample_connected_mcps)

            # Verify the MCPs data
            for i, mcp in enumerate(data["connectedMcps"]):
                assert mcp["mcpName"] == sample_connected_mcps[i].mcp_name
                assert mcp["url"] == sample_connected_mcps[i].url
                assert mcp["transport"] == sample_connected_mcps[i].transport.value

        finally:
            app.dependency_overrides.clear()

    async def test_get_all_connected_mcps_as_admin(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcps: list[ConnectedMcp],
    ):
        """Test getting all connected MCPs as an admin user."""
        # Mock the count result
        count_result = AsyncMock()
        count_result.scalar_one = MagicMock(return_value=len(sample_connected_mcps))

        # Mock the MCPs result
        mcps_result = AsyncMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=sample_connected_mcps)
        mcps_result.scalars = MagicMock(return_value=scalars_mock)

        # Configure mock session to return different results for different calls
        mock_session.execute = AsyncMock(side_effect=[count_result, mcps_result])

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                "/api/v1/mcp/get-all",
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
            assert len(data["connectedMcps"]) == len(sample_connected_mcps)

        finally:
            app.dependency_overrides.clear()

    async def test_get_all_connected_mcps_empty_result(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
    ):
        """Test getting all connected MCPs when no MCPs exist."""
        # Mock the count result
        count_result = AsyncMock()
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
                "/api/v1/mcp/get-all",
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
            assert len(data["connectedMcps"]) == 0

        finally:
            app.dependency_overrides.clear()

    async def test_get_all_connected_mcps_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
    ):
        """Test getting all connected MCPs when a database error occurs."""
        # Mock the database error
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                "/api/v1/mcp/get-all",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                params={"page_number": 1, "max_per_page": 10},
            )

            # Check for error response
            assert response.status_code == 500
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Database error occurred"

        finally:
            app.dependency_overrides.clear()

    # ================================
    # GET CONNECTED MCP DETAIL TESTS
    # ================================

    async def test_get_connected_mcp_detail_as_regular_user(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp: ConnectedMcp,
        sample_connected_mcp_id: str,
    ):
        """Test getting a specific connected MCP detail as a regular user."""
        # Mock the MCP result
        mcp_result = AsyncMock()
        mcp_result.scalar_one_or_none = MagicMock(return_value=sample_connected_mcp)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=mcp_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/mcp/{sample_connected_mcp_id}/get-detail",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data

            # Verify the MCP data
            data = response_data["data"]
            assert data["id"] == sample_connected_mcp.id
            assert data["userId"] == sample_connected_mcp.user_id
            assert data["mcpName"] == sample_connected_mcp.mcp_name
            assert data["url"] == sample_connected_mcp.url
            assert data["transport"] == sample_connected_mcp.transport.value
            assert data["description"] == sample_connected_mcp.description

        finally:
            app.dependency_overrides.clear()

    async def test_get_connected_mcp_detail_as_admin(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp: ConnectedMcp,
        sample_connected_mcp_id: str,
    ):
        """Test getting a specific connected MCP detail as an admin user."""
        # Mock the MCP result
        mcp_result = AsyncMock()
        mcp_result.scalar_one_or_none = MagicMock(return_value=sample_connected_mcp)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=mcp_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/mcp/{sample_connected_mcp_id}/get-detail",
                headers={"x-user-id": "admin-user", "x-user-role": "admin"},
            )

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data

            # Verify the MCP data
            data = response_data["data"]
            assert data["id"] == sample_connected_mcp.id
            assert data["mcpName"] == sample_connected_mcp.mcp_name

        finally:
            app.dependency_overrides.clear()

    async def test_get_connected_mcp_detail_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp_id: str,
    ):
        """Test getting a connected MCP that doesn't exist."""
        # Mock the MCP result (not found)
        mcp_result = AsyncMock()
        mcp_result.scalar_one_or_none = MagicMock(return_value=None)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=mcp_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/mcp/{sample_connected_mcp_id}/get-detail",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 404
            response_data = response.json()

            # Verify the response structure indicates a not found error
            assert response_data["status"] == 404
            assert response_data["message"] == "Connected MCP not found."

        finally:
            app.dependency_overrides.clear()

    async def test_get_connected_mcp_detail_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp_id: str,
    ):
        """Test getting a connected MCP when a database error occurs."""
        # Mock the database error
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/mcp/{sample_connected_mcp_id}/get-detail",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 500
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Database error occurred"

        finally:
            app.dependency_overrides.clear()

    # ================================
    # CREATE CONNECTED MCP TESTS
    # ================================

    async def test_create_connected_mcp_success(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp: ConnectedMcp,
    ):
        """Test creating a new connected MCP successfully."""
        # Setup mock session behavior for add, commit, refresh
        mock_session.add = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            # Create request data
            request_data = {
                "mcpName": "New MCP",
                "url": "https://new-mcp.com/api",
                "transport": "streamable_http",
                "description": "A new MCP for testing",
            }

            # Mock the behavior of refresh to set ID and created_at fields
            def refresh_side_effect(obj):
                obj.id = str(uuid.uuid4())
                obj.created_at = datetime.utcnow()
                return None

            mock_session.refresh.side_effect = refresh_side_effect

            response = client.post("/api/v1/mcp/create", headers={"x-user-id": sample_user_id, "x-user-role": "user"}, json=request_data)

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data

            # Verify the created MCP data
            data = response_data["data"]
            assert "id" in data
            assert data["userId"] == sample_user_id
            assert data["mcpName"] == request_data["mcpName"]
            assert data["url"] == request_data["url"]
            assert data["transport"] == request_data["transport"]
            assert data["description"] == request_data["description"]

            # Verify mock session methods were called
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    async def test_create_connected_mcp_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
    ):
        """Test creating a connected MCP when a database error occurs."""
        # Mock the database error
        mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Database error"))
        mock_session.rollback = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            # Create request data
            request_data = {
                "mcpName": "New MCP",
                "url": "https://new-mcp.com/api",
                "transport": "streamable_http",
                "description": "A new MCP for testing",
            }

            response = client.post("/api/v1/mcp/create", headers={"x-user-id": sample_user_id, "x-user-role": "user"}, json=request_data)

            # Check for error response
            assert response.status_code == 500
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Database error occurred"

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    # ================================
    # UPDATE CONNECTED MCP TESTS
    # ================================

    async def test_update_connected_mcp_success(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp: ConnectedMcp,
        sample_connected_mcp_id: str,
    ):
        """Test updating a connected MCP successfully."""
        # Mock the update result
        update_result = AsyncMock()
        update_result.rowcount = 1

        # Mock the fetch result
        fetch_result = AsyncMock()

        # Create a copy of the sample MCP with updated values
        updated_mcp = ConnectedMcp(
            id=sample_connected_mcp.id,
            user_id=sample_connected_mcp.user_id,
            mcp_name="Updated MCP Name",
            url="https://updated-url.com/api",
            transport=McpTransport.SSE,
            description="Updated description",
            created_at=sample_connected_mcp.created_at,
            is_deleted=False,
        )

        fetch_result.scalar_one_or_none = MagicMock(return_value=updated_mcp)

        # Configure mock session to return different results for different calls
        mock_session.execute = AsyncMock(side_effect=[update_result, fetch_result])
        mock_session.commit = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            # Create update request data
            update_data = {
                "mcpName": "Updated MCP Name",
                "url": "https://updated-url.com/api",
                "transport": "sse",
                "description": "Updated description",
            }

            response = client.patch(
                f"/api/v1/mcp/{sample_connected_mcp_id}/update", headers={"x-user-id": sample_user_id, "x-user-role": "user"}, json=update_data
            )

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data

            # Verify the updated MCP data
            data = response_data["data"]
            assert data["id"] == sample_connected_mcp_id
            assert data["mcpName"] == update_data["mcpName"]
            assert data["url"] == update_data["url"]
            assert data["transport"] == update_data["transport"]
            assert data["description"] == update_data["description"]

        finally:
            app.dependency_overrides.clear()

    async def test_update_connected_mcp_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp_id: str,
    ):
        """Test updating a connected MCP that doesn't exist."""
        # Mock the update result (no rows affected)
        update_result = AsyncMock()
        update_result.rowcount = 0

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=update_result)
        mock_session.commit = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            # Create update request data
            update_data = {
                "mcpName": "Updated MCP Name",
                "url": "https://updated-url.com/api",
                "transport": "sse",
                "description": "Updated description",
            }

            response = client.patch(
                f"/api/v1/mcp/{sample_connected_mcp_id}/update", headers={"x-user-id": sample_user_id, "x-user-role": "user"}, json=update_data
            )

            # Check for error response
            assert response.status_code == 404
            response_data = response.json()

            # Verify the response structure indicates a not found error
            assert response_data["status"] == 404
            assert response_data["message"] == "Connected MCP not found"

        finally:
            app.dependency_overrides.clear()

    async def test_update_connected_mcp_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp_id: str,
    ):
        """Test updating a connected MCP when a database error occurs."""
        # Mock the database error
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))
        mock_session.rollback = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            # Create update request data
            update_data = {
                "mcpName": "Updated MCP Name",
                "url": "https://updated-url.com/api",
                "transport": "sse",
                "description": "Updated description",
            }

            response = client.patch(
                f"/api/v1/mcp/{sample_connected_mcp_id}/update", headers={"x-user-id": sample_user_id, "x-user-role": "user"}, json=update_data
            )

            # Check for error response
            assert response.status_code == 500
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Database error occurred"

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    # ================================
    # DELETE CONNECTED MCP TESTS
    # ================================

    async def test_delete_connected_mcp_success(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp_id: str,
    ):
        """Test deleting a connected MCP successfully."""
        # Mock the delete operation
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.delete(
                f"/api/v1/mcp/{sample_connected_mcp_id}/delete",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for successful response
            assert response.status_code == 200
            response_data = response.json()

            # Verify the response structure
            assert response_data["status"] == 200
            assert "data" in response_data
            assert response_data["data"]["message"] == "Connected MCP deleted successfully"

            # Verify mock session methods were called
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    async def test_delete_connected_mcp_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp_id: str,
    ):
        """Test deleting a connected MCP when a database error occurs."""
        # Mock the database error
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))
        mock_session.rollback = AsyncMock()

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.delete(
                f"/api/v1/mcp/{sample_connected_mcp_id}/delete",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 500
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Database error occurred"

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    # ================================
    # GET TOOL INFOS TESTS
    # ================================

    async def test_get_tool_infos_success(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp: ConnectedMcp,
        sample_connected_mcp_id: str,
        sample_tool_infos: list,
    ):
        """Test getting tool infos successfully."""
        # Mock the MCP result
        mcp_result = AsyncMock()
        mcp_result.scalar_one_or_none = MagicMock(return_value=sample_connected_mcp)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=mcp_result)

        # Mock the McpService.aget_mcp_tool_info method
        from unittest.mock import patch

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        with patch("app.services.mcps.mcp_service.McpService.aget_mcp_tool_info", new_callable=AsyncMock) as mock_get_tool_info:
            # Configure the mock to return sample tool infos
            mock_get_tool_info.return_value = sample_tool_infos

            try:
                response = client.get(
                    f"/api/v1/mcp/{sample_connected_mcp_id}/tool-infos",
                    headers={"x-user-id": sample_user_id, "x-user-role": "user"},
                )

                # Check for successful response
                assert response.status_code == 200
                response_data = response.json()

                # Verify the response structure
                assert response_data["status"] == 200
                assert "data" in response_data
                assert "toolInfos" in response_data["data"]

                # Verify the tool infos data
                tool_infos = response_data["data"]["toolInfos"]
                assert len(tool_infos) == len(sample_tool_infos)

                # Verify each tool info
                for i, tool_info in enumerate(tool_infos):
                    assert tool_info["description"] == sample_tool_infos[i].description
                    if sample_tool_infos[i].input_parameters:
                        if "parameters" in sample_tool_infos[i].input_parameters:
                            assert len(tool_info["input_parameters"]["parameters"]) == len(sample_tool_infos[i].input_parameters["parameters"])

            finally:
                app.dependency_overrides.clear()

    async def test_get_tool_infos_mcp_not_found(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp_id: str,
    ):
        """Test getting tool infos for a connected MCP that doesn't exist."""
        # Mock the MCP result (not found)
        mcp_result = AsyncMock()
        mcp_result.scalar_one_or_none = MagicMock(return_value=None)

        # Configure mock session
        mock_session.execute = AsyncMock(return_value=mcp_result)

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/mcp/{sample_connected_mcp_id}/tool-infos",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 404
            response_data = response.json()

            # Verify the response structure indicates a not found error
            assert response_data["status"] == 404
            assert response_data["message"] == "Connected MCP not found."

        finally:
            app.dependency_overrides.clear()

    async def test_get_tool_infos_database_error(
        self,
        client: TestClient,
        mock_session: AsyncMock,
        sample_user_id: str,
        sample_connected_mcp_id: str,
    ):
        """Test getting tool infos when a database error occurs."""
        # Mock the database error
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))

        # Override the dependency
        from app.core.db_session import get_async_session

        async def mock_get_async_session():
            yield mock_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = client.get(
                f"/api/v1/mcp/{sample_connected_mcp_id}/tool-infos",
                headers={"x-user-id": sample_user_id, "x-user-role": "user"},
            )

            # Check for error response
            assert response.status_code == 500
            response_data = response.json()

            # Verify the response structure indicates an error
            assert response_data["status"] == 500
            assert response_data["message"] == "Database error occurred"

        finally:
            app.dependency_overrides.clear()
