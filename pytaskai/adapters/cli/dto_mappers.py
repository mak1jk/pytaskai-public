"""
CLI DTO mappers for PyTaskAI adapter layer.

This module provides mapping between CLI command arguments and application DTOs,
following the same patterns as the MCP adapter to ensure identical business logic
execution and zero duplication between CLI and MCP interfaces.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pytaskai.application.dto.task_dto import (
    TaskCreateDTO,
    TaskListFiltersDTO,
    TaskUpdateDTO,
)


class CLITaskMapper:
    """
    Maps CLI command arguments to application DTOs.

    This mapper reuses the same DTO structures as the MCP adapter,
    ensuring identical data validation and business logic execution.
    """

    @staticmethod
    def map_list_args_to_filters_dto(
        assignee: Optional[str] = None,
        project: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_type: Optional[str] = None,
        tag: Optional[str] = None,
        due_before: Optional[str] = None,
        due_after: Optional[str] = None,
        parent_id: Optional[str] = None,
        include_completed: bool = True,
    ) -> TaskListFiltersDTO:
        """
        Map CLI list command arguments to TaskListFiltersDTO.

        Args:
            assignee: Filter by task assignee
            project: Filter by project name
            status: Filter by task status
            priority: Filter by priority level
            task_type: Filter by task type
            tag: Filter by tag name
            due_before: Filter tasks due before this date
            due_after: Filter tasks due after this date
            parent_id: Filter by parent task ID
            include_completed: Whether to include completed tasks

        Returns:
            TaskListFiltersDTO instance
        """
        return TaskListFiltersDTO(
            assignee=assignee,
            project=project,
            status=status,
            priority=priority,
            task_type=task_type,
            tag=tag,
            due_at_before=(
                CLITaskMapper._parse_datetime(due_before) if due_before else None
            ),
            due_at_after=(
                CLITaskMapper._parse_datetime(due_after) if due_after else None
            ),
            parent_id=parent_id,
            include_completed=include_completed,
        )

    @staticmethod
    def map_add_args_to_create_dto(
        title: str,
        project: str = "Default",
        task_type: str = "Task",
        status: str = "Todo",
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        size: Optional[str] = None,
    ) -> TaskCreateDTO:
        """
        Map CLI add command arguments to TaskCreateDTO.

        Args:
            title: Task title (required)
            project: Project name
            task_type: Type of task
            status: Initial status
            description: Task description
            assignee: Person assigned to task
            parent_id: Parent task ID
            tags: List of tags
            priority: Task priority
            start_date: Start date (ISO format)
            due_date: Due date (ISO format)
            size: Task size estimate

        Returns:
            TaskCreateDTO instance
        """
        return TaskCreateDTO(
            title=title,
            project=project,
            task_type=task_type,
            status=status,
            description=description,
            assignee=assignee,
            parent_id=parent_id,
            tags=tags or [],
            priority=priority,
            start_at=CLITaskMapper._parse_datetime(start_date) if start_date else None,
            due_at=CLITaskMapper._parse_datetime(due_date) if due_date else None,
            size=size,
        )

    @staticmethod
    def map_update_args_to_update_dto(
        task_id: str,
        title: Optional[str] = None,
        status: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        size: Optional[str] = None,
    ) -> TaskUpdateDTO:
        """
        Map CLI update command arguments to TaskUpdateDTO.

        Args:
            task_id: Task ID to update (required)
            title: New task title
            status: New task status
            description: New task description
            assignee: New assignee
            tags: New list of tags
            priority: New priority level
            start_date: New start date (ISO format)
            due_date: New due date (ISO format)
            size: New size estimate

        Returns:
            TaskUpdateDTO instance
        """
        return TaskUpdateDTO(
            task_id=task_id,
            title=title,
            status=status,
            description=description,
            assignee=assignee,
            tags=tags,
            priority=priority,
            start_at=CLITaskMapper._parse_datetime(start_date) if start_date else None,
            due_at=CLITaskMapper._parse_datetime(due_date) if due_date else None,
            size=size,
        )

    @staticmethod
    def _parse_datetime(date_str: str) -> Optional[datetime]:
        """
        Parse datetime string from CLI input.

        Supports multiple formats for user convenience:
        - ISO format: 2024-01-01T09:00:00
        - Date only: 2024-01-01 (defaults to 09:00:00)
        - Short format: 2024-01-01 09:00

        Args:
            date_str: Date string to parse

        Returns:
            Parsed datetime or None if invalid

        Raises:
            ValueError: If date format is invalid
        """
        if not date_str:
            return None

        # Remove 'Z' suffix if present
        if date_str.endswith("Z"):
            date_str = date_str[:-1]

        # Try different formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",  # ISO format
            "%Y-%m-%d %H:%M:%S",  # Space-separated
            "%Y-%m-%d %H:%M",  # Without seconds
            "%Y-%m-%d",  # Date only
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # If date only, set time to 09:00:00
                if fmt == "%Y-%m-%d":
                    parsed = parsed.replace(hour=9, minute=0, second=0)
                return parsed
            except ValueError:
                continue

        raise ValueError(
            f"Invalid date format: {date_str}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
        )


class CLIArgumentValidator:
    """
    Validates CLI command arguments before mapping to DTOs.

    This ensures consistent validation between CLI and MCP adapters
    by applying the same validation rules.
    """

    @staticmethod
    def validate_priority(priority: str) -> None:
        """
        Validate priority value.

        Args:
            priority: Priority value to validate

        Raises:
            ValueError: If priority is invalid
        """
        valid_priorities = ["Low", "Medium", "High", "Critical"]
        if priority not in valid_priorities:
            raise ValueError(
                f"Invalid priority '{priority}'. Must be one of: {', '.join(valid_priorities)}"
            )

    @staticmethod
    def validate_status(status: str) -> None:
        """
        Validate status value.

        Args:
            status: Status value to validate

        Raises:
            ValueError: If status is invalid
        """
        valid_statuses = ["Todo", "In Progress", "Done", "Blocked", "Cancelled"]
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
            )

    @staticmethod
    def validate_task_type(task_type: str) -> None:
        """
        Validate task type value.

        Args:
            task_type: Task type value to validate

        Raises:
            ValueError: If task type is invalid
        """
        valid_types = [
            "Task",
            "Bug",
            "Feature",
            "Enhancement",
            "Research",
            "Documentation",
        ]
        if task_type not in valid_types:
            raise ValueError(
                f"Invalid task type '{task_type}'. Must be one of: {', '.join(valid_types)}"
            )

    @staticmethod
    def validate_size(size: str) -> None:
        """
        Validate size value.

        Args:
            size: Size value to validate

        Raises:
            ValueError: If size is invalid
        """
        valid_sizes = ["XS", "S", "M", "L", "XL"]
        if size not in valid_sizes:
            raise ValueError(
                f"Invalid size '{size}'. Must be one of: {', '.join(valid_sizes)}"
            )

    @staticmethod
    def validate_tags(tags: List[str]) -> None:
        """
        Validate tags list.

        Args:
            tags: List of tags to validate

        Raises:
            ValueError: If tags are invalid
        """
        if not isinstance(tags, list):
            raise ValueError("Tags must be a list")

        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError("All tags must be non-empty strings")

    @staticmethod
    def validate_required_field(value: Any, field_name: str) -> None:
        """
        Validate required field is present and not empty.

        Args:
            value: Field value to validate
            field_name: Name of the field for error messages

        Raises:
            ValueError: If field is missing or empty
        """
        if value is None:
            raise ValueError(f"Field '{field_name}' is required")

        if isinstance(value, str) and not value.strip():
            raise ValueError(f"Field '{field_name}' cannot be empty")


def validate_and_map_create_args(**kwargs) -> TaskCreateDTO:
    """
    Validate CLI arguments and map to TaskCreateDTO.

    This convenience function combines validation and mapping for
    task creation commands.

    Args:
        **kwargs: CLI command arguments

    Returns:
        Validated TaskCreateDTO instance

    Raises:
        ValueError: If validation fails
    """
    # Validate required fields
    CLIArgumentValidator.validate_required_field(kwargs.get("title"), "title")

    # Validate optional fields
    if priority := kwargs.get("priority"):
        CLIArgumentValidator.validate_priority(priority)

    if status := kwargs.get("status", "Todo"):
        CLIArgumentValidator.validate_status(status)

    if task_type := kwargs.get("task_type", "Task"):
        CLIArgumentValidator.validate_task_type(task_type)

    if size := kwargs.get("size"):
        CLIArgumentValidator.validate_size(size)

    if tags := kwargs.get("tags"):
        CLIArgumentValidator.validate_tags(tags)

    return CLITaskMapper.map_add_args_to_create_dto(**kwargs)


def validate_and_map_update_args(**kwargs) -> TaskUpdateDTO:
    """
    Validate CLI arguments and map to TaskUpdateDTO.

    This convenience function combines validation and mapping for
    task update commands.

    Args:
        **kwargs: CLI command arguments

    Returns:
        Validated TaskUpdateDTO instance

    Raises:
        ValueError: If validation fails
    """
    # Validate required fields
    CLIArgumentValidator.validate_required_field(kwargs.get("task_id"), "task_id")

    # Validate optional fields
    if priority := kwargs.get("priority"):
        CLIArgumentValidator.validate_priority(priority)

    if status := kwargs.get("status"):
        CLIArgumentValidator.validate_status(status)

    if task_type := kwargs.get("task_type"):
        CLIArgumentValidator.validate_task_type(task_type)

    if size := kwargs.get("size"):
        CLIArgumentValidator.validate_size(size)

    if tags := kwargs.get("tags"):
        CLIArgumentValidator.validate_tags(tags)

    return CLITaskMapper.map_update_args_to_update_dto(**kwargs)
