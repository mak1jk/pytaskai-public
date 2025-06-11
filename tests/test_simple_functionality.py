"""
Simplified test suite for core functionality without MCP wrapping
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


class TestCoreFunctionality(unittest.TestCase):
    """Test core PyTaskAI functionality"""

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
        
        self.assertEqual(bug_task.type, TaskType.BUG)
        self.assertEqual(bug_task.severity, BugSeverity.CRITICAL)
        self.assertIsNotNone(bug_task.steps_to_reproduce)
        self.assertIsNotNone(bug_task.expected_result)
        self.assertIsNotNone(bug_task.actual_result)
        self.assertIsNotNone(bug_task.environment)

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
        
        self.assertEqual(task.target_test_coverage, 85.0)
        self.assertEqual(task.achieved_test_coverage, 78.5)
        self.assertEqual(len(task.related_tests), 2)
        self.assertIn("test_auth.py", task.related_tests)

    def test_task_type_enum_values(self):
        """Test TaskType enum values"""
        self.assertEqual(TaskType.TASK, "task")
        self.assertEqual(TaskType.BUG, "bug")
        self.assertEqual(TaskType.FEATURE, "feature")
        self.assertEqual(TaskType.ENHANCEMENT, "enhancement")
        self.assertEqual(TaskType.RESEARCH, "research")
        self.assertEqual(TaskType.DOCUMENTATION, "documentation")

    def test_bug_severity_enum_values(self):
        """Test BugSeverity enum values"""
        self.assertEqual(BugSeverity.CRITICAL, "critical")
        self.assertEqual(BugSeverity.HIGH, "high")
        self.assertEqual(BugSeverity.MEDIUM, "medium")
        self.assertEqual(BugSeverity.LOW, "low")

    def test_task_serialization(self):
        """Test that tasks can be serialized to/from JSON"""
        task = Task(
            id=3,
            title="Test task",
            description="A test task for serialization",
            type=TaskType.FEATURE,
            priority=TaskPriority.MEDIUM,
            target_test_coverage=90.0,
            related_tests=["test_feature.py"]
        )
        
        # Serialize to dict
        task_dict = task.model_dump()
        self.assertIn("type", task_dict)
        self.assertEqual(task_dict["type"], "feature")
        self.assertEqual(task_dict["target_test_coverage"], 90.0)
        
        # Deserialize from dict
        reconstructed_task = Task(**task_dict)
        self.assertEqual(reconstructed_task.type, TaskType.FEATURE)
        self.assertEqual(reconstructed_task.target_test_coverage, 90.0)

    def test_bug_task_with_all_fields(self):
        """Test bug task with all possible fields"""
        bug = Task(
            id=4,
            title="Database connection timeout",
            description="Database queries timeout after 30 seconds",
            type=TaskType.BUG,
            severity=BugSeverity.HIGH,
            priority=TaskPriority.HIGHEST,
            steps_to_reproduce="1. Execute long-running query\n2. Wait 30 seconds\n3. Observe timeout",
            expected_result="Query should complete successfully",
            actual_result="Query times out with error 'Connection timeout'",
            environment="PostgreSQL 13, Production",
            attachments=["error_log.txt", "screenshot.png"],
            target_test_coverage=100.0,
            related_tests=["test_database.py", "test_timeout.py"]
        )
        
        # Verify all fields are set correctly
        self.assertEqual(bug.type, TaskType.BUG)
        self.assertEqual(bug.severity, BugSeverity.HIGH)
        self.assertEqual(bug.priority, TaskPriority.HIGHEST)
        self.assertIn("long-running query", bug.steps_to_reproduce)
        self.assertIn("timeout", bug.actual_result.lower())
        self.assertEqual(len(bug.attachments), 2)
        self.assertEqual(len(bug.related_tests), 2)
        self.assertEqual(bug.target_test_coverage, 100.0)

    def test_task_validation(self):
        """Test task validation works correctly"""
        # Valid task should not raise exception
        try:
            task = Task(
                id=5,
                title="Valid task",
                description="This task should be valid",
                target_test_coverage=75.5,
                achieved_test_coverage=80.0
            )
            self.assertIsNotNone(task)
        except Exception as e:
            self.fail(f"Valid task raised exception: {e}")
        
        # Invalid coverage should raise exception
        with self.assertRaises(Exception):
            Task(
                id=6,
                title="Invalid coverage",
                description="This should fail",
                target_test_coverage=150.0  # Invalid: > 100
            )

    def test_task_default_values(self):
        """Test task default values are set correctly"""
        task = Task(
            id=7,
            title="Minimal task",
            description="Task with minimal fields"
        )
        
        # Check defaults
        self.assertEqual(task.type, TaskType.TASK)
        self.assertEqual(task.priority, TaskPriority.MEDIUM)
        self.assertEqual(len(task.attachments), 0)
        self.assertEqual(len(task.related_tests), 0)
        self.assertEqual(len(task.dependencies), 0)
        self.assertIsNone(task.severity)  # Should be None for non-bug tasks


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)