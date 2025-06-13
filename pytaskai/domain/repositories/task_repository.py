"""
Repository interfaces for PyTaskAI task management.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from pytaskai.domain.entities.task import Document, Task
from pytaskai.domain.value_objects.task_types import TaskConfig, TaskId


class TaskRepository(ABC):
    """
    Abstract repository interface for PyTaskAI task operations.
    """

    @abstractmethod
    async def get_config(self) -> TaskConfig:
        """Get PyTaskAI workspace configuration."""
        pass

    @abstractmethod
    async def list_tasks(
        self,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
        project: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        due_at_before: Optional[datetime] = None,
        due_at_after: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Task]:
        """List tasks with optional filters."""
        pass

    @abstractmethod
    async def get_task(self, task_id: TaskId) -> Optional[Task]:
        """Get a specific task by ID."""
        pass

    @abstractmethod
    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        size: Optional[str] = None,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        due_at: Optional[datetime] = None,
        start_at: Optional[datetime] = None,
        parent_id: Optional[str] = None,
    ) -> Task:
        """Create a new task."""
        pass

    @abstractmethod
    async def update_task(
        self,
        task_id: TaskId,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        size: Optional[str] = None,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        due_at: Optional[datetime] = None,
        start_at: Optional[datetime] = None,
        parent_id: Optional[str] = None,
    ) -> Task:
        """Update an existing task."""
        pass

    @abstractmethod
    async def delete_task(self, task_id: TaskId) -> bool:
        """Delete a task (move to trash)."""
        pass

    @abstractmethod
    async def add_task_comment(self, task_id: TaskId, text: str) -> bool:
        """Add a comment to a task."""
        pass


class DocumentRepository(ABC):
    """
    Abstract repository interface for PyTaskAI document operations.
    """

    @abstractmethod
    async def list_docs(
        self,
        folder: Optional[str] = None,
        title: Optional[str] = None,
        text: Optional[str] = None,
        search: Optional[str] = None,
        in_trash: Optional[bool] = None,
        is_draft: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Document]:
        """List documents with optional filters."""
        pass

    @abstractmethod
    async def get_doc(self, doc_id: str) -> Optional[Document]:
        """Get a specific document by ID."""
        pass

    @abstractmethod
    async def create_doc(
        self,
        title: str,
        text: Optional[str] = None,
        folder: Optional[str] = None,
    ) -> Document:
        """Create a new document."""
        pass

    @abstractmethod
    async def update_doc(
        self,
        doc_id: str,
        title: Optional[str] = None,
        text: Optional[str] = None,
        folder: Optional[str] = None,
    ) -> Document:
        """Update an existing document."""
        pass

    @abstractmethod
    async def delete_doc(self, doc_id: str) -> bool:
        """Delete a document (move to trash)."""
        pass


class TaskManagementRepository(ABC):
    """
    Combined repository interface for all PyTaskAI operations.
    """

    # ---------------------------------------------------------------------
    # Task repository compatibility helpers
    # ---------------------------------------------------------------------
    #
    # A large part of the application layer directly calls task CRUD methods
    # (``create_task``, ``list_tasks`` …) on the *combined* repository instance
    # instead of going through the nested ``tasks`` sub-repository.  At the
    # same time, many tests – and some adapter implementations – expect to
    # access the nested repositories via the ``tasks`` / ``docs`` properties.
    #
    # To support **both** calling conventions we expose shim methods here that
    # simply forward the calls to the appropriate nested repository.  Concrete
    # implementations can rely on these default behaviours, but are free to
    # override them if they need a more efficient implementation.
    # ---------------------------------------------------------------------

    # ---- Nested repositories ------------------------------------------------
    # Use PEP 526 attribute annotations so that unittest.mock can dynamically
    # assign AsyncMock instances (e.g. ``mock_repo.tasks.list_tasks =
    # AsyncMock(...)``) without raising ``AttributeError``.  Defining these as
    # *properties* would break such test setups because property descriptors
    # are read-only.

    # Default ``None`` runtime values ensure the attributes *exist* on the
    # class so that ``unittest.mock.MagicMock(spec=TaskManagementRepository)``
    # can produce writable mocks (the spec only checks attribute *names*).
    tasks: TaskRepository  # type: ignore
    docs: DocumentRepository  # type: ignore

    # Runtime placeholders – will be replaced by concrete repository instances
    # in real implementations or by MagicMock objects in unit tests.
    tasks = None  # type: ignore
    docs = None  # type: ignore

    # ---- Task-level convenience wrappers -----------------------------------

    async def get_config(self) -> TaskConfig:  # type: ignore[override]
        return await self.tasks.get_config()

    async def list_tasks(
        self,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
        project: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        due_at_before: Optional[datetime] = None,
        due_at_after: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        parent_id: Optional[str] = None,
    ) -> List[Task]:  # type: ignore[override]
        return await self.tasks.list_tasks(
            assignee=assignee,
            status=status,
            project=project,
            priority=priority,
            tag=tag,
            due_at_before=due_at_before,
            due_at_after=due_at_after,
            limit=limit,
            offset=offset,
            parent_id=parent_id,
        )

    async def get_task(self, task_id: TaskId) -> Optional[Task]:  # type: ignore[override]
        return await self.tasks.get_task(task_id)

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        size: Optional[str] = None,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        due_at: Optional[datetime] = None,
        start_at: Optional[datetime] = None,
        parent_id: Optional[str] = None,
    ) -> Task:  # type: ignore[override]
        return await self.tasks.create_task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            size=size,
            project=project,
            assignee=assignee,
            assignees=assignees,
            tags=tags,
            due_at=due_at,
            start_at=start_at,
            parent_id=parent_id,
        )

    async def update_task(
        self,
        task_id: TaskId,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        size: Optional[str] = None,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        due_at: Optional[datetime] = None,
        start_at: Optional[datetime] = None,
        parent_id: Optional[str] = None,
    ) -> Task:  # type: ignore[override]
        return await self.tasks.update_task(
            task_id=task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            size=size,
            project=project,
            assignee=assignee,
            assignees=assignees,
            tags=tags,
            due_at=due_at,
            start_at=start_at,
            parent_id=parent_id,
        )

    async def delete_task(self, task_id: TaskId) -> bool:  # type: ignore[override]
        return await self.tasks.delete_task(task_id)

    async def add_task_comment(self, task_id: TaskId, text: str) -> bool:  # type: ignore[override]
        return await self.tasks.add_task_comment(task_id, text)

    # ---- Document-level convenience wrappers --------------------------------

    async def list_docs(self, *args, **kwargs):  # type: ignore[override]
        return await self.docs.list_docs(*args, **kwargs)

    async def get_doc(self, doc_id: str):  # type: ignore[override]
        return await self.docs.get_doc(doc_id)

    async def create_doc(self, *args, **kwargs):  # type: ignore[override]
        return await self.docs.create_doc(*args, **kwargs)

    async def update_doc(self, *args, **kwargs):  # type: ignore[override]
        return await self.docs.update_doc(*args, **kwargs)

    async def delete_doc(self, doc_id: str):  # type: ignore[override]
        return await self.docs.delete_doc(doc_id)
