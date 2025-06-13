"""
MCP tools for PyTaskAI task management.

This module implements the 6 essential MCP tools for task management,
following the Command pattern and Adapter pattern to expose application
layer use cases as MCP protocol-compliant tools.
"""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from pytaskai.adapters.mcp.dependency_injection import MCPContainer
from pytaskai.adapters.mcp.dto_mappers import MCPTaskMapper
from pytaskai.adapters.mcp.error_handlers import MCPErrorHandler, mcp_error_handler


class TaskMCPTools:
    """
    MCP tools for task management operations.

    This class implements the 6 essential MCP tools following the
    Command pattern, where each tool is a command that encapsulates
    a request to the application layer.
    """

    def __init__(self, container: MCPContainer, mcp_app: FastMCP) -> None:
        """
        Initialize task MCP tools with dependency injection container.

        Args:
            container: MCP dependency injection container
            mcp_app: FastMCP application instance
        """
        self._container = container
        self._app_container = container.application_container
        self._mcp_app = mcp_app

    @mcp_error_handler
    async def list_tasks(
        self,
        assignee: Optional[str] = None,
        project: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_type: Optional[str] = None,
        tag: Optional[str] = None,
        due_at_before: Optional[str] = None,
        due_at_after: Optional[str] = None,
        parent_id: Optional[str] = None,
        include_completed: bool = True,
    ) -> Dict[str, Any]:
        """
        List tasks with optional filtering.

        This tool provides comprehensive task listing with multiple filter
        options, supporting all common task management queries.

        Args:
            assignee: Filter by task assignee
            project: Filter by project name
            status: Filter by task status (Todo, In Progress, Done, etc.)
            priority: Filter by priority (Low, Medium, High, Critical)
            task_type: Filter by task type (Task, Bug, Feature, etc.)
            tag: Filter by tag name
            due_at_before: Filter tasks due before this date (ISO format)
            due_at_after: Filter tasks due after this date (ISO format)
            parent_id: Filter by parent task ID (for subtasks)
            include_completed: Whether to include completed tasks

        Returns:
            Dictionary containing list of tasks and metadata
        """
        MCPErrorHandler.log_tool_execution(
            "list_tasks",
            {
                "assignee": assignee,
                "project": project,
                "status": status,
                "priority": priority,
                "task_type": task_type,
                "tag": tag,
                "parent_id": parent_id,
                "include_completed": include_completed,
            },
        )

        # Build filters DTO
        filters_data = {
            "assignee": assignee,
            "project": project,
            "status": status,
            "priority": priority,
            "task_type": task_type,
            "tag": tag,
            "due_at_before": due_at_before,
            "due_at_after": due_at_after,
            "parent_id": parent_id,
            "include_completed": include_completed,
        }

        filters_dto = MCPTaskMapper.map_filters_request_to_dto(filters_data)

        # Execute use case
        task_use_case = self._app_container.task_management_use_case
        tasks = await task_use_case.list_tasks(filters_dto)

        # Map to response format
        response = MCPTaskMapper.map_task_list_to_response(tasks)

        return MCPErrorHandler.create_success_response(
            response, f"Found {len(tasks)} tasks"
        )

    @mcp_error_handler
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific task.

        This tool retrieves complete task details including all metadata,
        relationships, and computed properties.

        Args:
            task_id: The unique identifier of the task

        Returns:
            Dictionary containing task details

        Raises:
            MCPTaskNotFoundError: If task does not exist
        """
        MCPErrorHandler.log_tool_execution("get_task", {"task_id": task_id})

        # Validate required fields
        MCPErrorHandler.validate_required_fields({"task_id": task_id}, ["task_id"])

        # Execute use case
        task_use_case = self._app_container.task_management_use_case
        task_dto = await task_use_case.get_task(task_id)

        if not task_dto:
            from pytaskai.adapters.mcp.error_handlers import MCPTaskNotFoundError

            raise MCPTaskNotFoundError(task_id)

        # Map to response format
        task_data = MCPTaskMapper.map_task_dto_to_response(task_dto)

        return MCPErrorHandler.create_success_response(
            task_data, f"Retrieved task {task_id}"
        )

    @mcp_error_handler
    async def add_task(
        self,
        title: str,
        project: str = "Default",
        task_type: str = "Task",
        status: str = "Todo",
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        start_at: Optional[str] = None,
        due_at: Optional[str] = None,
        size: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new task with specified attributes.

        This tool creates a new task in the system with comprehensive
        metadata support including dates, priorities, and relationships.

        Args:
            title: The task title (required)
            project: Project name (defaults to "Default")
            task_type: Type of task (Task, Bug, Feature, Enhancement, etc.)
            status: Initial status (Todo, In Progress, Done, etc.)
            description: Detailed task description
            assignee: Person assigned to the task
            parent_id: ID of parent task (for subtasks)
            tags: List of tags for categorization
            priority: Task priority (Low, Medium, High, Critical)
            start_at: Start date in ISO format
            due_at: Due date in ISO format
            size: Task size estimate (XS, S, M, L, XL)

        Returns:
            Dictionary containing created task details
        """
        request_data = {
            "title": title,
            "project": project,
            "task_type": task_type,
            "status": status,
            "description": description,
            "assignee": assignee,
            "parent_id": parent_id,
            "tags": tags or [],
            "priority": priority,
            "start_at": start_at,
            "due_at": due_at,
            "size": size,
        }

        MCPErrorHandler.log_tool_execution("add_task", request_data)

        # Validate required fields
        MCPErrorHandler.validate_required_fields(request_data, ["title"])

        # Validate field types
        MCPErrorHandler.validate_field_type(request_data, "tags", list)

        # Validate field choices
        if priority:
            MCPErrorHandler.validate_field_choices(
                request_data, "priority", ["Low", "Medium", "High", "Critical"]
            )

        # Map to DTO
        create_dto = MCPTaskMapper.map_create_request_to_dto(request_data)

        # Execute use case
        task_use_case = self._app_container.task_management_use_case
        created_task = await task_use_case.create_task(create_dto)

        # Map to response format
        task_data = MCPTaskMapper.map_task_dto_to_response(created_task)

        return MCPErrorHandler.create_success_response(
            task_data, f"Created task '{title}'"
        )

    @mcp_error_handler
    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        status: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
        start_at: Optional[str] = None,
        due_at: Optional[str] = None,
        size: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing task with new attributes.

        This tool allows partial updates to existing tasks, only modifying
        the fields that are explicitly provided.

        Args:
            task_id: The unique identifier of the task to update (required)
            title: New task title
            status: New task status
            description: New task description
            assignee: New assignee
            tags: New list of tags (replaces existing tags)
            priority: New priority level
            start_at: New start date in ISO format
            due_at: New due date in ISO format
            size: New size estimate

        Returns:
            Dictionary containing updated task details
        """
        request_data = {
            "task_id": task_id,
            "title": title,
            "status": status,
            "description": description,
            "assignee": assignee,
            "tags": tags,
            "priority": priority,
            "start_at": start_at,
            "due_at": due_at,
            "size": size,
        }

        MCPErrorHandler.log_tool_execution("update_task", request_data)

        # Validate required fields
        MCPErrorHandler.validate_required_fields(request_data, ["task_id"])

        # Validate field choices
        if priority:
            MCPErrorHandler.validate_field_choices(
                request_data, "priority", ["Low", "Medium", "High", "Critical"]
            )

        # Map to DTO
        update_dto = MCPTaskMapper.map_update_request_to_dto(request_data)

        # Execute use case
        task_use_case = self._app_container.task_management_use_case
        updated_task = await task_use_case.update_task(update_dto)

        # Map to response format
        task_data = MCPTaskMapper.map_task_dto_to_response(updated_task)

        return MCPErrorHandler.create_success_response(
            task_data, f"Updated task {task_id}"
        )

    @mcp_error_handler
    async def delete_task(self, task_id: str) -> Dict[str, Any]:
        """
        Delete a task from the system.

        This tool permanently removes a task and all its data from the system.
        Use with caution as this operation cannot be undone.

        Args:
            task_id: The unique identifier of the task to delete

        Returns:
            Dictionary confirming the deletion
        """
        MCPErrorHandler.log_tool_execution("delete_task", {"task_id": task_id})

        # Validate required fields
        MCPErrorHandler.validate_required_fields({"task_id": task_id}, ["task_id"])

        # Execute use case
        task_use_case = self._app_container.task_management_use_case
        success = await task_use_case.delete_task(task_id)

        if not success:
            from pytaskai.adapters.mcp.error_handlers import MCPTaskNotFoundError

            raise MCPTaskNotFoundError(task_id)

        return MCPErrorHandler.create_success_response(
            {"deleted": True, "task_id": task_id}, f"Deleted task {task_id}"
        )

    @mcp_error_handler
    async def generate_subtasks(
        self,
        parent_task_id: str,
        breakdown_approach: str = "functional",
        max_subtasks: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate subtasks for a parent task using AI (future implementation).

        This tool will use AI services to intelligently break down complex
        tasks into manageable subtasks. Currently returns a placeholder
        response indicating the feature is planned but not yet implemented.

        Args:
            parent_task_id: ID of the task to break down
            breakdown_approach: Approach for breakdown (functional, temporal, etc.)
            max_subtasks: Maximum number of subtasks to generate

        Returns:
            Dictionary containing generated subtasks or placeholder response
        """
        MCPErrorHandler.log_tool_execution(
            "generate_subtasks",
            {
                "parent_task_id": parent_task_id,
                "breakdown_approach": breakdown_approach,
                "max_subtasks": max_subtasks,
            },
        )

        # Validate required fields
        MCPErrorHandler.validate_required_fields(
            {"parent_task_id": parent_task_id}, ["parent_task_id"]
        )

        # Check if AI services are available
        if not self._app_container.has_ai_services():
            return MCPErrorHandler.create_success_response(
                {
                    "generated_subtasks": [],
                    "message": "AI services not configured. Subtask generation requires AI integration.",
                    "parent_task_id": parent_task_id,
                },
                "AI subtask generation not available",
            )

        # Future implementation: Use AI task generation use case
        # For now, return placeholder response
        return MCPErrorHandler.create_success_response(
            {
                "generated_subtasks": [],
                "message": "AI subtask generation is planned but not yet implemented.",
                "parent_task_id": parent_task_id,
                "breakdown_approach": breakdown_approach,
                "max_subtasks": max_subtasks,
            },
            "Subtask generation planned for future release",
        )

    def register_tools(self) -> None:
        """Register all task tools with the FastMCP application."""
        # Register list_tasks tool
        self._mcp_app.tool(
            name="list_tasks", description="List tasks with optional filtering"
        )(self.list_tasks)

        # Register get_task tool
        self._mcp_app.tool(
            name="get_task",
            description="Get detailed information about a specific task",
        )(self.get_task)

        # Register add_task tool
        self._mcp_app.tool(
            name="add_task", description="Create a new task with specified attributes"
        )(self.add_task)

        # Register update_task tool
        self._mcp_app.tool(
            name="update_task",
            description="Update an existing task with new attributes",
        )(self.update_task)

        # Register delete_task tool
        self._mcp_app.tool(
            name="delete_task", description="Delete a task from the system"
        )(self.delete_task)

        # Register generate_subtasks tool
        self._mcp_app.tool(
            name="generate_subtasks",
            description="Generate subtasks for a parent task using AI",
        )(self.generate_subtasks)


def register_task_tools(container: MCPContainer, mcp_app: FastMCP) -> TaskMCPTools:
    """
    Register all task-related MCP tools with the FastMCP server.

    This function creates the TaskMCPTools instance and registers
    all tools with the MCP server, following the Factory pattern.

    Args:
        container: MCP dependency injection container
        mcp_app: FastMCP application instance

    Returns:
        Configured TaskMCPTools instance
    """
    task_tools = TaskMCPTools(container, mcp_app)
    task_tools.register_tools()
    return task_tools
