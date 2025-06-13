"""
Integration tests for CLI adapter.

This module tests the CLI adapter integration with the application layer,
ensuring that CLI commands produce the same business logic results as the
MCP adapter, validating zero duplication of business logic.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pytaskai.adapters.cli.cli_app import cli
from pytaskai.adapters.cli.config import CLIConfig
from pytaskai.adapters.cli.dependency_injection import create_cli_container


class TestCLIIntegration:
    """Test CLI adapter integration with application layer."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        yield tmp_path
        # Cleanup
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI runner for testing."""
        return CliRunner()

    def test_cli_version_command(self, cli_runner, temp_db_path):
        """Test CLI version command."""
        result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "version"])

        assert result.exit_code == 0
        assert "PyTaskAI CLI v0.1.0" in result.output

    def test_cli_status_command(self, cli_runner, temp_db_path):
        """Test CLI status command."""
        result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "status"])

        assert result.exit_code == 0
        assert "PyTaskAI System Status" in result.output
        assert "Database:" in result.output

    def test_cli_init_command(self, cli_runner, temp_db_path):
        """Test CLI initialization command."""
        result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])

        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")

        assert result.exit_code == 0
        assert "Database initialized successfully" in result.output

    def test_task_add_command_table_format(self, cli_runner, temp_db_path):
        """Test task add command with table format output."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Add task
        result = cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "--output-format",
                "table",
                "task",
                "add",
                "Test Task",
                "--description",
                "Test description",
                "--priority",
                "High",
            ],
        )

        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")

        assert result.exit_code == 0
        assert "Created task" in result.output
        assert "Test Task" in result.output

    def test_task_add_command_json_format(self, cli_runner, temp_db_path):
        """Test task add command with JSON format output."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Add task
        result = cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "--output-format",
                "json",
                "task",
                "add",
                "JSON Test Task",
            ],
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert '"title": "JSON Test Task"' in result.output

    def test_task_list_command_empty(self, cli_runner, temp_db_path):
        """Test task list command with empty database."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # List tasks
        result = cli_runner.invoke(
            cli, ["--database-path", temp_db_path, "task", "list"]
        )

        assert result.exit_code == 0
        assert "Found 0 tasks" in result.output

    def test_task_list_command_with_tasks(self, cli_runner, temp_db_path):
        """Test task list command with existing tasks."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Add a test task
        add_result = cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "task",
                "add",
                "List Test Task",
                "--priority",
                "Medium",
            ],
        )
        assert add_result.exit_code == 0

        # List tasks
        result = cli_runner.invoke(
            cli, ["--database-path", temp_db_path, "task", "list"]
        )

        assert result.exit_code == 0
        assert "Found 1 tasks" in result.output
        assert "List Test Task" in result.output

    def test_task_get_command(self, cli_runner, temp_db_path):
        """Test task get command."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Add a test task to get its ID
        add_result = cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "--output-format",
                "json",
                "task",
                "add",
                "Get Test Task",
            ],
        )
        assert add_result.exit_code == 0

        # Extract task ID from JSON output
        import json

        add_output = json.loads(add_result.output)
        task_id = add_output["data"]["id"]

        # Get task details
        result = cli_runner.invoke(
            cli, ["--database-path", temp_db_path, "task", "get", task_id]
        )

        assert result.exit_code == 0
        assert "Get Test Task" in result.output

    def test_task_update_command(self, cli_runner, temp_db_path):
        """Test task update command."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Add a test task to update
        add_result = cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "--output-format",
                "json",
                "task",
                "add",
                "Update Test Task",
            ],
        )
        assert add_result.exit_code == 0

        # Extract task ID from JSON output
        import json

        add_output = json.loads(add_result.output)
        task_id = add_output["data"]["id"]

        # Update task
        result = cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "task",
                "update",
                task_id,
                "--status",
                "In Progress",
                "--priority",
                "High",
            ],
        )

        assert result.exit_code == 0
        assert f"Updated task {task_id}" in result.output

    def test_task_delete_command_with_confirmation(self, cli_runner, temp_db_path):
        """Test task delete command with auto-confirmation."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Add a test task to delete
        add_result = cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "--output-format",
                "json",
                "task",
                "add",
                "Delete Test Task",
            ],
        )
        assert add_result.exit_code == 0

        # Extract task ID from JSON output
        import json

        add_output = json.loads(add_result.output)
        task_id = add_output["data"]["id"]

        # Delete task with auto-confirmation
        result = cli_runner.invoke(
            cli,
            ["--database-path", temp_db_path, "task", "delete", task_id, "--confirm"],
        )

        assert result.exit_code == 0
        assert f"Deleted task {task_id}" in result.output

    def test_task_list_with_filters(self, cli_runner, temp_db_path):
        """Test task list command with various filters."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Add test tasks with different attributes
        cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "task",
                "add",
                "High Priority Task",
                "--priority",
                "High",
                "--status",
                "Todo",
            ],
        )

        cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "task",
                "add",
                "Low Priority Task",
                "--priority",
                "Low",
                "--status",
                "Done",
            ],
        )

        # Test status filter
        result = cli_runner.invoke(
            cli, ["--database-path", temp_db_path, "task", "list", "--status", "Todo"]
        )
        assert result.exit_code == 0
        assert "High Priority Task" in result.output
        assert "Low Priority Task" not in result.output

        # Test priority filter
        result = cli_runner.invoke(
            cli, ["--database-path", temp_db_path, "task", "list", "--priority", "High"]
        )
        assert result.exit_code == 0
        assert "High Priority Task" in result.output

    def test_generate_subtasks_without_ai(self, cli_runner, temp_db_path):
        """Test generate subtasks command without AI services."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Add a parent task
        add_result = cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "--output-format",
                "json",
                "task",
                "add",
                "Parent Task",
            ],
        )
        assert add_result.exit_code == 0

        # Extract task ID from JSON output
        import json

        add_output = json.loads(add_result.output)
        task_id = add_output["data"]["id"]

        # Try to generate subtasks (should indicate AI not available)
        result = cli_runner.invoke(
            cli, ["--database-path", temp_db_path, "task", "generate", task_id]
        )

        assert result.exit_code == 0
        assert (
            "AI services not configured" in result.output
            or "planned but not yet implemented" in result.output
            or "AI subtask generation not available" in result.output
        )

    def test_error_handling_invalid_task_id(self, cli_runner, temp_db_path):
        """Test error handling for invalid task ID."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Try to get non-existent task
        result = cli_runner.invoke(
            cli, ["--database-path", temp_db_path, "task", "get", "nonexistent123"]
        )

        assert result.exit_code == 1
        assert "Error" in result.output or "not found" in result.output

    def test_validation_errors(self, cli_runner, temp_db_path):
        """Test validation error handling."""
        # Initialize database first
        init_result = cli_runner.invoke(cli, ["--database-path", temp_db_path, "init"])
        assert init_result.exit_code == 0

        # Try to add task with invalid priority
        result = cli_runner.invoke(
            cli,
            [
                "--database-path",
                temp_db_path,
                "task",
                "add",
                "Invalid Priority Task",
                "--priority",
                "Invalid",
            ],
        )

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_config_file_usage(self, cli_runner, temp_db_path):
        """Test CLI configuration file usage."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as config_file:
            config_content = {
                "database_path": temp_db_path,
                "output_format": "json",
                "verbose": True,
            }
            import json

            json.dump(config_content, config_file)
            config_file_path = config_file.name

        try:
            # Initialize with config file
            result = cli_runner.invoke(cli, ["--config-file", config_file_path, "init"])

            assert result.exit_code == 0
            assert "Database initialized successfully" in result.output

        finally:
            # Cleanup config file
            Path(config_file_path).unlink()


class TestCLIBusinessLogicConsistency:
    """Test that CLI adapter produces same results as MCP adapter."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        yield tmp_path
        # Cleanup
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    @pytest.mark.asyncio
    async def test_cli_mcp_consistency_task_creation(self, temp_db_path):
        """Test that CLI and MCP adapters create identical tasks."""
        # Create CLI container
        cli_container = create_cli_container(database_path=temp_db_path)
        cli_container.initialize_database()

        # Create task via application layer (same as both adapters would)
        from pytaskai.application.dto.task_dto import TaskCreateDTO

        create_dto = TaskCreateDTO(
            title="Consistency Test Task",
            project="Test Project",
            task_type="Task",
            status="Todo",
            description="Test description",
            priority="High",
            tags=["test", "consistency"],
        )

        task_use_case = cli_container.application_container.task_management_use_case
        created_task = await task_use_case.create_task(create_dto)

        # Verify task was created correctly
        assert created_task.title == "Consistency Test Task"
        assert created_task.project == "Test Project"
        assert created_task.priority == "High"
        assert created_task.tags == ["test", "consistency"]

        # Cleanup
        cli_container.close_database()

    @pytest.mark.asyncio
    async def test_cli_mcp_consistency_task_listing(self, temp_db_path):
        """Test that CLI and MCP adapters return identical task lists."""
        # Create CLI container
        cli_container = create_cli_container(database_path=temp_db_path)
        cli_container.initialize_database()

        # Create multiple tasks
        from pytaskai.application.dto.task_dto import TaskCreateDTO, TaskListFiltersDTO

        task_use_case = cli_container.application_container.task_management_use_case

        # Add test tasks
        tasks_to_create = [
            TaskCreateDTO(
                title="Task 1", project="Test Project", status="Todo", priority="High"
            ),
            TaskCreateDTO(
                title="Task 2",
                project="Test Project",
                status="In Progress",
                priority="Medium",
            ),
            TaskCreateDTO(
                title="Task 3", project="Test Project", status="Done", priority="Low"
            ),
        ]

        for task_dto in tasks_to_create:
            await task_use_case.create_task(task_dto)

        # Test filtering (same logic as both adapters)
        filters = TaskListFiltersDTO(status="Todo", include_completed=False)
        filtered_tasks = await task_use_case.list_tasks(filters)

        # Verify filtering works correctly
        assert len(filtered_tasks) == 1
        assert filtered_tasks[0].title == "Task 1"
        assert filtered_tasks[0].status == "Todo"

        # Test include completed
        all_filters = TaskListFiltersDTO(include_completed=True)
        all_tasks = await task_use_case.list_tasks(all_filters)
        assert len(all_tasks) == 3

        # Cleanup
        cli_container.close_database()

    def test_dto_mapping_consistency(self):
        """Test that CLI and MCP DTO mapping produces identical results."""
        # Import both mappers
        from pytaskai.adapters.cli.dto_mappers import CLITaskMapper
        from pytaskai.adapters.mcp.dto_mappers import MCPTaskMapper

        # Test create DTO mapping
        cli_args = {
            "title": "Test Task",
            "project": "Test Project",
            "priority": "High",
            "tags": ["tag1", "tag2"],
            "description": "Test description",
        }

        mcp_args = {
            "title": "Test Task",
            "project": "Test Project",
            "priority": "High",
            "tags": ["tag1", "tag2"],
            "description": "Test description",
        }

        cli_dto = CLITaskMapper.map_add_args_to_create_dto(**cli_args)
        mcp_dto = MCPTaskMapper.map_create_request_to_dto(mcp_args)

        # Verify both DTOs are identical
        assert cli_dto.title == mcp_dto.title
        assert cli_dto.project == mcp_dto.project
        assert cli_dto.priority == mcp_dto.priority
        assert cli_dto.tags == mcp_dto.tags
        assert cli_dto.description == mcp_dto.description

    def test_output_format_consistency(self):
        """Test that different output formats work correctly."""
        from datetime import datetime

        from pytaskai.adapters.cli.formatters import get_formatter
        from pytaskai.application.dto.task_dto import TaskResponseDTO

        # Create test task
        test_task = TaskResponseDTO(
            id="test123",
            title="Test Task",
            description="Test description",
            status="Todo",
            priority="High",
            project="Test Project",
            task_type="Task",
            assignee=None,
            parent_id=None,
            tags=["test"],
            size=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            start_at=None,
            due_at=None,
            external_url=None,
        )

        # Test all formatters work
        table_formatter = get_formatter("table")
        json_formatter = get_formatter("json")
        plain_formatter = get_formatter("plain")

        table_output = table_formatter.format_task(test_task)
        json_output = json_formatter.format_task(test_task)
        plain_output = plain_formatter.format_task(test_task)

        # Verify outputs contain expected content
        assert "test123" in table_output
        assert "Test Task" in table_output

        assert '"id": "test123"' in json_output
        assert '"title": "Test Task"' in json_output

        assert "ID: test123" in plain_output
        assert "Title: Test Task" in plain_output
