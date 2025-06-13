"""
End-to-end integration tests for PyTaskAI hexagonal architecture.

This module contains comprehensive E2E tests that validate the complete
architecture flow from adapters through all layers to the database.

Test Strategy:
- CLI → Application → Domain → Infrastructure → Database
- MCP → Application → Domain → Infrastructure → Database  
- Contract Test: CLI and MCP produce identical results
- Error handling across all layers
- Data consistency validation
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pytest
from click.testing import CliRunner

from pytaskai.adapters.cli.cli_app import cli
from pytaskai.adapters.mcp.dependency_injection import MCPContainer
from pytaskai.application.dto.task_dto import TaskCreateDTO, TaskListFiltersDTO
from pytaskai.infrastructure.config.database_config import DatabaseConfig


class TestEndToEndArchitecture:
    """Test complete architecture flows end-to-end."""

    @pytest.fixture
    async def temp_database(self) -> str:
        """Create temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_file.close()
        return temp_file.name

    @pytest.fixture
    async def mcp_container(self, temp_database: str):
        """Initialize MCP container with test database."""
        config = DatabaseConfig()
        config.database_path = temp_database
        container = MCPContainer(database_config=config)
        await container.initialize()
        yield container
        await container.cleanup()

    @pytest.mark.asyncio
    async def test_cli_to_database_flow(self, temp_database: str):
        """
        Test complete CLI flow: CLI → Application → Domain → Infrastructure → Database.
        
        This test validates that a task created via CLI goes through all
        architectural layers correctly and persists to the database.
        """
        runner = CliRunner()

        # Initialize database
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "init"
        ])
        assert result.exit_code == 0

        # Create task via CLI
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "--output-format", "json",
            "task", "add",
            "E2E Test Task",
            "--description", "End-to-end testing task",
            "--project", "TestProject",
            "--priority", "High",
            "--assignee", "test@example.com"
        ])
        assert result.exit_code == 0
        assert "E2E Test Task" in result.output

        # Verify task exists via CLI list
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "--output-format", "json", 
            "task", "list"
        ])
        assert result.exit_code == 0
        assert "E2E Test Task" in result.output
        assert "TestProject" in result.output
        assert "High" in result.output

        # Update task via CLI
        # First extract task ID from list output (simplified for test)
        import json
        output_data = json.loads(result.output)
        task_id = None
        for task in output_data.get("tasks", []):
            if task["title"] == "E2E Test Task":
                task_id = task["id"]
                break
        
        assert task_id is not None, "Task ID not found in CLI output"

        # Update task status
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "task", "update", task_id,
            "--status", "Done"
        ])
        assert result.exit_code == 0

        # Verify update persisted
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "--output-format", "json",
            "task", "get", task_id
        ])
        assert result.exit_code == 0
        task_data = json.loads(result.output)
        assert task_data["task"]["status"] == "Done"

        # Delete task via CLI
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "task", "delete", task_id
        ])
        assert result.exit_code == 0

        # Verify deletion
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "task", "get", task_id
        ])
        assert result.exit_code != 0  # Should fail - task not found

    @pytest.mark.asyncio
    async def test_mcp_to_database_flow(self, mcp_container):
        """
        Test complete MCP flow: MCP → Application → Domain → Infrastructure → Database.
        
        This test validates that a task created via MCP tools goes through all
        architectural layers correctly and persists to the database.
        """
        # Get MCP tools
        task_tools = mcp_container.get_task_tools()

        # Create task via MCP
        create_result = await task_tools.add_task_tool(
            title="MCP E2E Test Task",
            description="End-to-end testing via MCP",
            project="MCPTestProject", 
            priority="Critical",
            assignee="mcp@example.com"
        )
        
        assert create_result["success"] is True
        task_id = create_result["task"]["id"]
        assert create_result["task"]["title"] == "MCP E2E Test Task"
        assert create_result["task"]["priority"] == "Critical"

        # List tasks via MCP
        list_result = await task_tools.list_tasks_tool()
        assert list_result["success"] is True
        found_task = None
        for task in list_result["tasks"]:
            if task["id"] == task_id:
                found_task = task
                break
        
        assert found_task is not None
        assert found_task["title"] == "MCP E2E Test Task"
        assert found_task["project"] == "MCPTestProject"

        # Update task via MCP
        update_result = await task_tools.set_task_status_tool(
            task_id=task_id,
            status="Done"
        )
        assert update_result["success"] is True
        assert update_result["task"]["status"] == "Done"

        # Get specific task via MCP
        get_result = await task_tools.get_task_tool(task_id=task_id)
        assert get_result["success"] is True
        assert get_result["task"]["status"] == "Done"
        assert get_result["task"]["title"] == "MCP E2E Test Task"

        # Delete task via MCP
        delete_result = await task_tools.delete_task_tool(task_id=task_id)
        assert delete_result["success"] is True

        # Verify deletion via MCP
        get_deleted_result = await task_tools.get_task_tool(task_id=task_id)
        assert get_deleted_result["success"] is False
        assert "not found" in get_deleted_result["error"].lower()

    @pytest.mark.asyncio
    async def test_cli_mcp_contract_consistency(self, temp_database: str, mcp_container):
        """
        Contract test: CLI and MCP adapters produce identical results.
        
        This test validates that both adapters, using the same application layer,
        produce exactly the same business logic results for equivalent operations.
        """
        runner = CliRunner()

        # Initialize CLI database
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "init"
        ])
        assert result.exit_code == 0

        # Test data
        test_task = {
            "title": "Contract Test Task",
            "description": "Testing CLI/MCP consistency",
            "project": "ContractTest",
            "priority": "Medium",
            "assignee": "contract@example.com"
        }

        # Create via CLI
        cli_result = runner.invoke(cli, [
            "--database-path", temp_database,
            "--output-format", "json",
            "task", "add", test_task["title"],
            "--description", test_task["description"],
            "--project", test_task["project"],
            "--priority", test_task["priority"],
            "--assignee", test_task["assignee"]
        ])
        assert cli_result.exit_code == 0
        cli_task_data = json.loads(cli_result.output)["task"]

        # Create identical task via MCP
        task_tools = mcp_container.get_task_tools()
        mcp_result = await task_tools.add_task_tool(**test_task)
        assert mcp_result["success"] is True
        mcp_task_data = mcp_result["task"]

        # Compare core business data (excluding IDs and timestamps)
        business_fields = ["title", "description", "project", "priority", "assignee", "status", "task_type"]
        
        for field in business_fields:
            assert cli_task_data[field] == mcp_task_data[field], \
                f"Field '{field}' mismatch: CLI={cli_task_data[field]}, MCP={mcp_task_data[field]}"

        # Test list operations produce consistent results
        cli_list = runner.invoke(cli, [
            "--database-path", temp_database,
            "--output-format", "json",
            "task", "list", "--project", "ContractTest"
        ])
        assert cli_list.exit_code == 0
        cli_tasks = json.loads(cli_list.output)["tasks"]

        mcp_list = await task_tools.list_tasks_tool(project="ContractTest")
        assert mcp_list["success"] is True
        mcp_tasks = mcp_list["tasks"]

        # Should have same number of tasks
        assert len(cli_tasks) == len(mcp_tasks)

        # Business logic should be identical for matching tasks
        cli_tasks_by_title = {task["title"]: task for task in cli_tasks}
        mcp_tasks_by_title = {task["title"]: task for task in mcp_tasks}

        for title in cli_tasks_by_title:
            if title in mcp_tasks_by_title:
                cli_task = cli_tasks_by_title[title]
                mcp_task = mcp_tasks_by_title[title]
                
                for field in business_fields:
                    assert cli_task[field] == mcp_task[field], \
                        f"List consistency failure for '{title}', field '{field}'"

    @pytest.mark.asyncio
    async def test_error_handling_across_layers(self, temp_database: str, mcp_container):
        """
        Test error handling propagation across all architecture layers.
        
        Validates that errors are properly handled and propagated from
        domain through application to adapter layers.
        """
        runner = CliRunner()
        
        # Initialize database
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "init"
        ])
        assert result.exit_code == 0

        # Test CLI error handling
        # 1. Invalid task ID (should propagate from domain → application → CLI)
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "task", "get", "invalid-task-id"
        ])
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "invalid" in result.output.lower()

        # 2. Invalid priority value (should be caught at domain layer)
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "task", "add", "Test Task",
            "--priority", "InvalidPriority"
        ])
        assert result.exit_code != 0

        # Test MCP error handling
        task_tools = mcp_container.get_task_tools()

        # 1. Invalid task ID
        get_result = await task_tools.get_task_tool(task_id="invalid-task-id")
        assert get_result["success"] is False
        assert "error" in get_result
        assert "not found" in get_result["error"].lower()

        # 2. Invalid data (empty title)
        create_result = await task_tools.add_task_tool(
            title="",  # Empty title should be invalid
            project="TestProject"
        )
        assert create_result["success"] is False
        assert "error" in create_result

    @pytest.mark.asyncio
    async def test_data_consistency_validation(self, temp_database: str):
        """
        Test data consistency across the architecture.
        
        Validates that domain invariants are maintained through
        all operations and layers.
        """
        runner = CliRunner()

        # Initialize database
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "init"
        ])
        assert result.exit_code == 0

        # Create task with complete data
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "--output-format", "json",
            "task", "add", "Consistency Test",
            "--description", "Testing data consistency",
            "--project", "DataTest",
            "--priority", "High",
            "--task-type", "Task",
            "--assignee", "test@example.com"
        ])
        assert result.exit_code == 0
        
        task_data = json.loads(result.output)["task"]
        task_id = task_data["id"]

        # Validate domain invariants
        assert task_data["title"] == "Consistency Test"
        assert task_data["project"] == "DataTest"
        assert task_data["priority"] == "High"
        assert task_data["status"] in ["Todo", "To-do"]  # Default status
        assert task_data["task_type"] == "Task"
        assert task_data["assignee"] == "test@example.com"
        assert task_data["created_at"] is not None
        assert task_data["updated_at"] is not None

        # Update and verify consistency
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "task", "update", task_id,
            "--status", "Done",
            "--priority", "Low"
        ])
        assert result.exit_code == 0

        # Get updated task and verify
        result = runner.invoke(cli, [
            "--database-path", temp_database,
            "--output-format", "json",
            "task", "get", task_id
        ])
        assert result.exit_code == 0
        
        updated_task = json.loads(result.output)["task"]
        
        # Verify updates applied correctly
        assert updated_task["status"] == "Done"
        assert updated_task["priority"] == "Low"
        
        # Verify unchanged fields remain consistent
        assert updated_task["title"] == task_data["title"]
        assert updated_task["project"] == task_data["project"]
        assert updated_task["task_type"] == task_data["task_type"]
        assert updated_task["assignee"] == task_data["assignee"]
        assert updated_task["created_at"] == task_data["created_at"]
        
        # Verify updated_at changed
        assert updated_task["updated_at"] != task_data["updated_at"]


class TestLayerIntegration:
    """Test integration between specific architecture layers."""

    @pytest.mark.asyncio
    async def test_application_to_domain_integration(self, temp_database: str):
        """Test Application Layer → Domain Layer integration."""
        # This test focuses on the application-domain boundary
        from pytaskai.application.container import ApplicationContainer
        from pytaskai.infrastructure.config.database_config import DatabaseConfig

        # Setup container
        db_config = DatabaseConfig()
        db_config.database_path = temp_database
        
        container = ApplicationContainer(database_config=db_config)
        await container.initialize()

        try:
            # Get use case (application layer)
            task_management = container.get_task_management_use_case()

            # Create task through application layer
            task_dto = TaskCreateDTO(
                title="Layer Integration Test",
                description="Testing app-domain integration",
                project="LayerTest",
                task_type="Task",
                status="Todo",
                priority="Medium"
            )

            # This call goes: Application → Domain → Infrastructure
            created_task = await task_management.create_task(task_dto)
            
            # Validate domain logic was applied
            assert created_task.id is not None
            assert created_task.title == "Layer Integration Test"
            assert created_task.created_at is not None
            assert created_task.updated_at is not None

            # Test domain business logic through application layer
            task_id = created_task.id
            
            # List with filters (tests domain filtering logic)
            filters = TaskListFiltersDTO(
                project="LayerTest",
                priority="Medium"
            )
            filtered_tasks = await task_management.list_tasks(filters)
            
            assert len(filtered_tasks) >= 1
            found_task = next((t for t in filtered_tasks if t.id == task_id), None)
            assert found_task is not None
            assert found_task.project == "LayerTest"
            assert found_task.priority == "Medium"

        finally:
            await container.cleanup()

    @pytest.mark.asyncio 
    async def test_domain_to_infrastructure_integration(self, temp_database: str):
        """Test Domain Layer → Infrastructure Layer integration."""
        # This test focuses on the domain-infrastructure boundary
        from pytaskai.infrastructure.config.database_config import DatabaseConfig
        from pytaskai.infrastructure.persistence.sqlite_task_repository import SQLiteTaskRepository
        from pytaskai.domain.value_objects.task_types import TaskId
        
        # Setup repository (infrastructure layer)
        db_config = DatabaseConfig()
        db_config.database_path = temp_database
        
        repository = SQLiteTaskRepository(db_config)
        await repository.initialize()

        try:
            # Create task through repository (domain interface → infrastructure implementation)
            task = await repository.create_task(
                title="Domain-Infrastructure Test",
                description="Testing domain-infra integration",
                project="InfraTest",
                task_type="Task",
                status="Todo",
                priority="High"
            )

            # Validate infrastructure properly implemented domain contracts
            assert isinstance(task.id, TaskId)
            assert task.title == "Domain-Infrastructure Test"
            assert str(task.priority) == "High"

            # Test repository operations
            task_id = task.id
            retrieved_task = await repository.get_task(task_id)
            
            assert retrieved_task is not None
            assert retrieved_task.id == task_id
            assert retrieved_task.title == task.title

            # Test domain business rules through infrastructure
            updated_task = await repository.update_task(
                task_id=task_id,
                status="Done"
            )
            
            assert updated_task.status.value == "Done"
            assert updated_task.id == task_id

        finally:
            await repository.cleanup()


class TestArchitectureBoundaries:
    """Test that architecture boundaries are properly maintained."""

    def test_domain_independence(self):
        """
        Test that domain layer has no dependencies on infrastructure or adapters.
        
        This is a critical test for hexagonal architecture - the domain
        should be completely independent of external concerns.
        """
        import inspect
        import pkgutil
        import pytaskai.domain

        # Get all modules in domain package
        domain_modules = []
        for importer, modname, ispkg in pkgutil.walk_packages(
            pytaskai.domain.__path__, 
            pytaskai.domain.__name__ + "."
        ):
            try:
                module = importer.find_module(modname).load_module(modname)
                domain_modules.append(module)
            except ImportError:
                continue

        # Check imports in each domain module
        forbidden_packages = [
            "pytaskai.infrastructure",
            "pytaskai.adapters", 
            "sqlalchemy",
            "fastmcp",
            "click",
            "openai"
        ]

        violations = []
        
        for module in domain_modules:
            try:
                source = inspect.getsource(module)
                for forbidden in forbidden_packages:
                    if f"from {forbidden}" in source or f"import {forbidden}" in source:
                        violations.append(f"Module {module.__name__} imports {forbidden}")
            except (OSError, TypeError):
                # Some modules might not have source available
                continue

        assert len(violations) == 0, f"Domain layer dependency violations: {violations}"

    def test_application_dependencies(self):
        """
        Test that application layer only depends on domain and interfaces.
        
        Application layer should not depend on infrastructure implementations
        or adapter specifics.
        """
        import inspect
        import pkgutil
        import pytaskai.application

        # Get all modules in application package  
        app_modules = []
        for importer, modname, ispkg in pkgutil.walk_packages(
            pytaskai.application.__path__,
            pytaskai.application.__name__ + "."
        ):
            try:
                module = importer.find_module(modname).load_module(modname)
                app_modules.append(module)
            except ImportError:
                continue

        # Check that application only imports from allowed packages
        allowed_packages = [
            "pytaskai.domain",
            "pytaskai.application",
            "typing",
            "abc",
            "datetime",
            "enum"
        ]

        forbidden_packages = [
            "pytaskai.infrastructure.persistence",
            "pytaskai.adapters",
            "sqlalchemy",
            "fastmcp", 
            "click"
        ]

        violations = []

        for module in app_modules:
            try:
                source = inspect.getsource(module)
                for forbidden in forbidden_packages:
                    if f"from {forbidden}" in source or f"import {forbidden}" in source:
                        violations.append(f"Module {module.__name__} imports {forbidden}")
            except (OSError, TypeError):
                continue

        assert len(violations) == 0, f"Application layer dependency violations: {violations}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])