"""
Test suite for bug tracking and test coverage features
"""

import os
import sys
import unittest
import tempfile
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.models import Task, TaskType, BugSeverity, TaskPriority
from mcp_server import task_manager
from mcp_server.utils import save_tasks, load_tasks


class TestBugTracking(unittest.TestCase):
    """Test bug tracking functionality"""

    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = self.temp_dir
        
        # Ensure tasks directory exists
        tasks_dir = os.path.join(self.project_root, "tasks")
        os.makedirs(tasks_dir, exist_ok=True)

    def test_task_model_with_bug_fields(self):
        """Test Task model with bug-specific fields"""
        bug_task = Task(
            id=1,
            title="Critical bug in login system",
            description="Users cannot log in with valid credentials",
            type=TaskType.BUG,
            severity=BugSeverity.CRITICAL,
            steps_to_reproduce="1. Go to login page\n2. Enter valid credentials\n3. Click login",
            expected_result="User should be logged in successfully",
            actual_result="Error message: 'Invalid credentials'",
            environment="Chrome 120, Production server",
            priority=TaskPriority.HIGH
        )
        
        assert bug_task.type == TaskType.BUG
        assert bug_task.severity == BugSeverity.CRITICAL
        assert bug_task.steps_to_reproduce is not None
        assert bug_task.expected_result is not None
        assert bug_task.actual_result is not None
        assert bug_task.environment is not None

    def test_task_model_with_test_coverage(self):
        """Test Task model with test coverage fields"""
        task = Task(
            id=2,
            title="Implement user authentication",
            description="Add JWT-based authentication",
            target_test_coverage=85.0,
            achieved_test_coverage=78.5,
            related_tests=["test_auth.py", "test_jwt.py"],
            test_report_url="http://localhost/coverage/auth.html"
        )
        
        assert task.target_test_coverage == 85.0
        assert task.achieved_test_coverage == 78.5
        assert len(task.related_tests) == 2
        assert "test_auth.py" in task.related_tests

    def test_create_bug_via_mcp_tool(self):
        """Test creating a bug through MCP add_task_tool"""
        import asyncio
        
        async def run_test():
            result = await task_manager.add_task_tool(
                project_root=self.project_root,
                prompt="Login page crashes when clicking submit button",
                task_type="bug",
                severity="high",
                priority="high",
                steps_to_reproduce="1. Navigate to /login\n2. Fill form\n3. Click submit",
                expected_result="Form should be submitted successfully",
                actual_result="Page crashes with 500 error",
                environment="Firefox 118, staging environment"
            )
            
            return result
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_test())
        finally:
            loop.close()
        
        assert result.get("success") is True
        assert result.get("task_id") is not None
        
        # Verify the bug was created with correct fields
        task = result.get("task")
        assert task is not None
        assert task["type"] == "bug"
        assert task["severity"] == "high"
        assert task["steps_to_reproduce"] is not None

    def test_list_tasks_with_type_filter(self):
        """Test filtering tasks by type"""
        # First create some tasks of different types
        tasks = [
            {
                "id": 1,
                "title": "Regular task",
                "description": "A normal task",
                "type": "task",
                "status": "pending",
                "priority": "medium",
                "dependencies": [],
                "subtasks": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": 2,
                "title": "Bug report",
                "description": "A bug that needs fixing",
                "type": "bug",
                "severity": "high",
                "status": "pending",
                "priority": "high",
                "dependencies": [],
                "subtasks": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": 3,
                "title": "New feature",
                "description": "A feature request",
                "type": "feature",
                "status": "pending",
                "priority": "medium",
                "dependencies": [],
                "subtasks": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        ]
        
        # Save tasks to file
        tasks_file = os.path.join(self.project_root, "tasks", "tasks.json")
        os.makedirs(os.path.dirname(tasks_file), exist_ok=True)
        
        with open(tasks_file, 'w') as f:
            json.dump({
                "version": "1.0",
                "tasks": tasks,
                "metadata": {
                    "generator": "PyTaskAI Test",
                    "created_at": datetime.now().isoformat()
                }
            }, f, indent=2)
        
        # Test filtering by bug type
        result = task_manager.list_tasks_tool(
            project_root=self.project_root,
            type_filter="bug"
        )
        
        assert result.get("error") is None
        filtered_tasks = result.get("tasks", [])
        assert len(filtered_tasks) == 1
        assert filtered_tasks[0]["type"] == "bug"
        assert filtered_tasks[0]["title"] == "Bug report"

    def test_update_test_coverage(self):
        """Test updating test coverage for a task"""
        # Create a task first
        task = {
            "id": 1,
            "title": "Test task",
            "description": "A task for testing coverage updates",
            "type": "task",
            "status": "pending",
            "priority": "medium",
            "dependencies": [],
            "subtasks": [],
            "target_test_coverage": 80.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # Save task to file
        tasks_file = os.path.join(self.project_root, "tasks", "tasks.json")
        os.makedirs(os.path.dirname(tasks_file), exist_ok=True)
        
        with open(tasks_file, 'w') as f:
            json.dump({
                "version": "1.0",
                "tasks": [task],
                "metadata": {
                    "generator": "PyTaskAI Test",
                    "created_at": datetime.now().isoformat()
                }
            }, f, indent=2)
        
        # Update test coverage
        result = task_manager.update_task_test_coverage_tool(
            project_root=self.project_root,
            task_id=1,
            achieved_coverage=85.5,
            test_report_url="http://localhost/coverage/task1.html",
            tests_passed=True,
            total_tests=25,
            failed_tests=0
        )
        
        assert result.get("success") is True
        assert result.get("coverage_status") == "target_met"  # 85.5 > 80.0
        assert result.get("achieved_coverage") == 85.5

    def test_task_type_enum_values(self):
        """Test TaskType enum values"""
        assert TaskType.TASK == "task"
        assert TaskType.BUG == "bug"
        assert TaskType.FEATURE == "feature"
        assert TaskType.ENHANCEMENT == "enhancement"
        assert TaskType.RESEARCH == "research"
        assert TaskType.DOCUMENTATION == "documentation"

    def test_bug_severity_enum_values(self):
        """Test BugSeverity enum values"""
        assert BugSeverity.CRITICAL == "critical"
        assert BugSeverity.HIGH == "high"
        assert BugSeverity.MEDIUM == "medium"
        assert BugSeverity.LOW == "low"


if __name__ == "__main__":
    # Run tests if file is executed directly
    import unittest
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestBugTracking)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    exit(0 if result.wasSuccessful() else 1)