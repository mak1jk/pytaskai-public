"""
Domain entities for PyTaskAI task management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pytaskai.domain.value_objects.task_types import (
    ProjectName,
    TagName,
    TaskId,
    TaskPriority,
    TaskSize,
    TaskStatus,
    TaskType,
)


@dataclass(frozen=True)
class Task:
    """
    Domain entity representing a PyTaskAI task.
    """

    id: TaskId
    title: str
    project: ProjectName
    task_type: TaskType
    status: TaskStatus
    external_url: Optional[str] = None
    assignee: Optional[str] = None
    parent_id: Optional[TaskId] = None
    tags: List[TagName] = field(default_factory=list)
    priority: Optional[TaskPriority] = None
    start_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    size: Optional[TaskSize] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status.is_done()

    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_at:
            return False
        return datetime.now() > self.due_at

    def has_parent(self) -> bool:
        """Check if task has a parent."""
        return self.parent_id is not None

    def is_high_priority(self) -> bool:
        """Check if task has high or critical priority."""
        return bool(self.priority and self.priority.is_high_priority())

    def add_tag(self, tag: TagName) -> "Task":
        """Add a tag to the task (returns new instance)."""
        if tag in self.tags:
            return self
        new_tags = self.tags + [tag]
        return self._replace(tags=new_tags)

    def remove_tag(self, tag: TagName) -> "Task":
        """Remove a tag from the task (returns new instance)."""
        if tag not in self.tags:
            return self
        new_tags = [t for t in self.tags if t != tag]
        return self._replace(tags=new_tags)

    def update_status(self, new_status: TaskStatus) -> "Task":
        """Update task status (returns new instance)."""
        return self._replace(status=new_status)

    def _replace(self, **changes: Any) -> "Task":
        """Create a new instance with updated fields."""
        current_dict: Dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "external_url": self.external_url,
            "project": self.project,
            "task_type": self.task_type,
            "status": self.status,
            "assignee": self.assignee,
            "parent_id": self.parent_id,
            "tags": self.tags,
            "priority": self.priority,
            "start_at": self.start_at,
            "due_at": self.due_at,
            "size": self.size,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        current_dict.update(changes)
        return Task(**current_dict)


@dataclass(frozen=True)
class Document:
    """
    Domain entity representing a PyTaskAI document.
    """

    id: str
    title: str
    text: Optional[str] = None
    folder: Optional[str] = None
    is_draft: bool = False
    in_trash: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_empty(self) -> bool:
        """Check if document has no content."""
        return not self.text or self.text.strip() == ""

    def update_content(self, new_text: str) -> "Document":
        """Update document content (returns new instance)."""
        return self._replace(text=new_text)

    def move_to_folder(self, folder_name: str) -> "Document":
        """Move document to folder (returns new instance)."""
        return self._replace(folder=folder_name)

    def _replace(self, **changes: Any) -> "Document":
        """Create a new instance with updated fields."""
        current_dict: Dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "folder": self.folder,
            "is_draft": self.is_draft,
            "in_trash": self.in_trash,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        current_dict.update(changes)
        return Document(**current_dict)
