"""
End-to-End Workflow Tests for PyTaskAI
Tests complete user journeys and real-world usage scenarios
"""

import pytest
import asyncio
import tempfile
import json
import os
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import MCP tools and handle FastMCP wrapping
try:
    from mcp_server.task_manager import (
        add_task_tool,
        report_bug_tool,
        get_bug_statistics_tool,
        update_task_test_coverage_tool,
        list_tasks_tool,
        get_task_tool,
        set_task_status_tool,
        validate_tasks_tool,
        parse_prd_tool,
    )
    
    # Helper function to unwrap FastMCP tools if needed
    def unwrap_mcp_tool(tool):
        """Unwrap FastMCP tool to get the underlying function"""
        if hasattr(tool, 'func'):
            return tool.func
        elif hasattr(tool, '__wrapped__'):
            return tool.__wrapped__
        return tool
    
    # Unwrap tools for direct testing
    add_task_tool = unwrap_mcp_tool(add_task_tool)
    report_bug_tool = unwrap_mcp_tool(report_bug_tool)
    get_bug_statistics_tool = unwrap_mcp_tool(get_bug_statistics_tool)
    update_task_test_coverage_tool = unwrap_mcp_tool(update_task_test_coverage_tool)
    list_tasks_tool = unwrap_mcp_tool(list_tasks_tool)
    get_task_tool = unwrap_mcp_tool(get_task_tool)
    set_task_status_tool = unwrap_mcp_tool(set_task_status_tool)
    validate_tasks_tool = unwrap_mcp_tool(validate_tasks_tool)
    parse_prd_tool = unwrap_mcp_tool(parse_prd_tool)
    
except ImportError as e:
    print(f"Warning: Could not import MCP tools: {e}")
    # Create mock functions for testing
    async def add_task_tool(*args, **kwargs):
        return {"success": False, "error": "MCP tools not available"}
    
    async def report_bug_tool(*args, **kwargs):
        return {"success": False, "error": "MCP tools not available"}
    
    async def get_bug_statistics_tool(*args, **kwargs):
        return {"success": False, "error": "MCP tools not available"}
    
    async def update_task_test_coverage_tool(*args, **kwargs):
        return {"success": False, "error": "MCP tools not available"}
    
    async def list_tasks_tool(*args, **kwargs):
        return {"success": False, "error": "MCP tools not available"}
    
    async def get_task_tool(*args, **kwargs):
        return {"success": False, "error": "MCP tools not available"}
    
    async def set_task_status_tool(*args, **kwargs):
        return {"success": False, "error": "MCP tools not available"}
    
    async def validate_tasks_tool(*args, **kwargs):
        return {"success": False, "error": "MCP tools not available"}
        
    async def parse_prd_tool(*args, **kwargs):
        return {"success": False, "error": "MCP tools not available"}

# Import models
from shared.models import Task, TaskType, BugSeverity, TaskStatus, TaskPriority


class TestBugLifecycleWorkflow:
    """Complete bug lifecycle from discovery to resolution"""
    
    @pytest.fixture
    def development_project(self):
        """Simulate a real development project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            # Start with some existing development tasks
            existing_tasks = [
                {
                    "id": 1,
                    "title": "User Authentication System",
                    "description": "Implement secure user login and registration",
                    "type": "feature",
                    "status": "in-progress",
                    "priority": "high",
                    "target_test_coverage": 85.0,
                    "achieved_test_coverage": 60.0,
                    "created_at": "2025-01-01T10:00:00Z"
                },
                {
                    "id": 2,
                    "title": "Database Migration Scripts",
                    "description": "Create migration scripts for new schema",
                    "type": "task",
                    "status": "done",
                    "priority": "medium",
                    "created_at": "2024-12-28T10:00:00Z"
                }
            ]
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": existing_tasks, "next_id": 3}, f)
            
            yield temp_dir
    
    async def test_complete_bug_discovery_to_resolution(self, development_project):
        """Test complete bug workflow: discovery -> triage -> fix -> test -> resolve"""
        
        # Step 1: Bug Discovery - User reports a critical bug
        print("🔍 Step 1: Bug Discovery")
        bug_report = await report_bug_tool(
            project_root=development_project,
            title="User Cannot Login with Valid Credentials",
            description="Users with valid email/password combinations are unable to log in to the system",
            severity="critical",
            priority="highest",
            steps_to_reproduce="""1. Navigate to login page
2. Enter valid email: user@example.com
3. Enter correct password
4. Click 'Sign In' button
5. Observe error message""",
            expected_result="User should be logged in and redirected to dashboard",
            actual_result="Error message: 'Invalid credentials' appears, user remains on login page",
            environment="Chrome 120.0.6099.129, Windows 11, Production environment"
        )
        
        assert bug_report["success"] is True
        bug_id = bug_report["bug_report"]["bug_id"]
        assert bug_id is not None
        
        # Verify bug created with correct severity
        bug_task = await get_task_tool(development_project, bug_id)
        assert bug_task["task"]["severity"] == "critical"
        assert bug_task["task"]["priority"] == "highest"
        
        # Step 2: Bug Triage - Check analytics and prioritize
        print("📊 Step 2: Bug Triage and Analytics")
        stats_result = await get_bug_statistics_tool(
            project_root=development_project,
            include_resolved=False
        )
        
        assert stats_result["success"] is True
        stats = stats_result["statistics"]
        assert stats["total_bugs"] == 1
        assert stats["critical_high_count"] == 1  # Our critical bug
        
        # Verify recommendations include urgency for critical bug
        recommendations = bug_report.get("recommendations", [])
        assert any("critical" in rec.lower() or "immediate" in rec.lower() for rec in recommendations)
        
        # Step 3: Development Phase - Update bug status and track progress
        print("🔧 Step 3: Development and Fix Implementation")
        
        # Developer starts working on the bug
        status_update = await set_task_status_tool(
            project_root=development_project,
            task_id=bug_id,
            status="in-progress"
        )
        assert status_update["success"] is True
        
        # Developer identifies this relates to authentication system
        # Check if we can link to existing auth task
        auth_task = await get_task_tool(development_project, 1)  # Existing auth system task
        assert auth_task["task"]["title"] == "User Authentication System"
        
        # Step 4: Testing Phase - Add comprehensive test coverage
        print("🧪 Step 4: Testing and Coverage")
        
        # First iteration: Basic fix with initial tests
        coverage_update_1 = await update_task_test_coverage_tool(
            project_root=development_project,
            task_id=bug_id,
            achieved_coverage=45.0,
            test_results={
                "tests_passed": 8,
                "total_tests": 12,
                "failed_tests": 4
            },
            test_report_url="https://ci.example.com/reports/bug-fix-initial"
        )
        assert coverage_update_1["success"] is True
        
        # Second iteration: Improved tests after finding edge cases
        coverage_update_2 = await update_task_test_coverage_tool(
            project_root=development_project,
            task_id=bug_id,
            achieved_coverage=78.0,
            test_results={
                "tests_passed": 18,
                "total_tests": 20,
                "failed_tests": 2
            },
            test_report_url="https://ci.example.com/reports/bug-fix-improved"
        )
        assert coverage_update_2["success"] is True
        
        # Final iteration: Comprehensive testing
        coverage_update_3 = await update_task_test_coverage_tool(
            project_root=development_project,
            task_id=bug_id,
            achieved_coverage=92.0,
            test_results={
                "tests_passed": 23,
                "total_tests": 25,
                "failed_tests": 2
            },
            test_report_url="https://ci.example.com/reports/bug-fix-final"
        )
        assert coverage_update_3["success"] is True
        
        # Step 5: Code Review Phase
        print("👀 Step 5: Code Review")
        review_status = await set_task_status_tool(
            project_root=development_project,
            task_id=bug_id,
            status="review"
        )
        assert review_status["success"] is True
        
        # Step 6: Resolution and Verification
        print("✅ Step 6: Resolution and Verification")
        resolution = await set_task_status_tool(
            project_root=development_project,
            task_id=bug_id,
            status="done"
        )
        assert resolution["success"] is True
        
        # Step 7: Final Analytics - Verify bug resolution in metrics
        print("📈 Step 7: Post-Resolution Analytics")
        final_stats = await get_bug_statistics_tool(
            project_root=development_project,
            include_resolved=True
        )
        
        assert final_stats["success"] is True
        final_stats_data = final_stats["statistics"]
        assert final_stats_data["total_bugs"] == 1
        assert final_stats_data["resolution_rate"] == 100.0
        assert final_stats_data["status_distribution"]["done"] == 1
        
        # Verify final bug state includes all our work
        final_bug = await get_task_tool(development_project, bug_id)
        final_bug_data = final_bug["task"]
        
        assert final_bug_data["status"] == "done"
        assert final_bug_data["achieved_test_coverage"] == 92.0
        assert final_bug_data["tests_passed"] == 23
        assert final_bug_data["severity"] == "critical"
        
        print("🎉 Complete bug lifecycle workflow completed successfully!")


class TestFeatureDevelopmentWorkflow:
    """Complete feature development workflow with testing"""
    
    @pytest.fixture
    def feature_project(self):
        """Project setup for feature development workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": [], "next_id": 1}, f)
            
            yield temp_dir
    
    async def test_feature_development_with_testing_workflow(self, feature_project):
        """Test complete feature development from planning to deployment"""
        
        # Step 1: Feature Planning and Requirements
        print("📋 Step 1: Feature Planning")
        feature_task = await add_task_tool(
            project_root=feature_project,
            prompt="Implement real-time notifications system for user activities",
            task_type="feature",
            priority="high",
            target_test_coverage=85.0,
            related_tests="test_notifications.py,test_websockets.py,test_user_events.py",
            use_research=False  # Skip research for speed
        )
        
        assert feature_task["success"] is True
        feature_id = feature_task["task_id"]
        
        # Verify feature created with proper test requirements
        feature_data = feature_task["task"]
        assert feature_data["target_test_coverage"] == 85.0
        assert "test_notifications.py" in feature_data["related_tests"]
        
        # Step 2: Break down into subtasks (simulate dependency creation)
        print("🔗 Step 2: Task Breakdown and Dependencies")
        
        # Create backend API subtask
        backend_task = await add_task_tool(
            project_root=feature_project,
            prompt="Implement backend API for real-time notifications",
            task_type="task",
            priority="high",
            target_test_coverage=90.0,
            dependencies=[feature_id]
        )
        backend_id = backend_task["task_id"]
        
        # Create frontend component subtask
        frontend_task = await add_task_tool(
            project_root=feature_project,
            prompt="Create frontend notification component",
            task_type="task", 
            priority="medium",
            target_test_coverage=80.0,
            dependencies=[backend_id]  # Depends on backend
        )
        frontend_id = frontend_task["task_id"]
        
        # Validate dependencies
        validation = await validate_tasks_tool(feature_project)
        assert validation["success"] is True
        assert validation["valid"] is True
        
        # Step 3: Development Phase - Backend Implementation
        print("⚙️ Step 3: Backend Development")
        
        # Start backend development
        await set_task_status_tool(feature_project, backend_id, "in-progress")
        
        # Iterative testing for backend
        test_iterations = [
            {"coverage": 30.0, "passed": 5, "total": 15, "phase": "initial"},
            {"coverage": 65.0, "passed": 12, "total": 18, "phase": "core-logic"},
            {"coverage": 85.0, "passed": 16, "total": 19, "phase": "edge-cases"},
            {"coverage": 92.0, "passed": 18, "total": 19, "phase": "complete"}
        ]
        
        for iteration in test_iterations:
            coverage_result = await update_task_test_coverage_tool(
                project_root=feature_project,
                task_id=backend_id,
                achieved_coverage=iteration["coverage"],
                test_results={
                    "tests_passed": iteration["passed"],
                    "total_tests": iteration["total"],
                    "failed_tests": iteration["total"] - iteration["passed"]
                },
                test_report_url=f"https://ci.example.com/backend-{iteration['phase']}"
            )
            assert coverage_result["success"] is True
        
        # Complete backend
        await set_task_status_tool(feature_project, backend_id, "done")
        
        # Step 4: Frontend Development (dependent on backend)
        print("🎨 Step 4: Frontend Development")
        
        await set_task_status_tool(feature_project, frontend_id, "in-progress")
        
        # Frontend testing iterations
        frontend_iterations = [
            {"coverage": 40.0, "passed": 8, "total": 15, "phase": "components"},
            {"coverage": 70.0, "passed": 14, "total": 18, "phase": "integration"},
            {"coverage": 82.0, "passed": 16, "total": 18, "phase": "complete"}
        ]
        
        for iteration in frontend_iterations:
            coverage_result = await update_task_test_coverage_tool(
                project_root=feature_project,
                task_id=frontend_id,
                achieved_coverage=iteration["coverage"],
                test_results={
                    "tests_passed": iteration["passed"],
                    "total_tests": iteration["total"],
                    "failed_tests": iteration["total"] - iteration["passed"]
                },
                test_report_url=f"https://ci.example.com/frontend-{iteration['phase']}"
            )
            assert coverage_result["success"] is True
        
        await set_task_status_tool(feature_project, frontend_id, "done")
        
        # Step 5: Integration Testing
        print("🔗 Step 5: Integration Testing")
        
        await set_task_status_tool(feature_project, feature_id, "in-progress")
        
        # Integration testing for main feature
        integration_result = await update_task_test_coverage_tool(
            project_root=feature_project,
            task_id=feature_id,
            achieved_coverage=87.0,
            test_results={
                "tests_passed": 35,
                "total_tests": 40,
                "failed_tests": 5
            },
            test_report_url="https://ci.example.com/integration-complete"
        )
        assert integration_result["success"] is True
        
        # Step 6: Final Review and Deployment
        print("🚀 Step 6: Review and Deployment")
        
        await set_task_status_tool(feature_project, feature_id, "review")
        await set_task_status_tool(feature_project, feature_id, "done")
        
        # Step 7: Verify Complete Workflow
        print("✅ Step 7: Workflow Verification")
        
        # Check all tasks are completed
        all_tasks = await list_tasks_tool(
            project_root=feature_project,
            include_subtasks=True,
            include_stats=True
        )
        
        tasks = all_tasks["tasks"]
        assert len(tasks) == 3  # Feature + backend + frontend
        
        # Verify all tasks are done
        completed_tasks = [t for t in tasks if t["status"] == "done"]
        assert len(completed_tasks) == 3
        
        # Verify test coverage targets met
        feature_final = await get_task_tool(feature_project, feature_id)
        backend_final = await get_task_tool(feature_project, backend_id)
        frontend_final = await get_task_tool(feature_project, frontend_id)
        
        assert feature_final["task"]["achieved_test_coverage"] >= 85.0
        assert backend_final["task"]["achieved_test_coverage"] >= 90.0
        assert frontend_final["task"]["achieved_test_coverage"] >= 80.0
        
        print("🎉 Complete feature development workflow completed successfully!")


class TestProjectManagementWorkflow:
    """Test project-level management workflows"""
    
    @pytest.fixture
    def project_management_setup(self):
        """Setup for project management testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            # Start with a mix of tasks representing a real project
            initial_tasks = [
                {
                    "id": 1,
                    "title": "Setup CI/CD Pipeline",
                    "type": "task",
                    "status": "done",
                    "priority": "high",
                    "created_at": "2024-12-01T10:00:00Z"
                },
                {
                    "id": 2,
                    "title": "API Rate Limiting Bug",
                    "type": "bug",
                    "status": "in-progress",
                    "priority": "high",
                    "severity": "medium",
                    "created_at": "2024-12-15T10:00:00Z"
                }
            ]
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": initial_tasks, "next_id": 3}, f)
            
            yield temp_dir
    
    async def test_sprint_planning_and_execution_workflow(self, project_management_setup):
        """Test complete sprint planning and execution"""
        
        # Step 1: Sprint Planning - Add new tasks for upcoming sprint
        print("📅 Step 1: Sprint Planning")
        
        sprint_tasks = [
            {
                "prompt": "Implement user profile photo upload",
                "type": "feature",
                "priority": "medium",
                "target_coverage": 80.0
            },
            {
                "prompt": "Fix memory leak in image processing",
                "type": "bug",
                "priority": "high",
                "severity": "high",
                "steps": "1. Upload large image\n2. Process multiple times\n3. Monitor memory usage",
                "expected": "Memory should be released after processing",
                "actual": "Memory usage continuously increases"
            },
            {
                "prompt": "Update API documentation for v2.0",
                "type": "documentation",
                "priority": "low",
                "target_coverage": 70.0
            }
        ]
        
        sprint_task_ids = []
        
        for task_data in sprint_tasks:
            if task_data["type"] == "bug":
                result = await report_bug_tool(
                    project_root=project_management_setup,
                    title=task_data["prompt"],
                    description=task_data["prompt"],
                    severity=task_data["severity"],
                    priority=task_data["priority"],
                    steps_to_reproduce=task_data["steps"],
                    expected_result=task_data["expected"],
                    actual_result=task_data["actual"]
                )
                task_id = result["bug_report"]["bug_id"]
            else:
                result = await add_task_tool(
                    project_root=project_management_setup,
                    prompt=task_data["prompt"],
                    task_type=task_data["type"],
                    priority=task_data["priority"],
                    target_test_coverage=task_data.get("target_coverage")
                )
                task_id = result["task_id"]
            
            assert result["success"] is True
            sprint_task_ids.append(task_id)
        
        # Step 2: Sprint Execution - Work on tasks throughout sprint
        print("🏃 Step 2: Sprint Execution")
        
        # Day 1-2: Start working on high priority items
        await set_task_status_tool(project_management_setup, sprint_task_ids[1], "in-progress")  # Bug fix
        
        # Day 3-5: Continue with feature development
        await set_task_status_tool(project_management_setup, sprint_task_ids[0], "in-progress")  # Feature
        
        # Day 6-8: Bug fix testing and completion
        await update_task_test_coverage_tool(
            project_root=project_management_setup,
            task_id=sprint_task_ids[1],
            achieved_coverage=88.0,
            test_results={"tests_passed": 15, "total_tests": 17, "failed_tests": 2}
        )
        await set_task_status_tool(project_management_setup, sprint_task_ids[1], "done")
        
        # Day 9-10: Feature development and testing
        await update_task_test_coverage_tool(
            project_root=project_management_setup,
            task_id=sprint_task_ids[0],
            achieved_coverage=82.0,
            test_results={"tests_passed": 20, "total_tests": 24, "failed_tests": 4}
        )
        await set_task_status_tool(project_management_setup, sprint_task_ids[0], "review")
        
        # Documentation starts
        await set_task_status_tool(project_management_setup, sprint_task_ids[2], "in-progress")
        
        # Step 3: Sprint Review - Analyze progress and metrics
        print("📊 Step 3: Sprint Review and Metrics")
        
        # Get overall project status
        all_tasks = await list_tasks_tool(
            project_root=project_management_setup,
            include_stats=True
        )
        
        tasks = all_tasks["tasks"]
        stats = all_tasks["statistics"]
        
        # Verify sprint progress
        completed_tasks = [t for t in tasks if t["status"] == "done"]
        in_progress_tasks = [t for t in tasks if t["status"] in ["in-progress", "review"]]
        
        # Should have completed the bug fix and original tasks
        assert len(completed_tasks) >= 2
        assert len(in_progress_tasks) >= 2
        
        # Get bug-specific analytics
        bug_stats = await get_bug_statistics_tool(
            project_root=project_management_setup,
            include_resolved=True
        )
        
        bug_analytics = bug_stats["statistics"]
        
        # Should show improved bug resolution
        assert bug_analytics["resolution_rate"] > 0
        assert bug_analytics["total_bugs"] >= 2  # Original + new bug
        
        # Step 4: Sprint Retrospective - Complete remaining tasks
        print("🔄 Step 4: Sprint Retrospective")
        
        # Complete feature review
        await set_task_status_tool(project_management_setup, sprint_task_ids[0], "done")
        
        # Finish documentation
        await update_task_test_coverage_tool(
            project_root=project_management_setup,
            task_id=sprint_task_ids[2],
            achieved_coverage=75.0,
            test_results={"tests_passed": 6, "total_tests": 8, "failed_tests": 2}
        )
        await set_task_status_tool(project_management_setup, sprint_task_ids[2], "done")
        
        # Final project health check
        final_tasks = await list_tasks_tool(
            project_root=project_management_setup,
            include_stats=True
        )
        
        final_stats = final_tasks["statistics"]
        final_completed = [t for t in final_tasks["tasks"] if t["status"] == "done"]
        
        # Verify sprint completion
        assert len(final_completed) >= 4  # All tasks should be completed
        assert final_stats["total_tasks"] >= 5
        
        print("🎉 Complete sprint workflow completed successfully!")


class TestErrorRecoveryWorkflows:
    """Test error handling and recovery in real-world scenarios"""
    
    async def test_data_corruption_recovery_workflow(self):
        """Test recovery from data corruption scenarios"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            # Step 1: Create normal working state
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": [], "next_id": 1}, f)
            
            # Add some tasks
            task1 = await add_task_tool(temp_dir, "Test task 1", "task", "medium")
            task2 = await add_task_tool(temp_dir, "Test task 2", "task", "high")
            
            assert task1["success"] is True
            assert task2["success"] is True
            
            # Step 2: Simulate data corruption
            with open(tasks_file, 'w') as f:
                f.write('{"tasks": [{"id": 1, "corrupted')  # Incomplete JSON
            
            # Step 3: Try to continue operations - should handle gracefully
            recovery_task = await add_task_tool(temp_dir, "Recovery test task", "task", "high")
            
            # Should either recover or provide clear error
            assert "error" in recovery_task or recovery_task.get("success") is True
            
            print("✅ Data corruption recovery workflow completed")
    
    async def test_concurrent_access_workflow(self):
        """Test handling of concurrent access scenarios"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_dir = os.path.join(temp_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            tasks_file = os.path.join(tasks_dir, "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": [], "next_id": 1}, f)
            
            # Create concurrent operations
            concurrent_operations = [
                add_task_tool(temp_dir, f"Concurrent task {i}", "task", "medium")
                for i in range(10)
            ]
            
            results = await asyncio.gather(*concurrent_operations, return_exceptions=True)
            
            # Most should succeed
            successful = [r for r in results if isinstance(r, dict) and r.get("success")]
            assert len(successful) >= 7  # At least 70% success rate
            
            print("✅ Concurrent access workflow completed")


# End-to-end test runner
async def run_end_to_end_tests():
    """Run all end-to-end workflow tests"""
    print("Running End-to-End Workflow Tests...")
    
    try:
        # Test instances
        bug_lifecycle = TestBugLifecycleWorkflow()
        feature_development = TestFeatureDevelopmentWorkflow()
        project_management = TestProjectManagementWorkflow()
        error_recovery = TestErrorRecoveryWorkflows()
        
        print("✅ End-to-end test classes loaded successfully")
        
        # Run basic validation
        await error_recovery.test_data_corruption_recovery_workflow()
        await error_recovery.test_concurrent_access_workflow()
        
        print("✅ End-to-end test framework validated")
        return True
        
    except Exception as e:
        print(f"❌ End-to-end tests failed: {e}")
        return False


def run_sync_end_to_end_tests():
    """Synchronous wrapper for async end-to-end tests"""
    return asyncio.run(run_end_to_end_tests())


if __name__ == "__main__":
    success = run_sync_end_to_end_tests()
    if success:
        print("✅ All end-to-end workflow tests framework validated!")
    else:
        print("❌ Some end-to-end workflow tests failed!")