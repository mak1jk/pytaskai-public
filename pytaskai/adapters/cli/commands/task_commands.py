"""
Task management CLI commands for PyTaskAI.

This module implements CLI commands for task management operations,
following the Command pattern and ensuring zero duplication with MCP
adapter by reusing the same application layer use cases.
"""

import asyncio
import sys
from typing import List, Optional

import click

from pytaskai.adapters.cli.dto_mappers import (
    CLITaskMapper,
    validate_and_map_create_args,
    validate_and_map_update_args,
)
from pytaskai.adapters.cli.formatters import format_output


def async_command(func):
    """Decorator to make Click commands work with async functions."""

    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@click.group()
def task_commands():
    """Task management commands."""
    pass


@task_commands.command("list")
@click.option("--assignee", "-a", help="Filter by assignee")
@click.option("--project", "-p", help="Filter by project")
@click.option("--status", "-s", help="Filter by status")
@click.option("--priority", help="Filter by priority")
@click.option("--type", "task_type", help="Filter by task type")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--due-before", help="Filter tasks due before date (YYYY-MM-DD)")
@click.option("--due-after", help="Filter tasks due after date (YYYY-MM-DD)")
@click.option("--parent-id", help="Filter by parent task ID")
@click.option(
    "--include-completed/--exclude-completed",
    default=True,
    help="Include completed tasks",
)
@click.pass_obj
@async_command
async def list_tasks(
    cli_ctx,
    assignee: Optional[str],
    project: Optional[str],
    status: Optional[str],
    priority: Optional[str],
    task_type: Optional[str],
    tag: Optional[str],
    due_before: Optional[str],
    due_after: Optional[str],
    parent_id: Optional[str],
    include_completed: bool,
):
    """
    List tasks with optional filtering.

    Examples:
        pytaskai task list
        pytaskai task list --status Todo --priority High
        pytaskai task list --assignee "John Doe" --project "Website"
        pytaskai task list --due-before 2024-12-31
    """
    try:
        # Map CLI arguments to DTO (same as MCP adapter)
        filters_dto = CLITaskMapper.map_list_args_to_filters_dto(
            assignee=assignee,
            project=project,
            status=status,
            priority=priority,
            task_type=task_type,
            tag=tag,
            due_before=due_before,
            due_after=due_after,
            parent_id=parent_id,
            include_completed=include_completed,
        )

        # Execute use case (same as MCP adapter)
        task_use_case = cli_ctx.container.application_container.task_management_use_case
        tasks = await task_use_case.list_tasks(filters_dto)

        # Format output
        output = format_output(
            tasks,
            cli_ctx.config.output_format,
            success_message=f"Found {len(tasks)} tasks",
        )
        click.echo(output)

    except Exception as e:
        error_output = format_output(
            None, cli_ctx.config.output_format, error_message=str(e)
        )
        click.echo(error_output, err=True)
        sys.exit(1)


@task_commands.command("get")
@click.argument("task_id")
@click.pass_obj
@async_command
async def get_task(cli_ctx, task_id: str):
    """
    Get detailed information about a specific task.

    TASK_ID: The unique identifier of the task

    Examples:
        pytaskai task get task123
        pytaskai task get abcd1234567
    """
    try:
        # Execute use case (same as MCP adapter)
        task_use_case = cli_ctx.container.application_container.task_management_use_case
        task_dto = await task_use_case.get_task(task_id)

        if not task_dto:
            raise ValueError(f"Task not found: {task_id}")

        # Format output
        output = format_output(
            task_dto,
            cli_ctx.config.output_format,
            success_message=f"Retrieved task {task_id}",
        )
        click.echo(output)

    except Exception as e:
        error_output = format_output(
            None, cli_ctx.config.output_format, error_message=str(e)
        )
        click.echo(error_output, err=True)
        sys.exit(1)


@task_commands.command("add")
@click.argument("title")
@click.option("--project", "-p", default="Default", help="Project name")
@click.option("--type", "task_type", default="Task", help="Task type")
@click.option("--status", "-s", default="Todo", help="Initial status")
@click.option("--description", "-d", help="Task description")
@click.option("--assignee", "-a", help="Assignee name")
@click.option("--parent-id", help="Parent task ID")
@click.option("--tags", help="Comma-separated list of tags")
@click.option("--priority", help="Task priority (Low, Medium, High, Critical)")
@click.option("--start-date", help="Start date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
@click.option("--due-date", help="Due date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
@click.option("--size", help="Task size (XS, S, M, L, XL)")
@click.pass_obj
@async_command
async def add_task(
    cli_ctx,
    title: str,
    project: str,
    task_type: str,
    status: str,
    description: Optional[str],
    assignee: Optional[str],
    parent_id: Optional[str],
    tags: Optional[str],
    priority: Optional[str],
    start_date: Optional[str],
    due_date: Optional[str],
    size: Optional[str],
):
    """
    Create a new task with specified attributes.

    TITLE: The task title (required)

    Examples:
        pytaskai task add "Complete documentation"
        pytaskai task add "Fix login bug" --type Bug --priority High
        pytaskai task add "Feature request" --assignee "Jane Doe" --due-date 2024-12-31
    """
    try:
        # Parse tags if provided
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else None

        # Validate and map arguments to DTO (same validation as MCP adapter)
        create_dto = validate_and_map_create_args(
            title=title,
            project=project,
            task_type=task_type,
            status=status,
            description=description,
            assignee=assignee,
            parent_id=parent_id,
            tags=tag_list,
            priority=priority,
            start_date=start_date,
            due_date=due_date,
            size=size,
        )

        # Execute use case (same as MCP adapter)
        task_use_case = cli_ctx.container.application_container.task_management_use_case
        created_task = await task_use_case.create_task(create_dto)

        # Format output
        output = format_output(
            created_task,
            cli_ctx.config.output_format,
            success_message=f"Created task '{title}'",
        )
        click.echo(output)

    except Exception as e:
        error_output = format_output(
            None, cli_ctx.config.output_format, error_message=str(e)
        )
        click.echo(error_output, err=True)
        sys.exit(1)


@task_commands.command("update")
@click.argument("task_id")
@click.option("--title", help="New task title")
@click.option("--status", "-s", help="New task status")
@click.option("--description", "-d", help="New task description")
@click.option("--assignee", "-a", help="New assignee")
@click.option("--tags", help="New comma-separated list of tags (replaces existing)")
@click.option("--priority", help="New priority level")
@click.option("--start-date", help="New start date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
@click.option("--due-date", help="New due date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
@click.option("--size", help="New size estimate")
@click.pass_obj
@async_command
async def update_task(
    cli_ctx,
    task_id: str,
    title: Optional[str],
    status: Optional[str],
    description: Optional[str],
    assignee: Optional[str],
    tags: Optional[str],
    priority: Optional[str],
    start_date: Optional[str],
    due_date: Optional[str],
    size: Optional[str],
):
    """
    Update an existing task with new attributes.

    TASK_ID: The unique identifier of the task to update

    Examples:
        pytaskai task update task123 --status "In Progress"
        pytaskai task update task123 --title "Updated title" --priority High
        pytaskai task update task123 --tags "urgent,backend,api"
    """
    try:
        # Parse tags if provided
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else None

        # Validate and map arguments to DTO (same validation as MCP adapter)
        update_dto = validate_and_map_update_args(
            task_id=task_id,
            title=title,
            status=status,
            description=description,
            assignee=assignee,
            tags=tag_list,
            priority=priority,
            start_date=start_date,
            due_date=due_date,
            size=size,
        )

        # Execute use case (same as MCP adapter)
        task_use_case = cli_ctx.container.application_container.task_management_use_case
        updated_task = await task_use_case.update_task(update_dto)

        # Format output
        output = format_output(
            updated_task,
            cli_ctx.config.output_format,
            success_message=f"Updated task {task_id}",
        )
        click.echo(output)

    except Exception as e:
        error_output = format_output(
            None, cli_ctx.config.output_format, error_message=str(e)
        )
        click.echo(error_output, err=True)
        sys.exit(1)


@task_commands.command("delete")
@click.argument("task_id")
@click.option("--confirm", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
@async_command
async def delete_task(cli_ctx, task_id: str, confirm: bool):
    """
    Delete a task from the system.

    TASK_ID: The unique identifier of the task to delete

    Examples:
        pytaskai task delete task123
        pytaskai task delete task123 --confirm
    """
    try:
        # Get task details first for confirmation
        task_use_case = cli_ctx.container.application_container.task_management_use_case
        task_dto = await task_use_case.get_task(task_id)

        if not task_dto:
            raise ValueError(f"Task not found: {task_id}")

        # Confirmation prompt (unless --confirm flag is used)
        if not confirm:
            click.echo(f"Task to delete: {task_dto.title}")
            click.echo(f"Status: {task_dto.status}")
            if not click.confirm("Are you sure you want to delete this task?"):
                click.echo("Deletion cancelled.")
                return

        # Execute use case (same as MCP adapter)
        success = await task_use_case.delete_task(task_id)

        if not success:
            raise ValueError(f"Failed to delete task: {task_id}")

        # Format success message
        success_data = {"deleted": True, "task_id": task_id}
        output = format_output(
            success_data,
            cli_ctx.config.output_format,
            success_message=f"Deleted task {task_id}",
        )
        click.echo(output)

    except Exception as e:
        error_output = format_output(
            None, cli_ctx.config.output_format, error_message=str(e)
        )
        click.echo(error_output, err=True)
        sys.exit(1)


@task_commands.command("generate")
@click.argument("parent_task_id")
@click.option(
    "--approach",
    default="functional",
    help="Breakdown approach (functional, temporal, etc.)",
)
@click.option(
    "--max-subtasks", default=5, help="Maximum number of subtasks to generate"
)
@click.pass_obj
@async_command
async def generate_subtasks(
    cli_ctx,
    parent_task_id: str,
    approach: str,
    max_subtasks: int,
):
    """
    Generate subtasks for a parent task using AI (future implementation).

    PARENT_TASK_ID: ID of the task to break down into subtasks

    Examples:
        pytaskai task generate task123
        pytaskai task generate task123 --approach temporal --max-subtasks 10
    """
    try:
        # Check if AI services are available
        if not cli_ctx.container.application_container.has_ai_services():
            ai_error = "AI services not configured. Subtask generation requires AI integration."
            if cli_ctx.config.output_format == "json":
                result = {
                    "generated_subtasks": [],
                    "message": ai_error,
                    "parent_task_id": parent_task_id,
                }
            else:
                result = ai_error

            output = format_output(
                result,
                cli_ctx.config.output_format,
                success_message="AI subtask generation not available",
            )
            click.echo(output)
            return

        # Future implementation: Use AI task generation use case
        # For now, return placeholder response (same as MCP adapter)
        placeholder_result = {
            "generated_subtasks": [],
            "message": "AI subtask generation is planned but not yet implemented.",
            "parent_task_id": parent_task_id,
            "breakdown_approach": approach,
            "max_subtasks": max_subtasks,
        }

        output = format_output(
            placeholder_result,
            cli_ctx.config.output_format,
            success_message="Subtask generation planned for future release",
        )
        click.echo(output)

    except Exception as e:
        error_output = format_output(
            None, cli_ctx.config.output_format, error_message=str(e)
        )
        click.echo(error_output, err=True)
        sys.exit(1)
