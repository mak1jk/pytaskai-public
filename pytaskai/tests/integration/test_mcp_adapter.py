"""
Integration tests for PyTaskAI MCP adapter layer.

These tests verify the integration between MCP tools and the application layer,
ensuring that the adapter correctly translates MCP requests to use cases
and maps responses back to MCP format.
"""

from datetime import datetime
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP

from pytaskai.adapters.mcp.dependency_injection import MCPContainer
from pytaskai.adapters.mcp.task_tools import TaskMCPTools
from pytaskai.application.dto.task_dto import (
    TaskCreateDTO,
    TaskResponseDTO,
    TaskUpdateDTO,
)


class MockTaskUseCase:
    """Mock task management use case for testing."""

    def __init__(self):
        self.tasks_db = {}
        self.next_id = 1

    async def create_task(self, task_data: TaskCreateDTO) -> TaskResponseDTO:
        """Mock create task."""
        task_id = f"task_{self.next_id}"
        self.next_id += 1

        task_dto = TaskResponseDTO(
            id=task_id,
            title=task_data.title,
            external_url=None,
            project=task_data.project,
            task_type=task_data.task_type,
            status=task_data.status,
            assignee=task_data.assignee,
            parent_id=task_data.parent_id,
            tags=task_data.tags or [],
            priority=task_data.priority,
            start_at=task_data.start_at,
            due_at=task_data.due_at,
            size=task_data.size,
            description=task_data.description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.tasks_db[task_id] = task_dto
        return task_dto

    async def get_task(self, task_id: str) -> Optional[TaskResponseDTO]:
        """Mock get task."""
        return self.tasks_db.get(task_id)

    async def list_tasks(self, filters=None) -> List[TaskResponseDTO]:
        """Mock list tasks."""
        tasks = list(self.tasks_db.values())

        # Apply simple filtering for tests
        if filters:
            if filters.status:
                tasks = [t for t in tasks if t.status == filters.status]
            if filters.assignee:
                tasks = [t for t in tasks if t.assignee == filters.assignee]

        return tasks

    async def update_task(self, update_data: TaskUpdateDTO) -> TaskResponseDTO:
        """Mock update task."""
        task = self.tasks_db.get(update_data.task_id)
        if not task:
            raise ValueError(f"Task {update_data.task_id} not found")

        # Create updated task
        updated_task = TaskResponseDTO(
            id=task.id,
            title=update_data.title or task.title,
            external_url=task.external_url,
            project=task.project,
            task_type=task.task_type,
            status=update_data.status or task.status,
            assignee=(
                update_data.assignee
                if update_data.assignee is not None
                else task.assignee
            ),
            parent_id=task.parent_id,
            tags=update_data.tags if update_data.tags is not None else task.tags,
            priority=(
                update_data.priority
                if update_data.priority is not None
                else task.priority
            ),
            start_at=(
                update_data.start_at
                if update_data.start_at is not None
                else task.start_at
            ),
            due_at=(
                update_data.due_at if update_data.due_at is not None else task.due_at
            ),
            size=update_data.size if update_data.size is not None else task.size,
            description=(
                update_data.description
                if update_data.description is not None
                else task.description
            ),
            created_at=task.created_at,
            updated_at=datetime.now(),
        )

        self.tasks_db[task.id] = updated_task
        return updated_task

    async def delete_task(self, task_id: str) -> bool:
        """Mock delete task."""
        if task_id not in self.tasks_db:
            raise ValueError(f"Task {task_id} not found")

        del self.tasks_db[task_id]
        return True


@pytest.fixture
def mock_container():
    """Create mock MCP container for testing."""
    container = MagicMock(spec=MCPContainer)

    # Mock application container
    app_container = MagicMock()
    mock_use_case = MockTaskUseCase()
    app_container.task_management_use_case = mock_use_case
    app_container.has_ai_services.return_value = False

    container.application_container = app_container

    return container


@pytest.fixture
def mock_mcp_app():
    """Create mock FastMCP app for testing."""
    app = MagicMock(spec=FastMCP)
    return app


@pytest.fixture
def task_tools(mock_container, mock_mcp_app):
    """Create TaskMCPTools instance with mock container."""
    return TaskMCPTools(mock_container, mock_mcp_app)


class TestTaskMCPTools:
    """Test suite for Task MCP Tools."""

    @pytest.mark.asyncio
    async def test_add_task_success(self, task_tools):
        """Test successful task creation."""
        result = await task_tools.add_task(
            title="Test Task",
            project="Test Project",
            description="Test description",
            priority="High",
        )

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["title"] == "Test Task"
        assert result["data"]["project"] == "Test Project"
        assert result["data"]["priority"] == "High"
        assert result["data"]["id"].startswith("task_")

    @pytest.mark.asyncio
    async def test_add_task_validation_error(self, task_tools):
        """Test task creation with validation error."""
        with pytest.raises(Exception):
            await task_tools.add_task(title="")  # Empty title should fail

    @pytest.mark.asyncio
    async def test_get_task_success(self, task_tools):
        """Test successful task retrieval."""
        # First create a task
        create_result = await task_tools.add_task(
            title="Test Task", project="Test Project"
        )
        task_id = create_result["data"]["id"]

        # Then get it
        result = await task_tools.get_task(task_id)

        assert result["success"] is True
        assert result["data"]["id"] == task_id
        assert result["data"]["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, task_tools):
        """Test task retrieval with non-existent ID."""
        with pytest.raises(Exception):
            await task_tools.get_task("nonexistent_id")

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, task_tools):
        """Test listing tasks when none exist."""
        result = await task_tools.list_tasks()

        assert result["success"] is True
        assert result["data"]["tasks"] == []
        assert result["data"]["count"] == 0

    @pytest.mark.asyncio
    async def test_list_tasks_with_data(self, task_tools):
        """Test listing tasks with existing data."""
        # Create some tasks
        await task_tools.add_task(title="Task 1", project="Project A")
        await task_tools.add_task(title="Task 2", project="Project B")

        result = await task_tools.list_tasks()

        assert result["success"] is True
        assert result["data"]["count"] == 2
        assert len(result["data"]["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self, task_tools):
        """Test listing tasks with filters."""
        # Create tasks with different statuses
        await task_tools.add_task(title="Task 1", status="Todo")
        await task_tools.add_task(title="Task 2", status="Done")

        # Filter by status
        result = await task_tools.list_tasks(status="Todo")

        assert result["success"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["tasks"][0]["status"] == "Todo"

    @pytest.mark.asyncio
    async def test_update_task_success(self, task_tools):
        """Test successful task update."""
        # Create a task
        create_result = await task_tools.add_task(title="Original Title", status="Todo")
        task_id = create_result["data"]["id"]

        # Update it
        result = await task_tools.update_task(
            task_id=task_id, title="Updated Title", status="In Progress"
        )

        assert result["success"] is True
        assert result["data"]["title"] == "Updated Title"
        assert result["data"]["status"] == "In Progress"

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, task_tools):
        """Test task update with non-existent ID."""
        with pytest.raises(Exception):
            await task_tools.update_task(task_id="nonexistent_id", title="New Title")

    @pytest.mark.asyncio
    async def test_delete_task_success(self, task_tools):
        """Test successful task deletion."""
        # Create a task
        create_result = await task_tools.add_task(title="Task to Delete")
        task_id = create_result["data"]["id"]

        # Delete it
        result = await task_tools.delete_task(task_id)

        assert result["success"] is True
        assert result["data"]["deleted"] is True
        assert result["data"]["task_id"] == task_id

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, task_tools):
        """Test task deletion with non-existent ID."""
        with pytest.raises(Exception):
            await task_tools.delete_task("nonexistent_id")

    @pytest.mark.asyncio
    async def test_generate_subtasks_no_ai(self, task_tools):
        """Test subtask generation without AI services."""
        # Create a parent task
        create_result = await task_tools.add_task(title="Parent Task")
        task_id = create_result["data"]["id"]

        # Try to generate subtasks
        result = await task_tools.generate_subtasks(task_id)

        assert result["success"] is True
        assert result["data"]["generated_subtasks"] == []
        assert "AI services not configured" in result["data"]["message"]

    @pytest.mark.asyncio
    async def test_task_creation_with_tags(self, task_tools):
        """Test task creation with tags."""
        result = await task_tools.add_task(
            title="Tagged Task", tags=["urgent", "frontend", "bug-fix"]
        )

        assert result["success"] is True
        assert result["data"]["tags"] == ["urgent", "frontend", "bug-fix"]

    @pytest.mark.asyncio
    async def test_task_creation_with_dates(self, task_tools):
        """Test task creation with start and due dates."""
        result = await task_tools.add_task(
            title="Scheduled Task",
            start_at="2024-01-01T09:00:00",
            due_at="2024-01-31T17:00:00",
        )

        assert result["success"] is True
        assert result["data"]["start_at"] is not None
        assert result["data"]["due_at"] is not None

    @pytest.mark.asyncio
    async def test_priority_validation(self, task_tools):
        """Test priority field validation."""
        # Valid priority should work
        result = await task_tools.add_task(title="High Priority Task", priority="High")
        assert result["success"] is True

        # Invalid priority should fail
        with pytest.raises(Exception):
            await task_tools.add_task(
                title="Invalid Priority Task", priority="InvalidPriority"
            )


class TestMCPErrorHandling:
    """Test suite for MCP error handling."""

    @pytest.mark.asyncio
    async def test_missing_required_field(self, task_tools):
        """Test error handling for missing required fields."""
        with pytest.raises(Exception):
            await task_tools.get_task("")  # Empty task_id

    @pytest.mark.asyncio
    async def test_invalid_field_type(self, task_tools):
        """Test error handling for invalid field types."""
        with pytest.raises(Exception):
            await task_tools.add_task(
                title="Test Task",
                tags="invalid_tags_type",  # Should be list, not string
            )


class TestMCPIntegration:
    """Test suite for MCP integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_task_lifecycle(self, task_tools):
        """Test complete task lifecycle through MCP tools."""
        # Create task
        create_result = await task_tools.add_task(
            title="Lifecycle Test Task",
            project="Test Project",
            priority="Medium",
            tags=["test"],
        )

        task_id = create_result["data"]["id"]
        assert create_result["success"] is True

        # Get task
        get_result = await task_tools.get_task(task_id)
        assert get_result["success"] is True
        assert get_result["data"]["title"] == "Lifecycle Test Task"

        # Update task
        update_result = await task_tools.update_task(
            task_id=task_id, status="In Progress", assignee="test@example.com"
        )
        assert update_result["success"] is True
        assert update_result["data"]["status"] == "In Progress"

        # List tasks (should include our task)
        list_result = await task_tools.list_tasks()
        assert list_result["success"] is True
        assert list_result["data"]["count"] >= 1

        # Delete task
        delete_result = await task_tools.delete_task(task_id)
        assert delete_result["success"] is True

        # Verify task is gone
        with pytest.raises(Exception):
            await task_tools.get_task(task_id)
