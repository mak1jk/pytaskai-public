"""
Output formatters for PyTaskAI CLI.

This module provides different output formatting strategies for CLI results,
following the Strategy pattern to allow flexible output formatting based on
user preferences (table, JSON, plain text).
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import click
from tabulate import tabulate

from pytaskai.application.dto.task_dto import TaskResponseDTO


class OutputFormatter(ABC):
    """
    Abstract base class for output formatters.

    This follows the Strategy pattern, allowing different formatting
    implementations to be used interchangeably based on user preference.
    """

    @abstractmethod
    def format_task(self, task: TaskResponseDTO) -> str:
        """Format a single task for output."""
        pass

    @abstractmethod
    def format_task_list(self, tasks: List[TaskResponseDTO]) -> str:
        """Format a list of tasks for output."""
        pass

    @abstractmethod
    def format_success_message(
        self, message: str, data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a success message with optional data."""
        pass

    @abstractmethod
    def format_error_message(self, message: str) -> str:
        """Format an error message."""
        pass


class TableFormatter(OutputFormatter):
    """
    Table formatter for human-readable output.

    Uses tabulate library to create well-formatted tables that are
    easy to read in terminal environments.
    """

    def format_task(self, task: TaskResponseDTO) -> str:
        """Format a single task as a detailed table."""
        # Basic task information
        basic_info = [
            ["ID", task.id],
            ["Title", task.title],
            ["Status", task.status],
            ["Priority", task.priority or "None"],
            ["Project", task.project or "Default"],
            ["Type", task.task_type or "Task"],
        ]

        # Optional fields
        if task.description:
            basic_info.append(
                ["Description", self._truncate_text(task.description, 60)]
            )

        if task.assignee:
            basic_info.append(["Assignee", task.assignee])

        if task.parent_id:
            basic_info.append(["Parent ID", task.parent_id])

        # Dates
        if task.created_at:
            basic_info.append(["Created", self._format_datetime(task.created_at)])

        if task.updated_at:
            basic_info.append(["Updated", self._format_datetime(task.updated_at)])

        if task.start_at:
            basic_info.append(["Start Date", self._format_datetime(task.start_at)])

        if task.due_at:
            basic_info.append(["Due Date", self._format_datetime(task.due_at)])

        # Tags
        if task.tags:
            basic_info.append(["Tags", ", ".join(task.tags)])

        # Size
        if task.size:
            basic_info.append(["Size", task.size])

        return tabulate(basic_info, headers=["Field", "Value"], tablefmt="grid")

    def format_task_list(self, tasks: List[TaskResponseDTO]) -> str:
        """Format a list of tasks as a compact table."""
        if not tasks:
            return "No tasks found."

        # Prepare table data
        table_data = []
        for task in tasks:
            row = [
                task.id,
                self._truncate_text(task.title, 40),
                task.status,
                task.priority or "",
                task.project or "Default",
                self._format_datetime(task.due_at) if task.due_at else "",
                task.assignee or "",
            ]
            table_data.append(row)

        headers = [
            "ID",
            "Title",
            "Status",
            "Priority",
            "Project",
            "Due Date",
            "Assignee",
        ]
        return tabulate(table_data, headers=headers, tablefmt="grid")

    def format_success_message(
        self, message: str, data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a success message with optional data."""
        result = f"✅ {message}"

        if data:
            # Add key information from data
            if "task_id" in data:
                result += f" (ID: {data['task_id']})"
            elif "count" in data:
                result += f" ({data['count']} items)"

        return result

    def format_error_message(self, message: str) -> str:
        """Format an error message."""
        return f"❌ Error: {message}"

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for table display."""
        return dt.strftime("%Y-%m-%d %H:%M")


class JSONFormatter(OutputFormatter):
    """
    JSON formatter for machine-readable output.

    Provides structured JSON output suitable for scripting and
    automation use cases.
    """

    def format_task(self, task: TaskResponseDTO) -> str:
        """Format a single task as JSON."""
        return json.dumps(self._task_to_dict(task), indent=2, default=str)

    def format_task_list(self, tasks: List[TaskResponseDTO]) -> str:
        """Format a list of tasks as JSON array."""
        task_dicts = [self._task_to_dict(task) for task in tasks]
        return json.dumps(task_dicts, indent=2, default=str)

    def format_success_message(
        self, message: str, data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a success message as JSON."""
        result = {
            "success": True,
            "message": message,
        }

        if data:
            result["data"] = data

        return json.dumps(result, indent=2, default=str)

    def format_error_message(self, message: str) -> str:
        """Format an error message as JSON."""
        result = {
            "success": False,
            "error": message,
        }
        return json.dumps(result, indent=2)

    def _task_to_dict(self, task: TaskResponseDTO) -> Dict[str, Any]:
        """Convert TaskResponseDTO to dictionary for JSON serialization."""
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "project": task.project,
            "task_type": task.task_type,
            "assignee": task.assignee,
            "parent_id": task.parent_id,
            "tags": task.tags or [],
            "size": task.size,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "start_at": task.start_at,
            "due_at": task.due_at,
        }


class PlainFormatter(OutputFormatter):
    """
    Plain text formatter for minimal output.

    Provides simple, script-friendly output without decorative formatting,
    suitable for parsing and basic display needs.
    """

    def format_task(self, task: TaskResponseDTO) -> str:
        """Format a single task as plain text."""
        lines = [
            f"ID: {task.id}",
            f"Title: {task.title}",
            f"Status: {task.status}",
        ]

        if task.priority:
            lines.append(f"Priority: {task.priority}")

        if task.project:
            lines.append(f"Project: {task.project}")

        if task.assignee:
            lines.append(f"Assignee: {task.assignee}")

        if task.description:
            lines.append(f"Description: {task.description}")

        if task.tags:
            lines.append(f"Tags: {', '.join(task.tags)}")

        return "\n".join(lines)

    def format_task_list(self, tasks: List[TaskResponseDTO]) -> str:
        """Format a list of tasks as plain text."""
        if not tasks:
            return "No tasks found."

        lines = []
        for task in tasks:
            line = f"{task.id}: {task.title} [{task.status}]"
            if task.priority:
                line += f" ({task.priority})"
            lines.append(line)

        return "\n".join(lines)

    def format_success_message(
        self, message: str, data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a success message as plain text."""
        result = f"SUCCESS: {message}"

        if data and "task_id" in data:
            result += f" (ID: {data['task_id']})"

        return result

    def format_error_message(self, message: str) -> str:
        """Format an error message as plain text."""
        return f"ERROR: {message}"


def get_formatter(format_type: str) -> OutputFormatter:
    """
    Factory function to get appropriate formatter based on format type.

    Args:
        format_type: Format type ("table", "json", or "plain")

    Returns:
        Appropriate OutputFormatter instance

    Raises:
        ValueError: If format_type is not supported
    """
    formatters = {
        "table": TableFormatter,
        "json": JSONFormatter,
        "plain": PlainFormatter,
    }

    if format_type not in formatters:
        raise ValueError(
            f"Unsupported format type '{format_type}'. "
            f"Must be one of: {', '.join(formatters.keys())}"
        )

    return formatters[format_type]()


def format_output(
    data: Any,
    format_type: str,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None,
) -> str:
    """
    Convenience function to format output based on data type and format preference.

    Args:
        data: Data to format (TaskResponseDTO, List[TaskResponseDTO], or dict)
        format_type: Output format ("table", "json", or "plain")
        success_message: Optional success message to include
        error_message: Optional error message to format

    Returns:
        Formatted output string
    """
    formatter = get_formatter(format_type)

    if error_message:
        return formatter.format_error_message(error_message)

    if isinstance(data, TaskResponseDTO):
        if success_message and format_type == "json":
            # For JSON format, wrap task data in success response
            task_dict = JSONFormatter()._task_to_dict(data)
            return formatter.format_success_message(success_message, task_dict)
        else:
            result = formatter.format_task(data)
    elif isinstance(data, list) and all(
        isinstance(item, TaskResponseDTO) for item in data
    ):
        if success_message and format_type == "json":
            # For JSON format, wrap task list in success response
            task_dicts = [JSONFormatter()._task_to_dict(task) for task in data]
            return formatter.format_success_message(success_message, task_dicts)
        else:
            result = formatter.format_task_list(data)
    else:
        # Generic data formatting
        if success_message:
            return formatter.format_success_message(
                success_message, data if isinstance(data, dict) else None
            )
        else:
            # Fallback to JSON for unknown data types
            json_formatter = JSONFormatter()
            return json_formatter.format_success_message(
                "Operation completed", {"result": data}
            )

    # Add success message if provided (for non-JSON formats)
    if success_message and format_type != "json":
        success_line = formatter.format_success_message(success_message)
        return f"{success_line}\n\n{result}"

    return result
