"""
Integration tests for SQLite repository implementation.
"""

import os
import tempfile
from datetime import datetime, timedelta
from typing import Generator

import pytest

from pytaskai.domain.entities.task import Document, Task
from pytaskai.domain.value_objects.task_types import (
    ProjectName,
    TagName,
    TaskConfig,
    TaskId,
    TaskPriority,
    TaskSize,
    TaskStatus,
    TaskType,
)
from pytaskai.infrastructure.config.database_config import DatabaseConfig
from pytaskai.infrastructure.persistence.database import Database
from pytaskai.infrastructure.persistence.sqlite_task_repository import (
    SQLiteTaskManagementRepository,
)


@pytest.fixture
def temp_db() -> Generator[Database, None, None]:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        config = DatabaseConfig.for_testing(temp_path)
        database = Database(config)
        database.initialize()
        database.create_tables()
        yield database
    finally:
        database.close()
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.fixture
def repository(temp_db: Database) -> SQLiteTaskManagementRepository:
    """Create repository with temporary database."""
    return SQLiteTaskManagementRepository(temp_db)


@pytest.mark.asyncio
class TestSQLiteTaskRepository:
    """Test SQLite task repository implementation."""

    async def test_create_and_get_task(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test creating and retrieving a task."""
        # Create task
        task = await repository.tasks.create_task(
            title="Test Task",
            description="This is a test task",
            priority="High",
            size="Medium",
            project="Test Project",
            assignee="test@example.com",
            tags=["test", "integration"],
            due_at=datetime.now() + timedelta(days=7),
        )

        # Verify task was created
        assert task.title == "Test Task"
        assert task.description == "This is a test task"
        assert str(task.priority) == "High"
        assert str(task.size) == "Medium"
        assert str(task.project) == "Test Project"
        assert task.assignee == "test@example.com"
        assert len(task.tags) == 2
        assert task.due_at is not None

        # Retrieve task
        retrieved_task = await repository.tasks.get_task(task.id)
        assert retrieved_task is not None
        assert retrieved_task.id == task.id
        assert retrieved_task.title == task.title
        assert retrieved_task.description == task.description
        assert retrieved_task.priority == task.priority
        assert retrieved_task.size == task.size
        assert retrieved_task.assignee == task.assignee
        assert len(retrieved_task.tags) == 2

    async def test_update_task(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test updating a task."""
        # Create task
        task = await repository.tasks.create_task(
            title="Original Title",
            description="Original description",
            status="Todo",
            priority="Low",
        )

        # Update task
        updated_task = await repository.tasks.update_task(
            task_id=task.id,
            title="Updated Title",
            description="Updated description",
            status="In Progress",
            priority="High",
            assignee="updated@example.com",
        )

        # Verify updates
        assert updated_task.title == "Updated Title"
        assert updated_task.description == "Updated description"
        assert str(updated_task.status) == "In Progress"
        assert str(updated_task.priority) == "High"
        assert updated_task.assignee == "updated@example.com"
        assert updated_task.updated_at > task.updated_at

    async def test_delete_task(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test deleting a task."""
        # Create task
        task = await repository.tasks.create_task(
            title="Task to Delete",
            project="Test Project",
        )

        # Verify task exists
        retrieved_task = await repository.tasks.get_task(task.id)
        assert retrieved_task is not None

        # Delete task
        deleted = await repository.tasks.delete_task(task.id)
        assert deleted is True

        # Verify task is gone
        retrieved_task = await repository.tasks.get_task(task.id)
        assert retrieved_task is None

    async def test_list_tasks_with_filters(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test listing tasks with various filters."""
        # Create multiple tasks
        task1 = await repository.tasks.create_task(
            title="Task 1",
            project="Project A",
            assignee="alice@example.com",
            status="Todo",
            priority="High",
            tags=["frontend"],
        )

        task2 = await repository.tasks.create_task(
            title="Task 2",
            project="Project A",
            assignee="bob@example.com",
            status="In Progress",
            priority="Low",
            tags=["backend"],
        )

        task3 = await repository.tasks.create_task(
            title="Task 3",
            project="Project B",
            assignee="alice@example.com",
            status="Done",
            priority="High",
            tags=["frontend", "testing"],
        )

        # Test filter by assignee
        alice_tasks = await repository.tasks.list_tasks(assignee="alice@example.com")
        assert len(alice_tasks) == 2
        alice_task_ids = {task.id for task in alice_tasks}
        assert task1.id in alice_task_ids
        assert task3.id in alice_task_ids

        # Test filter by project
        project_a_tasks = await repository.tasks.list_tasks(project="Project A")
        assert len(project_a_tasks) == 2
        project_a_task_ids = {task.id for task in project_a_tasks}
        assert task1.id in project_a_task_ids
        assert task2.id in project_a_task_ids

        # Test filter by status
        todo_tasks = await repository.tasks.list_tasks(status="Todo")
        assert len(todo_tasks) == 1
        assert todo_tasks[0].id == task1.id

        # Test filter by priority
        high_priority_tasks = await repository.tasks.list_tasks(priority="High")
        assert len(high_priority_tasks) == 2
        high_priority_task_ids = {task.id for task in high_priority_tasks}
        assert task1.id in high_priority_task_ids
        assert task3.id in high_priority_task_ids

        # Test filter by tag
        frontend_tasks = await repository.tasks.list_tasks(tag="frontend")
        assert len(frontend_tasks) == 2
        frontend_task_ids = {task.id for task in frontend_tasks}
        assert task1.id in frontend_task_ids
        assert task3.id in frontend_task_ids

    async def test_task_hierarchy(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test parent-child task relationships."""
        # Create parent task
        parent_task = await repository.tasks.create_task(
            title="Parent Task",
            project="Test Project",
        )

        # Create child task
        child_task = await repository.tasks.create_task(
            title="Child Task",
            project="Test Project",
            parent_id=str(parent_task.id),
        )

        # Verify parent-child relationship
        assert child_task.parent_id == parent_task.id

        # List tasks by parent
        child_tasks = await repository.tasks.list_tasks(parent_id=str(parent_task.id))
        assert len(child_tasks) == 1
        assert child_tasks[0].id == child_task.id

    async def test_config_management(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test workspace configuration management."""
        # Get default config
        default_config = await repository.tasks.get_config()
        assert isinstance(default_config, TaskConfig)
        assert "Todo" in default_config.statuses
        assert "In Progress" in default_config.statuses
        assert "Done" in default_config.statuses

        # Update config
        new_config = TaskConfig(
            assignees=["alice@example.com", "bob@example.com"],
            statuses=["Backlog", "In Progress", "Review", "Done"],
            priorities=["Low", "Medium", "High", "Critical"],
            sizes=["XS", "S", "M", "L", "XL"],
            projects=["Project Alpha", "Project Beta"],
            tags=["frontend", "backend", "testing", "docs"],
        )

        updated_config = await repository.tasks.update_config(new_config)
        assert len(updated_config.assignees) == 2
        assert len(updated_config.statuses) == 4
        assert len(updated_config.projects) == 2
        assert "alice@example.com" in updated_config.assignees
        assert "Backlog" in updated_config.statuses
        assert "Project Alpha" in updated_config.projects

        # Verify config persistence
        retrieved_config = await repository.tasks.get_config()
        assert set(retrieved_config.assignees) == set(updated_config.assignees)
        assert set(retrieved_config.statuses) == set(updated_config.statuses)
        assert set(retrieved_config.projects) == set(updated_config.projects)


@pytest.mark.asyncio
class TestSQLiteDocumentRepository:
    """Test SQLite document repository implementation."""

    async def test_create_and_get_document(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test creating and retrieving a document."""
        # Create document
        doc = await repository.docs.create_doc(
            title="Test Document",
            text="This is test content",
            folder="Test Folder",
            is_draft=True,
        )

        # Verify document was created
        assert doc.title == "Test Document"
        assert doc.text == "This is test content"
        assert doc.folder == "Test Folder"
        assert doc.is_draft is True
        assert doc.in_trash is False

        # Retrieve document
        retrieved_doc = await repository.docs.get_doc(doc.id)
        assert retrieved_doc is not None
        assert retrieved_doc.id == doc.id
        assert retrieved_doc.title == doc.title
        assert retrieved_doc.text == doc.text
        assert retrieved_doc.folder == doc.folder
        assert retrieved_doc.is_draft == doc.is_draft

    async def test_update_document(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test updating a document."""
        # Create document
        doc = await repository.docs.create_doc(
            title="Original Title",
            text="Original content",
            folder="Original Folder",
            is_draft=True,
        )

        # Update document
        updated_doc = await repository.docs.update_doc(
            doc_id=doc.id,
            title="Updated Title",
            text="Updated content",
            folder="Updated Folder",
            is_draft=False,
        )

        # Verify updates
        assert updated_doc.title == "Updated Title"
        assert updated_doc.text == "Updated content"
        assert updated_doc.folder == "Updated Folder"
        assert updated_doc.is_draft is False
        assert updated_doc.updated_at > doc.updated_at

    async def test_delete_document(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test deleting a document (moving to trash)."""
        # Create document
        doc = await repository.docs.create_doc(
            title="Document to Delete",
            text="Content to delete",
        )

        # Verify document exists
        retrieved_doc = await repository.docs.get_doc(doc.id)
        assert retrieved_doc is not None
        assert retrieved_doc.in_trash is False

        # Delete document (move to trash)
        deleted = await repository.docs.delete_doc(doc.id)
        assert deleted is True

        # Verify document is in trash but still exists
        trashed_doc = await repository.docs.get_doc(doc.id)
        assert trashed_doc is not None
        assert trashed_doc.in_trash is True

    async def test_list_documents_with_filters(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test listing documents with filters."""
        # Create multiple documents
        doc1 = await repository.docs.create_doc(
            title="Document 1",
            text="Content about Python programming",
            folder="Programming",
        )

        doc2 = await repository.docs.create_doc(
            title="Document 2",
            text="Content about web development",
            folder="Programming",
        )

        doc3 = await repository.docs.create_doc(
            title="Meeting Notes",
            text="Notes from team meeting",
            folder="Meetings",
        )

        # Test list all documents
        all_docs = await repository.docs.list_docs()
        assert len(all_docs) == 3

        # Test filter by folder
        programming_docs = await repository.docs.list_docs(folder="Programming")
        assert len(programming_docs) == 2
        programming_doc_ids = {doc.id for doc in programming_docs}
        assert doc1.id in programming_doc_ids
        assert doc2.id in programming_doc_ids

        # Test search by content
        python_docs = await repository.docs.list_docs(search="Python")
        assert len(python_docs) == 1
        assert python_docs[0].id == doc1.id

        # Test search by title
        meeting_docs = await repository.docs.list_docs(search="Meeting")
        assert len(meeting_docs) == 1
        assert meeting_docs[0].id == doc3.id


@pytest.mark.asyncio
class TestRepositoryIntegration:
    """Test integration between task and document repositories."""

    async def test_repository_transaction_isolation(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test that repository operations are properly isolated."""
        # Create a task
        task = await repository.tasks.create_task(
            title="Test Task",
            project="Test Project",
        )

        # Create a document
        doc = await repository.docs.create_doc(
            title="Test Document",
            text="Related to the test task",
        )

        # Verify both exist independently
        retrieved_task = await repository.tasks.get_task(task.id)
        retrieved_doc = await repository.docs.get_doc(doc.id)

        assert retrieved_task is not None
        assert retrieved_doc is not None
        assert retrieved_task.id == task.id
        assert retrieved_doc.id == doc.id

    async def test_concurrent_operations(
        self, repository: SQLiteTaskManagementRepository
    ) -> None:
        """Test concurrent repository operations."""
        # Create multiple tasks and documents concurrently
        import asyncio

        async def create_task(i: int) -> Task:
            return await repository.tasks.create_task(
                title=f"Task {i}",
                project="Concurrent Test",
                assignee=f"user{i}@example.com",
            )

        async def create_doc(i: int) -> Document:
            return await repository.docs.create_doc(
                title=f"Document {i}",
                text=f"Content for document {i}",
                folder="Concurrent Test",
            )

        # Create tasks and documents concurrently
        tasks = await asyncio.gather(*[create_task(i) for i in range(5)])
        docs = await asyncio.gather(*[create_doc(i) for i in range(5)])

        # Verify all were created
        assert len(tasks) == 5
        assert len(docs) == 5

        # Verify all have unique IDs
        task_ids = {task.id for task in tasks}
        doc_ids = {doc.id for doc in docs}
        assert len(task_ids) == 5
        assert len(doc_ids) == 5
