"""
DTO mappers for MCP adapter layer.

This module provides mapping utilities between MCP protocol request/response
formats and the application layer DTOs, following the Adapter pattern to
isolate protocol-specific concerns from business logic.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pytaskai.application.dto.task_dto import (
    DocumentCreateDTO,
    DocumentResponseDTO,
    DocumentUpdateDTO,
    TaskCreateDTO,
    TaskListFiltersDTO,
    TaskResponseDTO,
    TaskUpdateDTO,
    WorkspaceSummaryDTO,
)


class MCPTaskMapper:
    """Mapper for Task-related MCP requests and responses."""

    @staticmethod
    def map_create_request_to_dto(mcp_request: Dict[str, Any]) -> TaskCreateDTO:
        """
        Map MCP create task request to TaskCreateDTO.

        Args:
            mcp_request: MCP request data

        Returns:
            TaskCreateDTO instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Parse datetime fields if provided
        start_at = None
        if mcp_request.get("start_at"):
            start_at = MCPTaskMapper._parse_datetime(mcp_request["start_at"])

        due_at = None
        if mcp_request.get("due_at"):
            due_at = MCPTaskMapper._parse_datetime(mcp_request["due_at"])

        # Parse tags as list
        tags = mcp_request.get("tags", [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

        return TaskCreateDTO(
            title=mcp_request["title"],
            project=mcp_request.get("project", "Default"),
            task_type=mcp_request.get("task_type", "Task"),
            status=mcp_request.get("status", "Todo"),
            description=mcp_request.get("description"),
            assignee=mcp_request.get("assignee"),
            parent_id=mcp_request.get("parent_id"),
            tags=tags,
            priority=mcp_request.get("priority"),
            start_at=start_at,
            due_at=due_at,
            size=mcp_request.get("size"),
        )

    @staticmethod
    def map_update_request_to_dto(mcp_request: Dict[str, Any]) -> TaskUpdateDTO:
        """
        Map MCP update task request to TaskUpdateDTO.

        Args:
            mcp_request: MCP request data

        Returns:
            TaskUpdateDTO instance

        Raises:
            ValueError: If task_id is missing
        """
        # Parse datetime fields if provided
        start_at = None
        if mcp_request.get("start_at"):
            start_at = MCPTaskMapper._parse_datetime(mcp_request["start_at"])

        due_at = None
        if mcp_request.get("due_at"):
            due_at = MCPTaskMapper._parse_datetime(mcp_request["due_at"])

        # Parse tags as list
        tags = None
        if "tags" in mcp_request:
            tags = mcp_request["tags"]
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

        return TaskUpdateDTO(
            task_id=mcp_request["task_id"],
            title=mcp_request.get("title"),
            status=mcp_request.get("status"),
            description=mcp_request.get("description"),
            assignee=mcp_request.get("assignee"),
            tags=tags,
            priority=mcp_request.get("priority"),
            start_at=start_at,
            due_at=due_at,
            size=mcp_request.get("size"),
        )

    @staticmethod
    def map_filters_request_to_dto(mcp_request: Dict[str, Any]) -> TaskListFiltersDTO:
        """
        Map MCP list tasks request to TaskListFiltersDTO.

        Args:
            mcp_request: MCP request data

        Returns:
            TaskListFiltersDTO instance
        """
        # Parse datetime fields if provided
        due_at_before = None
        if mcp_request.get("due_at_before"):
            due_at_before = MCPTaskMapper._parse_datetime(mcp_request["due_at_before"])

        due_at_after = None
        if mcp_request.get("due_at_after"):
            due_at_after = MCPTaskMapper._parse_datetime(mcp_request["due_at_after"])

        return TaskListFiltersDTO(
            assignee=mcp_request.get("assignee"),
            project=mcp_request.get("project"),
            status=mcp_request.get("status"),
            priority=mcp_request.get("priority"),
            task_type=mcp_request.get("task_type"),
            tag=mcp_request.get("tag"),
            due_at_before=due_at_before,
            due_at_after=due_at_after,
            parent_id=mcp_request.get("parent_id"),
            include_completed=mcp_request.get("include_completed", True),
        )

    @staticmethod
    def map_task_dto_to_response(task_dto: TaskResponseDTO) -> Dict[str, Any]:
        """
        Map TaskResponseDTO to MCP response format.

        Args:
            task_dto: TaskResponseDTO instance

        Returns:
            MCP response dictionary
        """
        return {
            "id": task_dto.id,
            "title": task_dto.title,
            "external_url": task_dto.external_url,
            "project": task_dto.project,
            "task_type": task_dto.task_type,
            "status": task_dto.status,
            "assignee": task_dto.assignee,
            "parent_id": task_dto.parent_id,
            "tags": task_dto.tags,
            "priority": task_dto.priority,
            "start_at": MCPTaskMapper._format_datetime(task_dto.start_at),
            "due_at": MCPTaskMapper._format_datetime(task_dto.due_at),
            "size": task_dto.size,
            "description": task_dto.description,
            "created_at": MCPTaskMapper._format_datetime(task_dto.created_at),
            "updated_at": MCPTaskMapper._format_datetime(task_dto.updated_at),
            "is_completed": task_dto.is_completed,
            "is_overdue": task_dto.is_overdue,
            "is_high_priority": task_dto.is_high_priority,
        }

    @staticmethod
    def map_task_list_to_response(tasks: List[TaskResponseDTO]) -> Dict[str, Any]:
        """
        Map list of TaskResponseDTO to MCP response format.

        Args:
            tasks: List of TaskResponseDTO instances

        Returns:
            MCP response dictionary with task list
        """
        return {
            "tasks": [MCPTaskMapper.map_task_dto_to_response(task) for task in tasks],
            "count": len(tasks),
        }

    @staticmethod
    def _parse_datetime(datetime_str: str) -> datetime:
        """Parse datetime string in various formats."""
        # Try ISO format first
        try:
            return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse datetime: {datetime_str}")

    @staticmethod
    def _format_datetime(dt: Optional[datetime]) -> Optional[str]:
        """Format datetime for MCP response."""
        if dt is None:
            return None
        return dt.isoformat()


class MCPDocumentMapper:
    """Mapper for Document-related MCP requests and responses."""

    @staticmethod
    def map_create_request_to_dto(mcp_request: Dict[str, Any]) -> DocumentCreateDTO:
        """
        Map MCP create document request to DocumentCreateDTO.

        Args:
            mcp_request: MCP request data

        Returns:
            DocumentCreateDTO instance
        """
        return DocumentCreateDTO(
            title=mcp_request["title"],
            text=mcp_request.get("text"),
            folder=mcp_request.get("folder"),
            is_draft=mcp_request.get("is_draft", False),
        )

    @staticmethod
    def map_update_request_to_dto(mcp_request: Dict[str, Any]) -> DocumentUpdateDTO:
        """
        Map MCP update document request to DocumentUpdateDTO.

        Args:
            mcp_request: MCP request data

        Returns:
            DocumentUpdateDTO instance
        """
        return DocumentUpdateDTO(
            document_id=mcp_request["document_id"],
            title=mcp_request.get("title"),
            text=mcp_request.get("text"),
            folder=mcp_request.get("folder"),
            is_draft=mcp_request.get("is_draft"),
        )

    @staticmethod
    def map_document_dto_to_response(doc_dto: DocumentResponseDTO) -> Dict[str, Any]:
        """
        Map DocumentResponseDTO to MCP response format.

        Args:
            doc_dto: DocumentResponseDTO instance

        Returns:
            MCP response dictionary
        """
        return {
            "id": doc_dto.id,
            "title": doc_dto.title,
            "text": doc_dto.text,
            "folder": doc_dto.folder,
            "is_draft": doc_dto.is_draft,
            "in_trash": doc_dto.in_trash,
            "created_at": MCPTaskMapper._format_datetime(doc_dto.created_at),
            "updated_at": MCPTaskMapper._format_datetime(doc_dto.updated_at),
            "is_empty": doc_dto.is_empty,
        }


class MCPWorkspaceMapper:
    """Mapper for Workspace-related MCP requests and responses."""

    @staticmethod
    def map_summary_dto_to_response(summary_dto: WorkspaceSummaryDTO) -> Dict[str, Any]:
        """
        Map WorkspaceSummaryDTO to MCP response format.

        Args:
            summary_dto: WorkspaceSummaryDTO instance

        Returns:
            MCP response dictionary
        """
        return {
            "total_tasks": summary_dto.total_tasks,
            "completed_tasks": summary_dto.completed_tasks,
            "overdue_tasks": summary_dto.overdue_tasks,
            "high_priority_tasks": summary_dto.high_priority_tasks,
            "completion_rate": summary_dto.completion_rate,
            "total_docs": summary_dto.total_docs,
            "draft_docs": summary_dto.draft_docs,
            "empty_docs": summary_dto.empty_docs,
            "assignees_count": summary_dto.assignees_count,
            "projects_count": summary_dto.projects_count,
        }


class MCPErrorMapper:
    """Mapper for error responses."""

    @staticmethod
    def map_error_to_response(
        error: Exception, error_code: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """
        Map exception to MCP error response format.

        Args:
            error: Exception instance
            error_code: Error code for categorization

        Returns:
            MCP error response dictionary
        """
        return {
            "error": {
                "code": error_code,
                "message": str(error),
                "details": {
                    "type": type(error).__name__,
                    "args": error.args if error.args else [],
                },
            }
        }

    @staticmethod
    def map_validation_error_to_response(field: str, message: str) -> Dict[str, Any]:
        """
        Map validation error to MCP error response format.

        Args:
            field: Field name that failed validation
            message: Validation error message

        Returns:
            MCP error response dictionary
        """
        return {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": f"Validation failed for field '{field}': {message}",
                "details": {"field": field, "type": "ValidationError"},
            }
        }
