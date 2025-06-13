"""
Unit tests for PyTaskAI application layer.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from pytaskai.application.container import ApplicationContainer
from pytaskai.application.dto.task_dto import (
    DocumentCreateDTO,
    DocumentUpdateDTO,
    TaskCreateDTO,
    TaskListFiltersDTO,
    TaskUpdateDTO,
)
from pytaskai.application.interfaces.ai_service import (
    AIResearchService,
    AITaskGenerationService,
)
from pytaskai.application.interfaces.notification_service import NotificationService
from pytaskai.application.use_cases.ai_task_generation import AITaskGenerationUseCase
from pytaskai.application.use_cases.document_management import DocumentManagementUseCase
from pytaskai.application.use_cases.task_management import TaskManagementUseCase
from pytaskai.domain.entities.task import Document, Task
from pytaskai.domain.repositories.task_repository import TaskManagementRepository
from pytaskai.domain.value_objects.task_types import (
    ProjectName,
    TaskId,
    TaskPriority,
    TaskStatus,
    TaskType,
)


@pytest.mark.asyncio
class TestTaskManagementUseCase:
    """Test TaskManagementUseCase."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.mock_repo = MagicMock(spec=TaskManagementRepository)
        self.mock_notification = MagicMock(spec=NotificationService)

        # Setup container
        self.container = ApplicationContainer(
            repository=self.mock_repo,
            notification_service=self.mock_notification,
        )
        self.use_case = self.container.task_management_use_case

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
            assignee="user@example.com",
        )

    async def test_create_task(self, sample_task: Task) -> None:
        """Test creating a task."""
        # Setup mock
        self.mock_repo.tasks.create_task = AsyncMock(return_value=sample_task)
        self.mock_notification.send_task_created_notification = AsyncMock(
            return_value=True
        )

        # Create task DTO
        task_dto = TaskCreateDTO(
            title="Sample Task",
            project="Test Project",
            assignee="user@example.com",
            priority="High",
        )

        # Execute
        result = await self.use_case.create_task(task_dto)

        # Assert
        assert result.title == "Sample Task"
        assert result.project == "Test Project"
        assert result.assignee == "user@example.com"
        self.mock_repo.tasks.create_task.assert_called_once()
        self.mock_notification.send_task_created_notification.assert_called_once()

    async def test_get_task(self, sample_task: Task) -> None:
        """Test getting a task by ID."""
        # Setup mock
        self.mock_repo.tasks.get_task = AsyncMock(return_value=sample_task)

        # Execute
        result = await self.use_case.get_task("task123")

        # Assert
        assert result is not None
        assert result.id == "task123"
        assert result.title == "Sample Task"
        self.mock_repo.tasks.get_task.assert_called_once_with(TaskId("task123"))

    async def test_get_task_not_found(self) -> None:
        """Test getting a non-existent task."""
        # Setup mock
        self.mock_repo.tasks.get_task = AsyncMock(return_value=None)

        # Execute
        result = await self.use_case.get_task("nonexistent")

        # Assert
        assert result is None

    async def test_list_tasks_with_filters(self, sample_task: Task) -> None:
        """Test listing tasks with filters."""
        # Setup mock
        self.mock_repo.tasks.list_tasks = AsyncMock(return_value=[sample_task])

        # Create filters
        filters = TaskListFiltersDTO(
            assignee="user@example.com",
            project="Test Project",
            status="Todo",
        )

        # Execute
        result = await self.use_case.list_tasks(filters)

        # Assert
        assert len(result) == 1
        assert result[0].id == "task123"
        self.mock_repo.tasks.list_tasks.assert_called_once_with(
            assignee="user@example.com",
            project="Test Project",
            status="Todo",
        )

    async def test_update_task(self, sample_task: Task) -> None:
        """Test updating a task."""
        # Setup mocks
        updated_task = sample_task._replace(status=TaskStatus("Done"))
        self.mock_repo.tasks.get_task = AsyncMock(return_value=sample_task)
        self.mock_repo.tasks.update_task = AsyncMock(return_value=updated_task)

        # Create update DTO
        update_dto = TaskUpdateDTO(
            task_id="task123",
            status="Done",
        )

        # Execute
        result = await self.use_case.update_task(update_dto)

        # Assert
        assert result.status == "Done"
        self.mock_repo.tasks.update_task.assert_called_once()

    async def test_update_task_not_found(self) -> None:
        """Test updating a non-existent task."""
        # Setup mock
        self.mock_repo.tasks.get_task = AsyncMock(return_value=None)

        # Create update DTO
        update_dto = TaskUpdateDTO(task_id="nonexistent", status="Done")

        # Execute and assert
        with pytest.raises(ValueError, match="Task nonexistent not found"):
            await self.use_case.update_task(update_dto)

    async def test_delete_task(self, sample_task: Task) -> None:
        """Test deleting a task."""
        # Setup mocks
        self.mock_repo.tasks.get_task = AsyncMock(return_value=sample_task)
        self.mock_repo.tasks.delete_task = AsyncMock(return_value=True)

        # Execute
        result = await self.use_case.delete_task("task123")

        # Assert
        assert result is True
        self.mock_repo.tasks.delete_task.assert_called_once_with(TaskId("task123"))


@pytest.mark.asyncio
class TestDocumentManagementUseCase:
    """Test DocumentManagementUseCase."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.mock_repo = MagicMock(spec=TaskManagementRepository)

        # Setup container
        self.container = ApplicationContainer(repository=self.mock_repo)
        self.use_case = self.container.document_management_use_case

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        return Document(
            id="doc123",
            title="Sample Document",
            text="This is sample content",
            folder="Test Folder",
        )

    async def test_create_document(self, sample_document: Document) -> None:
        """Test creating a document."""
        # Setup mock
        self.mock_repo.docs.create_doc = AsyncMock(return_value=sample_document)

        # Create document DTO
        doc_dto = DocumentCreateDTO(
            title="Sample Document",
            text="This is sample content",
            folder="Test Folder",
        )

        # Execute
        result = await self.use_case.create_document(doc_dto)

        # Assert
        assert result.title == "Sample Document"
        assert result.text == "This is sample content"
        assert result.folder == "Test Folder"
        self.mock_repo.docs.create_doc.assert_called_once()

    async def test_get_document(self, sample_document: Document) -> None:
        """Test getting a document by ID."""
        # Setup mock
        self.mock_repo.docs.get_doc = AsyncMock(return_value=sample_document)

        # Execute
        result = await self.use_case.get_document("doc123")

        # Assert
        assert result is not None
        assert result.id == "doc123"
        assert result.title == "Sample Document"

    async def test_update_document(self, sample_document: Document) -> None:
        """Test updating a document."""
        # Setup mocks
        updated_doc = sample_document._replace(text="Updated content")
        self.mock_repo.docs.get_doc = AsyncMock(return_value=sample_document)
        self.mock_repo.docs.update_doc = AsyncMock(return_value=updated_doc)

        # Create update DTO
        update_dto = DocumentUpdateDTO(
            document_id="doc123",
            text="Updated content",
        )

        # Execute
        result = await self.use_case.update_document(update_dto)

        # Assert
        assert result.text == "Updated content"
        self.mock_repo.docs.update_doc.assert_called_once()


@pytest.mark.asyncio
class TestAITaskGenerationUseCase:
    """Test AITaskGenerationUseCase."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.mock_repo = MagicMock(spec=TaskManagementRepository)
        self.mock_ai_generation = MagicMock(spec=AITaskGenerationService)
        self.mock_ai_research = MagicMock(spec=AIResearchService)

        # Setup container with AI services
        self.container = ApplicationContainer(
            repository=self.mock_repo,
            ai_generation_service=self.mock_ai_generation,
            ai_research_service=self.mock_ai_research,
        )
        self.use_case = self.container.ai_task_generation_use_case

    async def test_generate_tasks_from_prd(self) -> None:
        """Test generating tasks from PRD."""
        # Setup mocks
        generated_tasks = [
            TaskCreateDTO(
                title="Implement feature A",
                project="Test Project",
                description="Feature A implementation",
            ),
            TaskCreateDTO(
                title="Test feature A",
                project="Test Project",
                description="Feature A testing",
            ),
        ]

        self.mock_ai_generation.generate_tasks_from_prd = AsyncMock(
            return_value=generated_tasks
        )
        self.mock_ai_research.research_task_context = AsyncMock(
            return_value="Additional context from research"
        )

        # Execute
        result = await self.use_case.generate_tasks_from_prd(
            prd_content="Build feature A with testing",
            project="Test Project",
        )

        # Assert
        assert len(result) == 2
        assert result[0].title == "Implement feature A"
        assert "Additional context from research" in result[0].description
        self.mock_ai_generation.generate_tasks_from_prd.assert_called_once()

    async def test_generate_subtasks(self) -> None:
        """Test generating subtasks for a parent task."""
        # Setup parent task
        parent_task = Task(
            id=TaskId("parent123"),
            title="Complex Feature",
            project=ProjectName("Test Project"),
            task_type=TaskType("Task"),
            status=TaskStatus("Todo"),
            description="Complex feature implementation",
        )

        # Setup mocks
        self.mock_repo.tasks.get_task = AsyncMock(return_value=parent_task)

        generated_subtasks = [
            TaskCreateDTO(
                title="Subtask 1",
                project="Test Project",
                description="First subtask",
            ),
            TaskCreateDTO(
                title="Subtask 2",
                project="Test Project",
                description="Second subtask",
            ),
        ]

        self.mock_ai_generation.generate_subtasks = AsyncMock(
            return_value=generated_subtasks
        )

        # Execute
        result = await self.use_case.generate_subtasks(
            parent_task_id="parent123",
        )

        # Assert
        assert len(result) == 2
        assert result[0].parent_id == "parent123"
        assert result[1].parent_id == "parent123"
        self.mock_ai_generation.generate_subtasks.assert_called_once()


@pytest.mark.asyncio
class TestApplicationContainer:
    """Test ApplicationContainer dependency injection."""

    def test_container_initialization(self) -> None:
        """Test container initialization with all services."""
        # Setup mocks
        mock_repo = MagicMock(spec=TaskManagementRepository)
        mock_ai_generation = MagicMock(spec=AITaskGenerationService)
        mock_ai_research = MagicMock(spec=AIResearchService)
        mock_notification = MagicMock(spec=NotificationService)

        # Create container
        container = ApplicationContainer(
            repository=mock_repo,
            ai_generation_service=mock_ai_generation,
            ai_research_service=mock_ai_research,
            notification_service=mock_notification,
        )

        # Assert all services are available
        assert container.task_management_use_case is not None
        assert container.document_management_use_case is not None
        assert container.ai_task_generation_use_case is not None
        assert container.has_ai_services() is True
        assert container.has_notification_service() is True

    def test_container_without_optional_services(self) -> None:
        """Test container initialization without optional services."""
        # Setup mock
        mock_repo = MagicMock(spec=TaskManagementRepository)

        # Create container
        container = ApplicationContainer(repository=mock_repo)

        # Assert only core services are available
        assert container.task_management_use_case is not None
        assert container.document_management_use_case is not None
        assert container.ai_task_generation_use_case is None
        assert container.has_ai_services() is False
        assert container.has_notification_service() is False
