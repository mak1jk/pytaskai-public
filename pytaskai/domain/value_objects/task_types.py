"""
Value objects for PyTaskAI task management.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TaskId:
    """Value object for PyTaskAI task ID."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TaskId must be a non-empty string")
        if len(self.value) < 1:
            raise ValueError("TaskId must be at least 1 character")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TaskStatus:
    """Value object for PyTaskAI task status."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TaskStatus must be a non-empty string")

    def is_done(self) -> bool:
        """Check if status indicates completion."""
        return self.value.lower() in ["done", "completed", "closed"]

    def is_in_progress(self) -> bool:
        """Check if status indicates work in progress."""
        return self.value.lower() in ["in progress", "doing", "active"]

    def is_pending(self) -> bool:
        """Check if status indicates pending work."""
        return self.value.lower() in ["todo", "pending", "backlog", "open"]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TaskPriority:
    """Value object for PyTaskAI task priority."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TaskPriority must be a non-empty string")

    def is_high_priority(self) -> bool:
        """Check if priority is high or critical."""
        return self.value.lower() in ["high", "critical", "urgent"]

    def is_low_priority(self) -> bool:
        """Check if priority is low."""
        return self.value.lower() in ["low", "minor"]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TaskSize:
    """Value object for PyTaskAI task size."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TaskSize must be a non-empty string")

    def is_large(self) -> bool:
        """Check if task is large."""
        return self.value.lower() in ["large", "xl", "extra large"]

    def is_small(self) -> bool:
        """Check if task is small."""
        return self.value.lower() in ["small", "xs", "extra small"]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TaskType:
    """Value object for PyTaskAI task type."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TaskType must be a non-empty string")

    def is_bug(self) -> bool:
        """Check if task is a bug."""
        return self.value.lower() == "bug"

    def is_feature(self) -> bool:
        """Check if task is a feature."""
        return self.value.lower() == "feature"

    def is_task(self) -> bool:
        """Check if task is a regular task."""
        return self.value.lower() == "task"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ProjectName:
    """Value object for PyTaskAI project name."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("ProjectName must be a non-empty string")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TagName:
    """Value object for PyTaskAI tag name."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TagName must be a non-empty string")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TaskConfig:
    """Value object for PyTaskAI configuration."""

    assignees: List[str]
    statuses: List[str]
    priorities: List[str]
    sizes: List[str]
    projects: List[str]
    tags: List[str]

    def __post_init__(self) -> None:
        if not isinstance(self.assignees, list):
            raise ValueError("assignees must be a list")
        if not isinstance(self.statuses, list):
            raise ValueError("statuses must be a list")
        if not isinstance(self.priorities, list):
            raise ValueError("priorities must be a list")
        if not isinstance(self.sizes, list):
            raise ValueError("sizes must be a list")
        if not isinstance(self.projects, list):
            raise ValueError("projects must be a list")
        if not isinstance(self.tags, list):
            raise ValueError("tags must be a list")
