"""
Unit tests for PyTaskAI domain services.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from pytaskai.domain.entities.task import Document, Task
from pytaskai.domain.repositories.task_repository import TaskManagementRepository
from pytaskai.domain.services.task_service import (
    DocumentService,
    TaskService,
    WorkspaceService,
)
from pytaskai.domain.value_objects.task_types import (
    ProjectName,
    TaskConfig,
    TaskId,
    TaskPriority,
    TaskStatus,
    TaskType,
)


@pytest.mark.asyncio
class TestTaskService:
    """Test TaskService domain service."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.mock_repo = MagicMock(spec=TaskManagementRepository)
        self.task_service = TaskService(self.mock_repo)

    @pytest.fixture
    def sample_task(self) -> Task:
        """Create a sample task for testing."""
        return Task(
            id=TaskId("task123"),
            title="Sample Task",
            project=ProjectName("Test Project"),
            task_type=TaskType("Task"),
            status=TaskStatus("Todo"),
            priority=TaskPriority("High"),
            due_at=datetime.now() + timedelta(days=1),
        )

    @pytest.fixture
    def overdue_task(self) -> Task:
        """Create an overdue task for testing."""
        return Task(
            id=TaskId("overdue123"),
            title="Overdue Task",
            project=ProjectName("Test Project"),
            task_type=TaskType("Task"),
            status=TaskStatus("Todo"),
            priority=TaskPriority("High"),
            due_at=datetime.now() - timedelta(days=1),
        )

    async def test_get_overdue_tasks(self, overdue_task: Task) -> None:
        """Test getting overdue tasks."""
        self.mock_repo.tasks.list_tasks = AsyncMock(return_value=[overdue_task])

        result = await self.task_service.get_overdue_tasks("user@example.com")

        assert len(result) == 1
        assert result[0].id == overdue_task.id
        self.mock_repo.tasks.list_tasks.assert_called_once()

    async def test_get_high_priority_tasks(self, sample_task: Task) -> None:
        """Test getting high priority tasks."""
        self.mock_repo.tasks.list_tasks = AsyncMock(return_value=[sample_task])

        result = await self.task_service.get_high_priority_tasks(
            assignee="user@example.com", project="Test Project"
        )

        assert len(result) == 1
        assert result[0].is_high_priority()
        self.mock_repo.tasks.list_tasks.assert_called_once_with(
            assignee="user@example.com", project="Test Project"
        )

    async def test_get_my_active_tasks(self, sample_task: Task) -> None:
        """Test getting active tasks for a user."""
        self.mock_repo.tasks.list_tasks = AsyncMock(return_value=[sample_task])

        result = await self.task_service.get_my_active_tasks("user@example.com")

        assert len(result) == 1
        assert not result[0].is_completed()
        self.mock_repo.tasks.list_tasks.assert_called_once_with(
            assignee="user@example.com"
        )

    async def test_get_tasks_by_project(self, sample_task: Task) -> None:
        """Test grouping tasks by project status."""
        completed_task = Task(
            id=TaskId("completed123"),
            title="Completed Task",
            project=ProjectName("Test Project"),
            task_type=TaskType("Task"),
            status=TaskStatus("Done"),
        )

        self.mock_repo.tasks.list_tasks = AsyncMock(
            return_value=[sample_task, completed_task]
        )

        result = await self.task_service.get_tasks_by_project("Test Project")

        assert "Todo" in result
        assert "Done" in result
        assert len(result["Todo"]) == 1
        assert len(result["Done"]) == 1

    async def test_clone_task(self, sample_task: Task) -> None:
        """Test cloning an existing task."""
        cloned_task = Task(
            id=TaskId("cloned123"),
            title="Copy of Sample Task",
            project=sample_task.project,
            task_type=sample_task.task_type,
            status=TaskStatus("Todo"),
        )

        self.mock_repo.tasks.get_task = AsyncMock(return_value=sample_task)
        self.mock_repo.tasks.create_task = AsyncMock(return_value=cloned_task)

        result = await self.task_service.clone_task(sample_task.id)

        assert result.title == "Copy of Sample Task"
        self.mock_repo.tasks.get_task.assert_called_once_with(sample_task.id)
        self.mock_repo.tasks.create_task.assert_called_once()

    async def test_clone_task_not_found(self) -> None:
        """Test cloning a non-existent task."""
        self.mock_repo.tasks.get_task = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Task .* not found"):
            await self.task_service.clone_task(TaskId("nonexistent"))

    async def test_bulk_update_status(self, sample_task: Task) -> None:
        """Test bulk updating task status."""
        updated_task = sample_task._replace(status=TaskStatus("In Progress"))

        self.mock_repo.tasks.update_task = AsyncMock(return_value=updated_task)

        result = await self.task_service.bulk_update_status(
            [sample_task.id], "In Progress"
        )

        assert len(result) == 1
        assert result[0].status.value == "In Progress"

    async def test_get_task_hierarchy(self, sample_task: Task) -> None:
        """Test getting task hierarchy with subtasks."""
        child_task = Task(
            id=TaskId("child123"),
            title="Child Task",
            project=ProjectName("Test Project"),
            task_type=TaskType("Task"),
            status=TaskStatus("Todo"),
            parent_id=sample_task.id,
        )

        self.mock_repo.tasks.get_task = AsyncMock(return_value=sample_task)
        self.mock_repo.tasks.list_tasks = AsyncMock(
            return_value=[sample_task, child_task]
        )

        result = await self.task_service.get_task_hierarchy(sample_task.id)

        assert len(result) == 2
        assert result[0].id == sample_task.id
        assert result[1].id == child_task.id


@pytest.mark.asyncio
class TestDocumentService:
    """Test DocumentService domain service."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.mock_repo = MagicMock(spec=TaskManagementRepository)
        self.doc_service = DocumentService(self.mock_repo)

    @pytest.fixture
    def sample_doc(self) -> Document:
        """Create a sample document for testing."""
        return Document(
            id="doc123",
            title="Sample Document",
            text="This is sample content",
            folder="Test Folder",
        )

    async def test_get_docs_by_folder(self, sample_doc: Document) -> None:
        """Test getting documents by folder."""
        self.mock_repo.docs.list_docs = AsyncMock(return_value=[sample_doc])

        result = await self.doc_service.get_docs_by_folder("Test Folder")

        assert len(result) == 1
        assert result[0].folder == "Test Folder"
        self.mock_repo.docs.list_docs.assert_called_once_with(folder="Test Folder")

    async def test_search_docs_content(self, sample_doc: Document) -> None:
        """Test searching documents by content."""
        self.mock_repo.docs.list_docs = AsyncMock(return_value=[sample_doc])

        result = await self.doc_service.search_docs_content("sample")

        assert len(result) == 1
        self.mock_repo.docs.list_docs.assert_called_once_with(search="sample")

    async def test_get_empty_docs(self) -> None:
        """Test getting empty documents."""
        empty_doc = Document(
            id="empty123",
            title="Empty Document",
            text="   ",  # Empty/whitespace only
        )
        filled_doc = Document(
            id="filled123",
            title="Filled Document",
            text="This has content",
        )

        self.mock_repo.docs.list_docs = AsyncMock(return_value=[empty_doc, filled_doc])

        result = await self.doc_service.get_empty_docs()

        assert len(result) == 1
        assert result[0].id == "empty123"

    async def test_duplicate_doc(self, sample_doc: Document) -> None:
        """Test duplicating a document."""
        duplicated_doc = Document(
            id="dup123",
            title="Copy of Sample Document",
            text=sample_doc.text,
            folder=sample_doc.folder,
        )

        self.mock_repo.docs.get_doc = AsyncMock(return_value=sample_doc)
        self.mock_repo.docs.create_doc = AsyncMock(return_value=duplicated_doc)

        result = await self.doc_service.duplicate_doc("doc123")

        assert result.title == "Copy of Sample Document"
        assert result.text == sample_doc.text
        self.mock_repo.docs.get_doc.assert_called_once_with("doc123")
        self.mock_repo.docs.create_doc.assert_called_once()

    async def test_duplicate_doc_not_found(self) -> None:
        """Test duplicating a non-existent document."""
        self.mock_repo.docs.get_doc = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Document .* not found"):
            await self.doc_service.duplicate_doc("nonexistent")


@pytest.mark.asyncio
class TestWorkspaceService:
    """Test WorkspaceService domain service."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.mock_repo = MagicMock(spec=TaskManagementRepository)
        self.workspace_service = WorkspaceService(self.mock_repo)

    async def test_get_workspace_summary(self) -> None:
        """Test getting workspace summary statistics."""
        config = TaskConfig(
            assignees=["alice@example.com", "bob@example.com"],
            statuses=["Todo", "In Progress", "Done"],
            priorities=["Low", "Medium", "High"],
            sizes=["S", "M", "L"],
            projects=["Project A", "Project B"],
            tags=["frontend", "backend"],
        )

        tasks = [
            Task(
                id=TaskId("task1"),
                title="Task 1",
                project=ProjectName("Project A"),
                task_type=TaskType("Task"),
                status=TaskStatus("Done"),
                priority=TaskPriority("High"),
                due_at=datetime.now() - timedelta(days=1),  # Overdue
            ),
            Task(
                id=TaskId("task2"),
                title="Task 2",
                project=ProjectName("Project A"),
                task_type=TaskType("Task"),
                status=TaskStatus("Todo"),
                priority=TaskPriority("Low"),
            ),
        ]

        docs = [
            Document(id="doc1", title="Doc 1", is_draft=True, text="Content"),
            Document(id="doc2", title="Doc 2", text="   "),  # Empty
            Document(id="doc3", title="Doc 3", text="Content"),
        ]

        self.mock_repo.tasks.get_config = AsyncMock(return_value=config)
        self.mock_repo.tasks.list_tasks = AsyncMock(return_value=tasks)
        self.mock_repo.docs.list_docs = AsyncMock(return_value=docs)

        result = await self.workspace_service.get_workspace_summary()

        # Verify workspace config
        assert result["workspace_config"]["assignees_count"] == 2
        assert result["workspace_config"]["projects_count"] == 2

        # Verify task summary
        assert result["task_summary"]["total_tasks"] == 2
        assert result["task_summary"]["completed_tasks"] == 1
        assert result["task_summary"]["overdue_tasks"] == 1
        assert result["task_summary"]["high_priority_tasks"] == 1
        assert result["task_summary"]["completion_rate"] == 0.5

        # Verify doc summary
        assert result["doc_summary"]["total_docs"] == 3
        assert result["doc_summary"]["draft_docs"] == 1
        assert result["doc_summary"]["empty_docs"] == 1

        # Verify project stats
        assert "Project A" in result["project_stats"]
        assert result["project_stats"]["Project A"]["total"] == 2
        assert result["project_stats"]["Project A"]["completed"] == 1
