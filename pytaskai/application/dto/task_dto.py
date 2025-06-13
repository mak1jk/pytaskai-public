"""
Data Transfer Objects for PyTaskAI application layer.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class TaskCreateDTO:
    """DTO for creating a new task."""

    title: str
    project: str
    task_type: str = "Task"
    status: str = "Todo"
    description: Optional[str] = None
    assignee: Optional[str] = None
    parent_id: Optional[str] = None
    tags: List[str] = None
    priority: Optional[str] = None
    start_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    size: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate DTO data."""
        if not self.title or not self.title.strip():
            raise ValueError("Title is required")
        if not self.project or not self.project.strip():
            raise ValueError("Project is required")
        if self.tags is None:
            object.__setattr__(self, "tags", [])


@dataclass(frozen=True)
class TaskUpdateDTO:
    """DTO for updating an existing task."""

    task_id: str
    title: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    assignee: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    start_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    size: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate DTO data."""
        if not self.task_id or not self.task_id.strip():
            raise ValueError("Task ID is required")


@dataclass(frozen=True)
class TaskResponseDTO:
    """DTO for task responses."""

    id: str
    title: str
    external_url: Optional[str]
    project: str
    task_type: str
    status: str
    assignee: Optional[str]
    parent_id: Optional[str]
    tags: List[str]
    priority: Optional[str]
    start_at: Optional[datetime]
    due_at: Optional[datetime]
    size: Optional[str]
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    # ------------------------------------------------------------------
    # Convenience aliases
    # ------------------------------------------------------------------

    @property
    def task_id(self) -> str:  # pragma: no cover
        """Alias for ``id`` to improve developer ergonomics.

        Several parts of the codebase – especially test suites and AI helper
        utilities – historically used the attribute name ``task_id`` instead
        of the canonical ``id``.  To keep backward-compatibility we provide
        this read-only alias.
        """
        return self.id

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status.lower() in ["done", "completed", "finished"]

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_at:
            return False
        return datetime.now() > self.due_at

    @property
    def is_high_priority(self) -> bool:
        """Check if task has high priority."""
        if not self.priority:
            return False
        return self.priority.lower() in ["high", "critical", "urgent"]


@dataclass(frozen=True)
class TaskListFiltersDTO:
    """DTO for task list filtering parameters."""

    assignee: Optional[str] = None
    project: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    task_type: Optional[str] = None
    tag: Optional[str] = None
    due_at_before: Optional[datetime] = None
    due_at_after: Optional[datetime] = None
    parent_id: Optional[str] = None
    include_completed: bool = True


@dataclass(frozen=True)
class DocumentCreateDTO:
    """DTO for creating a new document."""

    title: str
    text: Optional[str] = None
    folder: Optional[str] = None
    is_draft: bool = False

    def __post_init__(self) -> None:
        """Validate DTO data."""
        if not self.title or not self.title.strip():
            raise ValueError("Title is required")


@dataclass(frozen=True)
class DocumentUpdateDTO:
    """DTO for updating an existing document."""

    document_id: str
    title: Optional[str] = None
    text: Optional[str] = None
    folder: Optional[str] = None
    is_draft: Optional[bool] = None

    def __post_init__(self) -> None:
        """Validate DTO data."""
        if not self.document_id or not self.document_id.strip():
            raise ValueError("Document ID is required")


@dataclass(frozen=True)
class DocumentResponseDTO:
    """DTO for document responses."""

    id: str
    title: str
    text: Optional[str]
    folder: Optional[str]
    is_draft: bool
    in_trash: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @property
    def is_empty(self) -> bool:
        """Check if document has no content."""
        return not self.text or self.text.strip() == ""


@dataclass(frozen=True)
class WorkspaceSummaryDTO:
    """DTO for workspace summary statistics."""

    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    high_priority_tasks: int
    completion_rate: float
    total_docs: int
    draft_docs: int
    empty_docs: int
    assignees_count: int
    projects_count: int
