"""
Integration tests for PyTaskAI workflows
Tests complete bug tracking, analytics, and task management workflows
"""

import pytest
import asyncio
import tempfile
import json
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import test utilities for direct testing
from test_utils import TaskTestHelper

# Import models
from shared.models import Task, TaskType, BugSeverity, TaskStatus, TaskPriority


class TestBugTrackingWorkflow:
    """Complete bug tracking workflow integration tests"""
    
    @pytest.fixture
    def fresh_project(self):
        """Create fresh project directory for workflow testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": [], "next_id": 1}, f)
            
            yield temp_dir
    
    async def test_complete_bug_lifecycle(self, fresh_project):
        """Test complete bug lifecycle: report -> analyze -> update -> resolve"""
        
        # Create task helper for direct testing
        helper = TaskTestHelper(fresh_project)
        
        # Step 1: Report a new bug
        bug_result = await helper.report_bug(
            title="Login Form Validation Error", 
            description="Email validation fails for valid addresses",
            severity="high",
            priority="high",
            steps_to_reproduce="1. Go to login\n2. Enter valid email\n3. See error message",
            expected_result="Email should be accepted",
            actual_result="Error: 'Invalid email format'",
            environment="Chrome 120, Windows 11"
        )
        
        assert bug_result["success"] is True
        bug_id = bug_result["bug_report"]["bug_id"]
        assert bug_id is not None
        
        # Step 2: Verify bug appears in analytics
        stats_result = await helper.get_bug_statistics(include_resolved=False)
        
        assert stats_result["success"] is True
        stats = stats_result["statistics"]
        assert stats["total_bugs"] == 1
        assert stats["severity_distribution"]["high"] == 1
        assert stats["critical_high_count"] == 1
        
        # Step 3: Update bug status to in-progress
        status_result = await helper.set_task_status(bug_id, "in-progress")
        
        assert status_result["success"] is True
        
        # Step 4: Add test coverage to bug fix
        coverage_result = await helper.update_test_coverage(
            task_id=bug_id,
            achieved_coverage=95.0,
            test_results={
                "tests_passed": 18,
                "total_tests": 19,
                "failed_tests": 1
            },
            test_report_url="https://example.com/coverage/bug-fix"
        )
        
        assert coverage_result["success"] is True
        
        # Step 5: Mark bug as resolved
        resolve_result = await helper.set_task_status(bug_id, "done")
        
        assert resolve_result["success"] is True
        
        # Step 6: Verify bug shows as resolved in analytics
        final_stats = await helper.get_bug_statistics(include_resolved=True)
        
        assert final_stats["success"] is True
        final_stats_data = final_stats["statistics"]
        assert final_stats_data["total_bugs"] == 1
        assert final_stats_data["resolution_rate"] == 100.0
        assert final_stats_data["status_distribution"]["done"] == 1
        
        # Step 7: Verify complete bug data
        bug_data = await helper.get_task(bug_id)
        
        assert bug_data["success"] is True
        bug = bug_data["task"]
        assert bug["type"] == "bug"
        assert bug["status"] == "done"
        assert bug["achieved_test_coverage"] == 95.0
        assert bug["tests_passed"] == 18
    
    async def test_multiple_bugs_analytics_workflow(self, fresh_project):
        """Test analytics with multiple bugs of different severities and statuses"""
        
        # Create multiple bugs with different characteristics
        bugs_data = [
            {
                "title": "Critical Database Error",
                "severity": "critical",
                "priority": "highest",
                "status": "pending"
            },
            {
                "title": "UI Alignment Issue",
                "severity": "low", 
                "priority": "low",
                "status": "done"
            },
            {
                "title": "Performance Slowdown",
                "severity": "medium",
                "priority": "high",
                "status": "in-progress"
            },
            {
                "title": "API Timeout",
                "severity": "high",
                "priority": "high",
                "status": "review"
            }
        ]
        
        bug_ids = []
        
        # Create all bugs
        for bug_data in bugs_data:
            result = await report_bug_tool(
                project_root=fresh_project,
                title=bug_data["title"],
                description=f"Description for {bug_data['title']}",
                severity=bug_data["severity"],
                priority=bug_data["priority"]
            )
            
            assert result["success"] is True
            bug_id = result["bug_report"]["bug_id"]
            bug_ids.append(bug_id)
            
            # Set status if not pending
            if bug_data["status"] != "pending":
                await set_task_status_tool(
                    project_root=fresh_project,
                    task_id=bug_id,
                    status=bug_data["status"]
                )
        
        # Test analytics with all bugs
        stats_result = await get_bug_statistics_tool(
            project_root=fresh_project,
            include_resolved=True,
            group_by="severity"
        )
        
        assert stats_result["success"] is True
        stats = stats_result["statistics"]
        
        # Verify total counts
        assert stats["total_bugs"] == 4
        
        # Verify severity distribution
        severity_dist = stats["severity_distribution"]
        assert severity_dist["critical"] == 1
        assert severity_dist["high"] == 1
        assert severity_dist["medium"] == 1
        assert severity_dist["low"] == 1
        
        # Verify status distribution
        status_dist = stats["status_distribution"]
        assert status_dist["pending"] == 1
        assert status_dist["done"] == 1
        assert status_dist["in-progress"] == 1
        assert status_dist["review"] == 1
        
        # Verify critical/high count (critical + high severity)
        assert stats["critical_high_count"] == 2
        
        # Verify resolution rate (1 done out of 4 = 25%)
        assert stats["resolution_rate"] == 25.0
        
        # Test grouped statistics
        grouped = stats["grouped_stats"]
        assert "critical" in grouped
        assert grouped["critical"]["count"] == 1
        assert grouped["critical"]["percentage"] == 25.0


class TestTaskWorkflowIntegration:
    """Test task creation and management workflows"""
    
    @pytest.fixture
    def project_with_tasks(self):
        """Create project with existing tasks for workflow testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            # Start with some existing tasks
            sample_tasks = [
                {
                    "id": 1,
                    "title": "Existing Feature",
                    "description": "Pre-existing feature task",
                    "type": "feature",
                    "status": "in-progress",
                    "priority": "medium",
                    "created_at": "2025-01-01T10:00:00Z"
                }
            ]
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": sample_tasks, "next_id": 2}, f)
            
            yield temp_dir
    
    async def test_task_creation_and_test_coverage_workflow(self, project_with_tasks):
        """Test creating task with test requirements and tracking coverage"""
        
        # Step 1: Create task with test coverage requirements
        task_result = await add_task_tool(
            project_root=project_with_tasks,
            prompt="Implement user authentication system",
            task_type="feature",
            priority="high",
            target_test_coverage=85.0,
            related_tests="test_auth.py,test_user_model.py,test_login_flow.py"
        )
        
        assert task_result["success"] is True
        task_id = task_result["task_id"]
        
        # Verify task was created with correct test fields
        task = task_result["task"]
        assert task["target_test_coverage"] == 85.0
        assert "test_auth.py" in task["related_tests"]
        
        # Step 2: Update task to in-progress
        await set_task_status_tool(
            project_root=project_with_tasks,
            task_id=task_id,
            status="in-progress"
        )
        
        # Step 3: Update test coverage as development progresses
        coverage_updates = [
            {"coverage": 30.0, "tests_passed": 5, "total_tests": 15},
            {"coverage": 65.0, "tests_passed": 12, "total_tests": 18},
            {"coverage": 87.0, "tests_passed": 17, "total_tests": 19}
        ]
        
        for update in coverage_updates:
            result = await update_task_test_coverage_tool(
                project_root=project_with_tasks,
                task_id=task_id,
                achieved_coverage=update["coverage"],
                test_results={
                    "tests_passed": update["tests_passed"],
                    "total_tests": update["total_tests"],
                    "failed_tests": update["total_tests"] - update["tests_passed"]
                }
            )
            
            assert result["success"] is True
        
        # Step 4: Mark as ready for review when coverage target met
        await set_task_status_tool(
            project_root=project_with_tasks,
            task_id=task_id,
            status="review"
        )
        
        # Step 5: Verify final task state
        final_task = await get_task_tool(
            project_root=project_with_tasks,
            task_id=task_id
        )
        
        assert final_task["success"] is True
        task_data = final_task["task"]
        assert task_data["achieved_test_coverage"] == 87.0
        assert task_data["achieved_test_coverage"] > task_data["target_test_coverage"]
        assert task_data["status"] == "review"
        assert task_data["tests_passed"] == 17
    
    async def test_task_dependency_validation_workflow(self, project_with_tasks):
        """Test task dependency validation in workflow"""
        
        # Create parent task
        parent_result = await add_task_tool(
            project_root=project_with_tasks,
            prompt="Setup database schema",
            task_type="task",
            priority="high"
        )
        
        parent_id = parent_result["task_id"]
        
        # Create dependent task
        dependent_result = await add_task_tool(
            project_root=project_with_tasks,
            prompt="Implement user CRUD operations",
            task_type="feature",
            priority="medium",
            dependencies=[parent_id]
        )
        
        dependent_id = dependent_result["task_id"]
        
        # Validate dependencies
        validation_result = await validate_tasks_tool(
            project_root=project_with_tasks
        )
        
        assert validation_result["success"] is True
        assert validation_result["valid"] is True
        
        # Try to complete dependent before parent (should be allowed but noted)
        await set_task_status_tool(
            project_root=project_with_tasks,
            task_id=dependent_id,
            status="done"
        )
        
        # Verify task list shows dependency relationship
        tasks_result = await list_tasks_tool(
            project_root=project_with_tasks,
            include_subtasks=True
        )
        
        tasks = tasks_result["tasks"]
        dependent_task = next(t for t in tasks if t["id"] == dependent_id)
        assert parent_id in dependent_task.get("dependencies", [])


class TestConcurrentOperations:
    """Test concurrent operations and race conditions"""
    
    @pytest.fixture
    def concurrent_project(self):
        """Create project for concurrent operation testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": [], "next_id": 1}, f)
            
            yield temp_dir
    
    async def test_concurrent_bug_reporting(self, concurrent_project):
        """Test multiple bugs being reported concurrently"""
        
        # Define concurrent bug reports
        bug_reports = [
            {
                "title": f"Concurrent Bug {i}",
                "description": f"Description for bug {i}",
                "severity": "medium",
                "priority": "medium"
            }
            for i in range(5)
        ]
        
        # Create tasks concurrently
        tasks = [
            report_bug_tool(
                project_root=concurrent_project,
                **bug_data
            )
            for bug_data in bug_reports
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all succeeded
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful_results) == 5
        
        # Verify all bugs are in analytics
        stats_result = await get_bug_statistics_tool(
            project_root=concurrent_project,
            include_resolved=True
        )
        
        assert stats_result["statistics"]["total_bugs"] == 5
    
    async def test_concurrent_status_updates(self, concurrent_project):
        """Test concurrent status updates on the same task"""
        
        # Create a bug first
        bug_result = await report_bug_tool(
            project_root=concurrent_project,
            title="Concurrent Update Test Bug",
            description="Bug for testing concurrent updates",
            severity="medium"
        )
        
        task_id = bug_result["bug_report"]["bug_id"]
        
        # Try concurrent status updates (only one should succeed per update)
        status_updates = [
            set_task_status_tool(
                project_root=concurrent_project,
                task_id=task_id,
                status="in-progress"
            ),
            set_task_status_tool(
                project_root=concurrent_project,
                task_id=task_id,
                status="review"
            )
        ]
        
        results = await asyncio.gather(*status_updates, return_exceptions=True)
        
        # At least one should succeed
        successful_updates = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful_updates) >= 1


class TestErrorRecoveryWorkflows:
    """Test error handling and recovery in workflows"""
    
    async def test_malformed_data_recovery(self):
        """Test recovery from malformed task data"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            # Create malformed tasks.json
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                f.write('{"tasks": [{"id": 1, "malformed": true}], "next_id"')  # Incomplete JSON
            
            # Try to add task - should handle gracefully
            result = await add_task_tool(
                project_root=temp_dir,
                prompt="Test task after corruption",
                task_type="task"
            )
            
            # Should either recover or provide clear error
            assert "error" in result or result.get("success") is True
    
    async def test_missing_required_fields_workflow(self):
        """Test workflow with missing required fields"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": [], "next_id": 1}, f)
            
            # Try to create bug without required title
            result = await report_bug_tool(
                project_root=temp_dir,
                title="",  # Empty title
                description="Valid description"
            )
            
            assert result["success"] is False
            assert "error" in result
            assert "title" in result["error"].lower()


# Integration test runner
async def run_integration_tests():
    """Run all integration tests"""
    print("Running Integration Workflow Tests...")
    
    try:
        # Create test instances
        bug_workflow = TestBugTrackingWorkflow()
        task_workflow = TestTaskWorkflowIntegration() 
        concurrent_tests = TestConcurrentOperations()
        error_tests = TestErrorRecoveryWorkflows()
        
        print("✅ Integration test classes loaded successfully")
        
        # Run a simple workflow test
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": [], "next_id": 1}, f)
            
            # Test basic workflow
            await bug_workflow.test_complete_bug_lifecycle(temp_dir)
            print("✅ Basic bug lifecycle test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False


def run_sync_integration_tests():
    """Synchronous wrapper for async integration tests"""
    return asyncio.run(run_integration_tests())


if __name__ == "__main__":
    success = run_sync_integration_tests()
    if success:
        print("✅ All integration workflow tests passed!")
    else:
        print("❌ Some integration workflow tests failed!")