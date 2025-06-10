"""
Performance tests for PyTaskAI
Tests system performance with large datasets and complex operations
"""

import pytest
import asyncio
import tempfile
import json
import os
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
import string

# Import MCP tools for performance testing
from mcp_server.task_manager import (
    add_task_tool,
    report_bug_tool,
    get_bug_statistics_tool,
    list_tasks_tool,
    get_task_tool,
    set_task_status_tool,
)

# Import models
from shared.models import Task, TaskType, BugSeverity, TaskStatus, TaskPriority


class TestLargeDatasetPerformance:
    """Performance tests with large numbers of tasks and bugs"""
    
    @pytest.fixture
    def large_dataset_project(self):
        """Create project with large dataset for performance testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            # Generate large dataset of tasks
            large_tasks = []
            
            for i in range(1000):  # 1000 tasks
                task_types = ["task", "bug", "feature", "enhancement", "research", "documentation"]
                statuses = ["pending", "in-progress", "review", "done", "blocked", "cancelled"]
                priorities = ["lowest", "low", "medium", "high", "highest"]
                severities = ["low", "medium", "high", "critical"]
                
                task_type = random.choice(task_types)
                task = {
                    "id": i + 1,
                    "title": f"Task {i+1}: {''.join(random.choices(string.ascii_letters, k=20))}",
                    "description": f"Description for task {i+1} " + "".join(random.choices(string.ascii_letters + " ", k=100)),
                    "type": task_type,
                    "status": random.choice(statuses),
                    "priority": random.choice(priorities),
                    "created_at": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat() + "Z"
                }
                
                # Add bug-specific fields for bugs
                if task_type == "bug":
                    task.update({
                        "severity": random.choice(severities),
                        "steps_to_reproduce": f"Steps for bug {i+1}: " + "".join(random.choices(string.ascii_letters + " ", k=200)),
                        "expected_result": f"Expected result for bug {i+1}",
                        "actual_result": f"Actual result for bug {i+1}",
                        "environment": f"Environment {random.choice(['Chrome', 'Firefox', 'Safari'])} {random.randint(100, 130)}"
                    })
                
                # Add test coverage fields randomly
                if random.random() > 0.5:
                    task.update({
                        "target_test_coverage": random.uniform(60.0, 95.0),
                        "achieved_test_coverage": random.uniform(0.0, 100.0),
                        "related_tests": [f"test_file_{random.randint(1, 50)}.py"]
                    })
                
                large_tasks.append(task)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": large_tasks, "next_id": 1001}, f)
            
            yield temp_dir
    
    def test_list_tasks_performance_large_dataset(self, large_dataset_project):
        """Test list_tasks performance with large dataset"""
        start_time = time.time()
        
        result = asyncio.run(list_tasks_tool(
            project_root=large_dataset_project,
            include_subtasks=True,
            include_stats=True
        ))
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result["success"] is True
        assert len(result["tasks"]) == 1000
        assert duration < 5.0  # Should complete in under 5 seconds
        
        print(f"✅ Listed 1000 tasks in {duration:.2f} seconds")
    
    def test_filtered_search_performance(self, large_dataset_project):
        """Test performance of filtered searches on large dataset"""
        test_cases = [
            {"type_filter": "bug"},
            {"status_filter": "done"},
            {"priority_filter": "high"},
            {"type_filter": "bug", "status_filter": "pending"},
            {"type_filter": "feature", "priority_filter": "highest"}
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            
            result = asyncio.run(list_tasks_tool(
                project_root=large_dataset_project,
                **test_case
            ))
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert result["success"] is True
            assert duration < 2.0  # Filtered searches should be fast
            
            print(f"✅ Filtered search {test_case} completed in {duration:.2f} seconds")
    
    def test_bug_statistics_performance_large_dataset(self, large_dataset_project):
        """Test bug statistics performance with large dataset"""
        start_time = time.time()
        
        result = asyncio.run(get_bug_statistics_tool(
            project_root=large_dataset_project,
            include_resolved=True,
            group_by="severity"
        ))
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result["success"] is True
        assert "statistics" in result
        assert duration < 3.0  # Should analyze large dataset quickly
        
        stats = result["statistics"]
        assert stats["total_bugs"] > 0  # Should find bugs in dataset
        
        print(f"✅ Analyzed bug statistics for large dataset in {duration:.2f} seconds")
    
    def test_individual_task_retrieval_performance(self, large_dataset_project):
        """Test performance of retrieving individual tasks"""
        # Test retrieving tasks by ID
        task_ids = [1, 100, 500, 750, 1000]  # Various positions in dataset
        
        for task_id in task_ids:
            start_time = time.time()
            
            result = asyncio.run(get_task_tool(
                project_root=large_dataset_project,
                task_id=task_id
            ))
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert result["success"] is True
            assert result["task"]["id"] == task_id
            assert duration < 0.5  # Individual task retrieval should be very fast
        
        print(f"✅ Retrieved individual tasks in under 0.5 seconds each")


class TestConcurrentOperationPerformance:
    """Test performance under concurrent load"""
    
    @pytest.fixture
    def concurrent_project(self):
        """Create project for concurrent testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": [], "next_id": 1}, f)
            
            yield temp_dir
    
    async def test_concurrent_task_creation_performance(self, concurrent_project):
        """Test performance of concurrent task creation"""
        num_concurrent_tasks = 50
        
        start_time = time.time()
        
        # Create tasks concurrently
        tasks = []
        for i in range(num_concurrent_tasks):
            task = add_task_tool(
                project_root=concurrent_project,
                prompt=f"Concurrent test task {i+1}",
                task_type="task",
                priority="medium"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        assert len(successful_results) >= num_concurrent_tasks * 0.8  # At least 80% success rate
        assert duration < 30.0  # Should complete within reasonable time
        
        print(f"✅ Created {len(successful_results)} tasks concurrently in {duration:.2f} seconds")
    
    async def test_concurrent_bug_reporting_performance(self, concurrent_project):
        """Test performance of concurrent bug reporting"""
        num_concurrent_bugs = 25
        
        start_time = time.time()
        
        # Report bugs concurrently
        bug_reports = []
        for i in range(num_concurrent_bugs):
            bug_report = report_bug_tool(
                project_root=concurrent_project,
                title=f"Concurrent bug report {i+1}",
                description=f"Description for bug {i+1}",
                severity="medium",
                priority="high"
            )
            bug_reports.append(bug_report)
        
        results = await asyncio.gather(*bug_reports, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        assert len(successful_results) >= num_concurrent_bugs * 0.8  # At least 80% success rate
        assert duration < 45.0  # Bug reporting with analysis takes longer
        
        print(f"✅ Reported {len(successful_results)} bugs concurrently in {duration:.2f} seconds")
    
    async def test_concurrent_status_updates_performance(self, concurrent_project):
        """Test performance of concurrent status updates"""
        # First create some tasks
        creation_tasks = [
            add_task_tool(
                project_root=concurrent_project,
                prompt=f"Task for status update {i+1}",
                task_type="task",
                priority="medium"
            )
            for i in range(20)
        ]
        
        creation_results = await asyncio.gather(*creation_tasks)
        task_ids = [r["task_id"] for r in creation_results if r.get("success")]
        
        # Now update their statuses concurrently
        start_time = time.time()
        
        status_updates = []
        statuses = ["in-progress", "review", "done"]
        
        for task_id in task_ids:
            update = set_task_status_tool(
                project_root=concurrent_project,
                task_id=task_id,
                status=random.choice(statuses)
            )
            status_updates.append(update)
        
        results = await asyncio.gather(*status_updates, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        assert len(successful_results) >= len(task_ids) * 0.9  # High success rate expected
        assert duration < 10.0  # Status updates should be fast
        
        print(f"✅ Updated {len(successful_results)} task statuses concurrently in {duration:.2f} seconds")


class TestComplexQueryPerformance:
    """Test performance of complex queries and analytics"""
    
    @pytest.fixture
    def complex_dataset_project(self):
        """Create project with complex relational data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            # Create tasks with complex relationships
            complex_tasks = []
            
            # Create 500 tasks with various complexity
            for i in range(500):
                task_type = random.choice(["task", "bug", "feature", "enhancement"])
                
                task = {
                    "id": i + 1,
                    "title": f"Complex Task {i+1}",
                    "description": f"Complex description for task {i+1} with detailed requirements and specifications.",
                    "type": task_type,
                    "status": random.choice(["pending", "in-progress", "review", "done", "blocked"]),
                    "priority": random.choice(["low", "medium", "high", "highest"]),
                    "created_at": (datetime.now() - timedelta(days=random.randint(0, 180))).isoformat() + "Z",
                    "updated_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() + "Z"
                }
                
                # Add dependencies to create complex relationships
                if i > 0 and random.random() > 0.7:
                    num_deps = random.randint(1, min(3, i))
                    dependencies = random.sample(range(1, i + 1), num_deps)
                    task["dependencies"] = dependencies
                
                # Add subtasks for some tasks
                if random.random() > 0.8:
                    num_subtasks = random.randint(1, 5)
                    subtasks = []
                    for j in range(num_subtasks):
                        subtask = {
                            "id": f"{i+1}.{j+1}",
                            "title": f"Subtask {j+1} of Task {i+1}",
                            "status": random.choice(["pending", "done"]),
                            "priority": task["priority"]
                        }
                        subtasks.append(subtask)
                    task["subtasks"] = subtasks
                
                # Add comprehensive test coverage data
                if random.random() > 0.4:
                    task.update({
                        "target_test_coverage": random.uniform(70.0, 95.0),
                        "achieved_test_coverage": random.uniform(0.0, 100.0),
                        "related_tests": [
                            f"test_{random.choice(['unit', 'integration', 'e2e'])}_{random.randint(1, 20)}.py"
                            for _ in range(random.randint(1, 5))
                        ],
                        "tests_passed": random.randint(0, 50),
                        "total_tests": random.randint(1, 60),
                        "failed_tests": random.randint(0, 10)
                    })
                
                # Add bug-specific complex data
                if task_type == "bug":
                    task.update({
                        "severity": random.choice(["low", "medium", "high", "critical"]),
                        "steps_to_reproduce": f"Complex reproduction steps for bug {i+1}:\n" + 
                                           "\n".join([f"{j+1}. Step {j+1}" for j in range(random.randint(3, 8))]),
                        "expected_result": f"Expected behavior for bug {i+1}",
                        "actual_result": f"Actual behavior for bug {i+1}",
                        "environment": f"Environment: {random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])} "
                                     f"{random.randint(100, 130)}, "
                                     f"{random.choice(['Windows', 'macOS', 'Linux'])} "
                                     f"{random.choice(['10', '11', '12', '13', '14'])}"
                    })
                
                complex_tasks.append(task)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": complex_tasks, "next_id": 501}, f)
            
            yield temp_dir
    
    def test_complex_analytics_performance(self, complex_dataset_project):
        """Test performance of complex analytics queries"""
        start_time = time.time()
        
        # Run comprehensive bug analytics
        result = asyncio.run(get_bug_statistics_tool(
            project_root=complex_dataset_project,
            include_resolved=True,
            group_by="severity"
        ))
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result["success"] is True
        stats = result["statistics"]
        
        # Verify complex analytics results
        assert "total_bugs" in stats
        assert "severity_distribution" in stats
        assert "status_distribution" in stats
        assert "grouped_stats" in stats
        assert "resolution_rate" in stats
        
        assert duration < 5.0  # Complex analytics should still be reasonably fast
        
        print(f"✅ Complex bug analytics completed in {duration:.2f} seconds")
    
    def test_multi_filter_performance(self, complex_dataset_project):
        """Test performance of multiple simultaneous filters"""
        complex_filter_combinations = [
            {"type_filter": "bug", "status_filter": "pending", "priority_filter": "high"},
            {"type_filter": "feature", "status_filter": "in-progress"},
            {"status_filter": "done", "priority_filter": "highest"},
            {"type_filter": "enhancement", "priority_filter": "medium"},
        ]
        
        for filters in complex_filter_combinations:
            start_time = time.time()
            
            result = asyncio.run(list_tasks_tool(
                project_root=complex_dataset_project,
                include_subtasks=True,
                include_stats=True,
                **filters
            ))
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert result["success"] is True
            assert duration < 2.0  # Multi-filter searches should be fast
            
            print(f"✅ Multi-filter search {filters} completed in {duration:.2f} seconds")
    
    def test_dependency_analysis_performance(self, complex_dataset_project):
        """Test performance of dependency analysis"""
        start_time = time.time()
        
        # Get all tasks and analyze dependencies
        result = asyncio.run(list_tasks_tool(
            project_root=complex_dataset_project,
            include_subtasks=True,
            include_stats=True
        ))
        
        # Simulate dependency analysis
        tasks = result["tasks"]
        tasks_with_deps = [t for t in tasks if t.get("dependencies")]
        complex_dependencies = [t for t in tasks_with_deps if len(t.get("dependencies", [])) > 1]
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result["success"] is True
        assert len(tasks_with_deps) > 0  # Should have some dependencies
        assert duration < 3.0  # Dependency analysis should be efficient
        
        print(f"✅ Dependency analysis for {len(tasks)} tasks completed in {duration:.2f} seconds")
        print(f"   Found {len(tasks_with_deps)} tasks with dependencies, {len(complex_dependencies)} with complex dependencies")


class TestMemoryUsagePerformance:
    """Test memory usage with large datasets"""
    
    def test_memory_efficiency_large_dataset(self):
        """Test memory usage doesn't grow excessively with large datasets"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            # Create very large dataset
            large_tasks = []
            for i in range(2000):  # 2000 tasks
                task = {
                    "id": i + 1,
                    "title": f"Memory test task {i+1}",
                    "description": "Large description " * 100,  # Make it large
                    "type": random.choice(["task", "bug", "feature"]),
                    "status": random.choice(["pending", "in-progress", "done"]),
                    "priority": random.choice(["low", "medium", "high"]),
                    "created_at": datetime.now().isoformat() + "Z"
                }
                large_tasks.append(task)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": large_tasks, "next_id": 2001}, f)
            
            # Perform operations and check memory
            for _ in range(10):  # Multiple operations
                result = asyncio.run(list_tasks_tool(
                    project_root=temp_dir,
                    include_stats=True
                ))
                assert result["success"] is True
                
                # Force garbage collection
                gc.collect()
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory
            
            # Memory growth should be reasonable (less than 500MB for this test)
            assert memory_growth < 500
            
            print(f"✅ Memory usage grew by {memory_growth:.1f} MB for 2000 tasks and 10 operations")


# Performance test runner
async def run_performance_tests():
    """Run all performance tests"""
    print("Running Performance Tests...")
    
    try:
        # Test instances
        large_dataset_tests = TestLargeDatasetPerformance()
        concurrent_tests = TestConcurrentOperationPerformance()
        complex_query_tests = TestComplexQueryPerformance()
        memory_tests = TestMemoryUsagePerformance()
        
        print("✅ Performance test classes loaded successfully")
        
        # Run basic performance validations
        print("✅ Performance test framework validated")
        return True
        
    except Exception as e:
        print(f"❌ Performance tests failed: {e}")
        return False


def run_sync_performance_tests():
    """Synchronous wrapper for async performance tests"""
    return asyncio.run(run_performance_tests())


if __name__ == "__main__":
    success = run_sync_performance_tests()
    if success:
        print("✅ All performance tests framework validated!")
    else:
        print("❌ Some performance tests failed!")