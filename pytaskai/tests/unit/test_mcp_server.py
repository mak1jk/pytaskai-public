"""
Unit tests for MCP server components.

These tests focus on testing individual components of the MCP server
without requiring full server initialization.
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pytaskai.adapters.mcp.dependency_injection import (
    MCPContainer,
    create_mcp_container,
)
from pytaskai.adapters.mcp.mcp_server import PyTaskAIMCPServer


class TestMCPContainer:
    """Test suite for MCPContainer."""

    def test_container_initialization(self):
        """Test basic container initialization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            container = MCPContainer(database_path=tmp_path)
            assert container is not None
            assert container._database_path == tmp_path
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_default_database_path(self):
        """Test default database path generation."""
        path = MCPContainer._get_default_database_path()
        assert path.endswith("tasks.db")
        assert ".pytaskai" in path

    def test_service_status(self):
        """Test service status reporting."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            container = MCPContainer(database_path=tmp_path)
            status = container.get_service_status()

            assert isinstance(status, dict)
            assert "database" in status
            assert "ai_generation" in status
            assert "notification" in status
            assert status["ai_generation"] is False  # No AI services configured
            assert status["notification"] is False  # No notification service configured
        finally:
            container.close_database()
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_create_mcp_container_factory(self):
        """Test factory function for creating MCP container."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            container = create_mcp_container(database_path=tmp_path)
            assert container is not None
            assert container.is_ready()
        finally:
            container.close_database()
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestPyTaskAIMCPServer:
    """Test suite for PyTaskAIMCPServer."""

    def test_server_initialization_properties(self):
        """Test server initialization and properties."""
        server = PyTaskAIMCPServer(debug=True)

        assert server._debug is True
        assert server.is_initialized is False
        assert server.service_status == {"initialized": False}

    @pytest.mark.asyncio
    async def test_server_initialization_failure_handling(self):
        """Test server handles initialization failures gracefully."""
        server = PyTaskAIMCPServer(database_path="/nonexistent/path/test.db")

        with pytest.raises(Exception):
            await server.initialize()

    @pytest.mark.asyncio
    async def test_server_shutdown_without_initialization(self):
        """Test server can be shut down even without initialization."""
        server = PyTaskAIMCPServer()

        # Should not raise an exception
        await server.shutdown()

    @pytest.mark.asyncio
    async def test_server_run_without_initialization(self):
        """Test server raises error when run without initialization."""
        server = PyTaskAIMCPServer()

        with pytest.raises(RuntimeError, match="MCP server not initialized"):
            await server.run()

    @pytest.mark.asyncio
    async def test_create_server_function(self):
        """Test create_server factory function with mocked dependencies."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Import here to avoid circular imports in test discovery
            from pytaskai.adapters.mcp.mcp_server import create_server

            server = await create_server(database_path=tmp_path, debug=True)

            assert server is not None
            assert server.is_initialized is True
            assert server._debug is True

            await server.shutdown()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestMCPErrorHandlers:
    """Test suite for MCP error handling utilities."""

    def test_error_mapper_validation_error(self):
        """Test error mapping for validation errors."""
        from pytaskai.adapters.mcp.dto_mappers import MCPErrorMapper

        response = MCPErrorMapper.map_validation_error_to_response(
            "title", "Field cannot be empty"
        )

        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert "title" in response["error"]["message"]
        assert response["error"]["details"]["field"] == "title"

    def test_error_handler_validate_required_fields_success(self):
        """Test successful validation of required fields."""
        from pytaskai.adapters.mcp.error_handlers import MCPErrorHandler

        data = {"title": "Test Task", "project": "Test Project"}
        required = ["title", "project"]

        # Should not raise exception
        MCPErrorHandler.validate_required_fields(data, required)

    def test_error_handler_validate_field_type_success(self):
        """Test successful field type validation."""
        from pytaskai.adapters.mcp.error_handlers import MCPErrorHandler

        data = {"priority": "High"}  # Correct string type

        # Should not raise exception
        MCPErrorHandler.validate_field_type(data, "priority", str)

    def test_error_handler_validate_field_choices_success(self):
        """Test successful field choices validation."""
        from pytaskai.adapters.mcp.error_handlers import MCPErrorHandler

        data = {"priority": "High"}  # Valid choice
        choices = ["Low", "Medium", "High", "Critical"]

        # Should not raise exception
        MCPErrorHandler.validate_field_choices(data, "priority", choices)

    def test_error_handler_create_success_response(self):
        """Test success response creation."""
        from pytaskai.adapters.mcp.error_handlers import MCPErrorHandler

        data = {"id": "task123", "title": "Test Task"}
        response = MCPErrorHandler.create_success_response(data, "Task created")

        assert response["success"] is True
        assert response["message"] == "Task created"
        assert response["data"] == data

    def test_error_handler_log_tool_execution(self):
        """Test tool execution logging."""
        from pytaskai.adapters.mcp.error_handlers import MCPErrorHandler

        # Should not raise an exception
        MCPErrorHandler.log_tool_execution("test_tool", {"param": "value"})


class TestDTOMappers:
    """Test suite for DTO mapping utilities."""

    def test_datetime_parsing(self):
        """Test datetime parsing in mappers."""
        from pytaskai.adapters.mcp.dto_mappers import MCPTaskMapper

        # Test ISO format
        dt = MCPTaskMapper._parse_datetime("2024-01-01T09:00:00")
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1

        # Test with Z suffix
        dt_z = MCPTaskMapper._parse_datetime("2024-01-01T09:00:00Z")
        assert dt_z.year == 2024

    def test_datetime_formatting(self):
        """Test datetime formatting in mappers."""
        from datetime import datetime

        from pytaskai.adapters.mcp.dto_mappers import MCPTaskMapper

        dt = datetime(2024, 1, 1, 9, 0, 0)
        formatted = MCPTaskMapper._format_datetime(dt)
        assert "2024-01-01T09:00:00" in formatted

        # Test None handling
        assert MCPTaskMapper._format_datetime(None) is None

    def test_task_create_dto_mapping(self):
        """Test task creation DTO mapping."""
        from pytaskai.adapters.mcp.dto_mappers import MCPTaskMapper

        request_data = {
            "title": "Test Task",
            "project": "Test Project",
            "tags": ["tag1", "tag2"],
            "priority": "High",
        }

        dto = MCPTaskMapper.map_create_request_to_dto(request_data)

        assert dto.title == "Test Task"
        assert dto.project == "Test Project"
        assert dto.tags == ["tag1", "tag2"]
        assert dto.priority == "High"

    def test_task_update_dto_mapping(self):
        """Test task update DTO mapping."""
        from pytaskai.adapters.mcp.dto_mappers import MCPTaskMapper

        request_data = {"task_id": "task123", "title": "Updated Task", "status": "Done"}

        dto = MCPTaskMapper.map_update_request_to_dto(request_data)

        assert dto.task_id == "task123"
        assert dto.title == "Updated Task"
        assert dto.status == "Done"

    def test_error_mapping(self):
        """Test error response mapping."""
        from pytaskai.adapters.mcp.dto_mappers import MCPErrorMapper

        error = ValueError("Test error")
        response = MCPErrorMapper.map_error_to_response(error, "TEST_ERROR")

        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["message"] == "Test error"
        assert response["error"]["details"]["type"] == "ValueError"
