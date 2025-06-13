"""
Performance and load testing for PyTaskAI hexagonal architecture.

This module establishes performance baselines for:
- Task CRUD operations
- Database query performance
- MCP tool response times
- CLI command execution
- Memory usage profiling
- Concurrent operation handling

These tests provide benchmarks for future optimization efforts
and ensure the architecture scales appropriately.
"""

import asyncio
import gc
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional

import pytest
from click.testing import CliRunner

from pytaskai.adapters.cli.cli_app import cli
from pytaskai.adapters.mcp.dependency_injection import MCPContainer
from pytaskai.application.container import ApplicationContainer
from pytaskai.application.dto.task_dto import TaskCreateDTO
from pytaskai.infrastructure.config.database_config import DatabaseConfig


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""
    operation: str
    duration_ms: float
    memory_usage_mb: float
    operations_per_second: float
    success_rate: float
    
    def __str__(self) -> str:
        return (f"{self.operation}: {self.duration_ms:.2f}ms, "
                f"{self.memory_usage_mb:.2f}MB, "
                f"{self.operations_per_second:.2f} ops/sec, "
                f"{self.success_rate:.1%} success")


class PerformanceBenchmark:
    """Performance benchmarking utilities."""
    
    def __init__(self):
        self.results: List[PerformanceMetrics] = []
    
    def measure_operation(self, operation_name: str, operation_func, iterations: int = 100):
        """Measure performance of an operation with multiple iterations."""
        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]
        
        start_time = time.perf_counter()
        successes = 0
        
        for _ in range(iterations):
            try:
                operation_func()
                successes += 1
            except Exception:
                pass
        
        end_time = time.perf_counter()
        end_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        duration_ms = (end_time - start_time) * 1000
        memory_usage_mb = (end_memory - start_memory) / 1024 / 1024
        ops_per_second = iterations / (duration_ms / 1000) if duration_ms > 0 else 0
        success_rate = successes / iterations
        
        metrics = PerformanceMetrics(
            operation=operation_name,
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            operations_per_second=ops_per_second,
            success_rate=success_rate
        )
        
        self.results.append(metrics)
        return metrics
    
    async def measure_async_operation(self, operation_name: str, operation_func, iterations: int = 100):
        """Measure performance of an async operation."""
        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]
        
        start_time = time.perf_counter()
        successes = 0
        
        for _ in range(iterations):
            try:
                await operation_func()
                successes += 1
            except Exception:
                pass
        
        end_time = time.perf_counter()
        end_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        duration_ms = (end_time - start_time) * 1000
        memory_usage_mb = (end_memory - start_memory) / 1024 / 1024
        ops_per_second = iterations / (duration_ms / 1000) if duration_ms > 0 else 0
        success_rate = successes / iterations
        
        metrics = PerformanceMetrics(
            operation=operation_name,
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            operations_per_second=ops_per_second,
            success_rate=success_rate
        )
        
        self.results.append(metrics)
        return metrics
    
    def print_summary(self):
        """Print performance summary."""
        print("\\n" + "="*80)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("="*80)
        
        for metric in self.results:
            print(metric)
        
        print("="*80)


class TestTaskCRUDPerformance:
    """Test performance of basic task CRUD operations."""
    
    @pytest.fixture
    async def temp_database(self):
        """Create temporary database for testing."""
        with NamedTemporaryFile(delete=False, suffix=".db") as temp_file:
            yield temp_file.name
        Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.fixture
    async def app_container(self, temp_database):
        """Initialize application container."""
        config = DatabaseConfig()
        config.database_path = temp_database
        container = ApplicationContainer(database_config=config)
        await container.initialize()
        yield container
        await container.cleanup()
    
    @pytest.mark.asyncio
    async def test_task_creation_performance(self, app_container):
        """Test task creation performance baseline."""
        benchmark = PerformanceBenchmark()
        task_management = app_container.get_task_management_use_case()
        
        task_counter = 0
        
        async def create_task():
            nonlocal task_counter
            task_counter += 1
            task_dto = TaskCreateDTO(
                title=f"Performance Test Task {task_counter}",
                description="Performance testing task",
                project="PerfTest",
                task_type="Task",
                status="Todo",
                priority="Medium"
            )
            await task_management.create_task(task_dto)
        
        # Measure task creation performance
        metrics = await benchmark.measure_async_operation(
            "Task Creation", create_task, iterations=50
        )
        
        # Baseline expectations
        assert metrics.duration_ms < 5000, f"Task creation too slow: {metrics.duration_ms}ms"
        assert metrics.memory_usage_mb < 50, f"Task creation uses too much memory: {metrics.memory_usage_mb}MB"
        assert metrics.success_rate >= 0.95, f"Task creation success rate too low: {metrics.success_rate}"
        assert metrics.operations_per_second > 10, f"Task creation too slow: {metrics.operations_per_second} ops/sec"
        
        benchmark.print_summary()
    
    @pytest.mark.asyncio
    async def test_task_retrieval_performance(self, app_container):
        """Test task retrieval performance baseline."""
        benchmark = PerformanceBenchmark()
        task_management = app_container.get_task_management_use_case()
        
        # Create test tasks first
        created_tasks = []
        for i in range(20):
            task_dto = TaskCreateDTO(
                title=f"Retrieval Test Task {i}",
                project="RetrievalTest",
                task_type="Task",
                status="Todo"
            )
            task = await task_management.create_task(task_dto)
            created_tasks.append(task)
        
        task_index = 0
        
        async def get_task():
            nonlocal task_index
            task_id = created_tasks[task_index % len(created_tasks)].id
            task_index += 1
            await task_management.get_task(task_id)
        
        # Measure retrieval performance
        metrics = await benchmark.measure_async_operation(
            "Task Retrieval", get_task, iterations=100
        )
        
        # Baseline expectations (should be faster than creation)
        assert metrics.duration_ms < 2000, f"Task retrieval too slow: {metrics.duration_ms}ms"
        assert metrics.memory_usage_mb < 20, f"Task retrieval uses too much memory: {metrics.memory_usage_mb}MB"
        assert metrics.success_rate >= 0.98, f"Task retrieval success rate too low: {metrics.success_rate}"
        assert metrics.operations_per_second > 50, f"Task retrieval too slow: {metrics.operations_per_second} ops/sec"
        
        benchmark.print_summary()
    
    @pytest.mark.asyncio
    async def test_task_listing_performance(self, app_container):
        """Test task listing performance with various filters."""
        benchmark = PerformanceBenchmark()
        task_management = app_container.get_task_management_use_case()
        
        # Create test dataset
        projects = ["Project1", "Project2", "Project3"]
        priorities = ["Low", "Medium", "High"]
        
        for i in range(100):
            task_dto = TaskCreateDTO(
                title=f"List Test Task {i}",
                project=projects[i % len(projects)],
                priority=priorities[i % len(priorities)],
                task_type="Task",
                status="Todo"
            )
            await task_management.create_task(task_dto)
        
        async def list_all_tasks():
            await task_management.list_tasks()
        
        async def list_filtered_tasks():
            from pytaskai.application.dto.task_dto import TaskListFiltersDTO
            filters = TaskListFiltersDTO(project="Project1", priority="High")
            await task_management.list_tasks(filters)
        
        # Measure listing performance
        list_all_metrics = await benchmark.measure_async_operation(
            "List All Tasks", list_all_tasks, iterations=50
        )
        
        list_filtered_metrics = await benchmark.measure_async_operation(
            "List Filtered Tasks", list_filtered_tasks, iterations=50
        )
        
        # Baseline expectations
        assert list_all_metrics.duration_ms < 3000, f"List all tasks too slow: {list_all_metrics.duration_ms}ms"
        assert list_filtered_metrics.duration_ms < 2000, f"Filtered listing too slow: {list_filtered_metrics.duration_ms}ms"
        assert list_all_metrics.success_rate >= 0.95, f"List all success rate too low: {list_all_metrics.success_rate}"
        assert list_filtered_metrics.success_rate >= 0.95, f"Filtered list success rate too low: {list_filtered_metrics.success_rate}"
        
        benchmark.print_summary()


class TestMCPToolPerformance:
    """Test performance of MCP tool operations."""
    
    @pytest.fixture
    async def temp_database(self):
        """Create temporary database for testing."""
        with NamedTemporaryFile(delete=False, suffix=".db") as temp_file:
            yield temp_file.name
        Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.fixture
    async def mcp_container(self, temp_database):
        """Initialize MCP container."""
        config = DatabaseConfig()
        config.database_path = temp_database
        container = MCPContainer(database_config=config)
        await container.initialize()
        yield container
        await container.cleanup()
    
    @pytest.mark.asyncio
    async def test_mcp_tool_response_times(self, mcp_container):
        """Test MCP tool response time baselines."""
        benchmark = PerformanceBenchmark()
        task_tools = mcp_container.get_task_tools()
        
        # Create some test data
        created_tasks = []
        for i in range(10):
            result = await task_tools.add_task_tool(
                title=f"MCP Perf Task {i}",
                project="MCPPerf",
                priority="Medium"
            )
            created_tasks.append(result["task"]["id"])
        
        async def add_task_tool():
            await task_tools.add_task_tool(
                title="MCP Performance Test",
                project="MCPPerf",
                priority="Low"
            )
        
        async def list_tasks_tool():
            await task_tools.list_tasks_tool()
        
        async def get_task_tool():
            task_id = created_tasks[0]
            await task_tools.get_task_tool(task_id=task_id)
        
        # Measure MCP tool performance
        add_metrics = await benchmark.measure_async_operation(
            "MCP Add Task Tool", add_task_tool, iterations=20
        )
        
        list_metrics = await benchmark.measure_async_operation(
            "MCP List Tasks Tool", list_tasks_tool, iterations=30
        )
        
        get_metrics = await benchmark.measure_async_operation(
            "MCP Get Task Tool", get_task_tool, iterations=50
        )
        
        # MCP tools should respond quickly (< 100ms per operation ideally)
        assert add_metrics.duration_ms < 2000, f"MCP add tool too slow: {add_metrics.duration_ms}ms"
        assert list_metrics.duration_ms < 1500, f"MCP list tool too slow: {list_metrics.duration_ms}ms"
        assert get_metrics.duration_ms < 1000, f"MCP get tool too slow: {get_metrics.duration_ms}ms"
        
        # All should have high success rates
        assert add_metrics.success_rate >= 0.95, f"MCP add tool success rate: {add_metrics.success_rate}"
        assert list_metrics.success_rate >= 0.98, f"MCP list tool success rate: {list_metrics.success_rate}"
        assert get_metrics.success_rate >= 0.98, f"MCP get tool success rate: {get_metrics.success_rate}"
        
        benchmark.print_summary()


class TestCLIPerformance:
    """Test CLI command performance."""
    
    @pytest.fixture
    def temp_database(self):
        """Create temporary database for testing."""
        with NamedTemporaryFile(delete=False, suffix=".db") as temp_file:
            yield temp_file.name
        Path(temp_file.name).unlink(missing_ok=True)
    
    def test_cli_command_performance(self, temp_database):
        """Test CLI command execution performance."""
        benchmark = PerformanceBenchmark()
        runner = CliRunner()
        
        # Initialize database
        result = runner.invoke(cli, ["--database-path", temp_database, "init"])
        assert result.exit_code == 0
        
        task_counter = 0
        
        def add_task_command():
            nonlocal task_counter
            task_counter += 1
            runner.invoke(cli, [
                "--database-path", temp_database,
                "task", "add", f"CLI Perf Task {task_counter}",
                "--project", "CLIPerf"
            ])
        
        def list_tasks_command():
            runner.invoke(cli, [
                "--database-path", temp_database,
                "task", "list"
            ])
        
        # Create some test data first
        for i in range(10):
            runner.invoke(cli, [
                "--database-path", temp_database,
                "task", "add", f"CLI Setup Task {i}",
                "--project", "CLISetup"
            ])
        
        # Measure CLI performance
        add_metrics = benchmark.measure_operation(
            "CLI Add Task", add_task_command, iterations=20
        )
        
        list_metrics = benchmark.measure_operation(
            "CLI List Tasks", list_tasks_command, iterations=30
        )
        
        # CLI commands should be reasonably fast
        assert add_metrics.duration_ms < 5000, f"CLI add command too slow: {add_metrics.duration_ms}ms"
        assert list_metrics.duration_ms < 3000, f"CLI list command too slow: {list_metrics.duration_ms}ms"
        
        # Should have high success rates
        assert add_metrics.success_rate >= 0.90, f"CLI add success rate: {add_metrics.success_rate}"
        assert list_metrics.success_rate >= 0.95, f"CLI list success rate: {list_metrics.success_rate}"
        
        benchmark.print_summary()


class TestConcurrencyPerformance:
    """Test concurrent operation performance."""
    
    @pytest.fixture
    async def temp_database(self):
        """Create temporary database for testing."""
        with NamedTemporaryFile(delete=False, suffix=".db") as temp_file:
            yield temp_file.name
        Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.fixture
    async def app_container(self, temp_database):
        """Initialize application container."""
        config = DatabaseConfig()
        config.database_path = temp_database
        container = ApplicationContainer(database_config=config)
        await container.initialize()
        yield container
        await container.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_task_operations(self, app_container):
        """Test performance under concurrent load."""
        benchmark = PerformanceBenchmark()
        task_management = app_container.get_task_management_use_case()
        
        async def concurrent_operations():
            """Perform multiple operations concurrently."""
            tasks = []
            
            # Create multiple tasks concurrently
            for i in range(10):
                task_dto = TaskCreateDTO(
                    title=f"Concurrent Task {i}",
                    project="ConcurrentTest",
                    task_type="Task",
                    status="Todo"
                )
                task_coro = task_management.create_task(task_dto)
                tasks.append(task_coro)
            
            # Wait for all creations
            created_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Perform concurrent reads
            read_tasks = []
            for task in created_tasks:
                if hasattr(task, 'id'):
                    read_coro = task_management.get_task(task.id)
                    read_tasks.append(read_coro)
            
            if read_tasks:
                await asyncio.gather(*read_tasks, return_exceptions=True)
        
        # Measure concurrent performance
        metrics = await benchmark.measure_async_operation(
            "Concurrent Operations", concurrent_operations, iterations=5
        )
        
        # Concurrent operations should scale reasonably
        assert metrics.duration_ms < 10000, f"Concurrent operations too slow: {metrics.duration_ms}ms"
        assert metrics.memory_usage_mb < 100, f"Concurrent operations use too much memory: {metrics.memory_usage_mb}MB"
        assert metrics.success_rate >= 0.80, f"Concurrent success rate too low: {metrics.success_rate}"
        
        benchmark.print_summary()
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, app_container):
        """Test database connection handling under load."""
        benchmark = PerformanceBenchmark()
        task_management = app_container.get_task_management_use_case()
        
        async def database_stress_test():
            """Stress test database connections."""
            # Perform rapid sequential operations
            for i in range(20):
                task_dto = TaskCreateDTO(
                    title=f"DB Stress Task {i}",
                    project="DBStress",
                    task_type="Task",
                    status="Todo"
                )
                task = await task_management.create_task(task_dto)
                await task_management.get_task(task.id)
                await task_management.list_tasks()
        
        # Measure database stress performance
        metrics = await benchmark.measure_async_operation(
            "Database Stress Test", database_stress_test, iterations=3
        )
        
        # Database should handle rapid operations efficiently
        assert metrics.duration_ms < 8000, f"Database stress test too slow: {metrics.duration_ms}ms"
        assert metrics.success_rate >= 0.95, f"Database stress success rate too low: {metrics.success_rate}"
        
        benchmark.print_summary()


class TestMemoryUsage:
    """Test memory usage patterns."""
    
    @pytest.fixture
    async def temp_database(self):
        """Create temporary database for testing."""
        with NamedTemporaryFile(delete=False, suffix=".db") as temp_file:
            yield temp_file.name
        Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_memory_growth_patterns(self, temp_database):
        """Test that memory usage doesn't grow unbounded."""
        config = DatabaseConfig()
        config.database_path = temp_database
        
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        # Perform many operations
        for batch in range(5):
            container = ApplicationContainer(database_config=config)
            await container.initialize()
            
            task_management = container.get_task_management_use_case()
            
            # Create and delete tasks
            for i in range(20):
                task_dto = TaskCreateDTO(
                    title=f"Memory Test Task {batch}-{i}",
                    project="MemoryTest",
                    task_type="Task",
                    status="Todo"
                )
                task = await task_management.create_task(task_dto)
                await task_management.delete_task(task.id)
            
            await container.cleanup()
            
            # Force garbage collection
            gc.collect()
        
        final_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        memory_growth_mb = (final_memory - initial_memory) / 1024 / 1024
        
        # Memory growth should be reasonable (< 20MB for this test)
        assert memory_growth_mb < 20, f"Excessive memory growth: {memory_growth_mb:.2f}MB"
        
        print(f"Memory growth after operations: {memory_growth_mb:.2f}MB")


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-s"])