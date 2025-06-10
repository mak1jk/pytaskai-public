"""
Test utilities for PyTaskAI
Provides simplified direct access to core functionality for testing
"""

import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.utils import (
    load_tasks,
    save_tasks,
    validate_tasks_file,
    get_tasks_statistics,
    ensure_directories_exist,
)
from shared.models import Task, TaskType, BugSeverity, TaskStatus, TaskPriority


class TaskTestHelper:
    """Helper class for direct task operations in tests"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        ensure_directories_exist(project_root)
    
    async def add_task(
        self,
        prompt: str,
        task_type: str = "task",
        priority: str = "medium",
        severity: Optional[str] = None,
        steps_to_reproduce: Optional[str] = None,
        expected_result: Optional[str] = None,
        actual_result: Optional[str] = None,
        environment: Optional[str] = None,
        target_test_coverage: Optional[float] = None,
        related_tests: str = "",
        dependencies: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Add a task directly using core utilities"""
        try:
            # Load existing tasks
            tasks_data = load_tasks(self.project_root)
            tasks = tasks_data.get("tasks", [])
            next_id = tasks_data.get("next_id", 1)
            
            # Create new task
            task = {
                "id": next_id,
                "title": prompt[:100],  # Truncate title
                "description": prompt,
                "type": task_type,
                "status": "pending",
                "priority": priority,
                "created_at": datetime.now().isoformat() + "Z",
                "updated_at": datetime.now().isoformat() + "Z"
            }
            
            # Add bug-specific fields
            if task_type == "bug" and severity:
                task["severity"] = severity
                if steps_to_reproduce:
                    task["steps_to_reproduce"] = steps_to_reproduce
                if expected_result:
                    task["expected_result"] = expected_result
                if actual_result:
                    task["actual_result"] = actual_result
                if environment:
                    task["environment"] = environment
            
            # Add test coverage fields
            if target_test_coverage is not None:
                task["target_test_coverage"] = target_test_coverage
            
            if related_tests:
                task["related_tests"] = [t.strip() for t in related_tests.split(",") if t.strip()]
            
            # Add dependencies
            if dependencies:
                task["dependencies"] = dependencies
            
            # Add to tasks list
            tasks.append(task)
            
            # Save updated tasks
            updated_data = {
                "tasks": tasks,
                "next_id": next_id + 1
            }
            
            save_tasks(self.project_root, updated_data)
            
            return {
                "success": True,
                "task_id": next_id,
                "task": task
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def report_bug(
        self,
        title: str,
        description: str,
        severity: str = "medium",
        priority: str = "high",
        steps_to_reproduce: Optional[str] = None,
        expected_result: Optional[str] = None,
        actual_result: Optional[str] = None,
        environment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Report a bug using core utilities"""
        if not title.strip():
            return {
                "success": False,
                "error": "Title is required"
            }
        
        result = await self.add_task(
            prompt=title,
            task_type="bug",
            severity=severity,
            priority=priority,
            steps_to_reproduce=steps_to_reproduce,
            expected_result=expected_result,
            actual_result=actual_result,
            environment=environment
        )
        
        if result["success"]:
            # Generate simple recommendations
            recommendations = []
            if severity == "critical":
                recommendations.append("Critical bug requires immediate attention")
            if severity in ["critical", "high"]:
                recommendations.append("High priority bug should be addressed soon")
            
            return {
                "success": True,
                "bug_report": {
                    "bug_id": result["task_id"],
                    "severity": severity,
                    "priority": priority
                },
                "recommendations": recommendations
            }
        
        return result
    
    async def get_bug_statistics(
        self,
        include_resolved: bool = True,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get bug statistics using core utilities"""
        try:
            tasks_data = load_tasks(self.project_root)
            tasks = tasks_data.get("tasks", [])
            
            # Filter bugs
            bugs = [t for t in tasks if t.get("type") == "bug"]
            
            if not include_resolved:
                bugs = [b for b in bugs if b.get("status") != "done"]
            
            # Calculate statistics
            total_bugs = len(bugs)
            
            # Severity distribution
            severity_dist = {}
            for bug in bugs:
                severity = bug.get("severity", "unknown")
                severity_dist[severity] = severity_dist.get(severity, 0) + 1
            
            # Status distribution
            status_dist = {}
            for bug in bugs:
                status = bug.get("status", "unknown")
                status_dist[status] = status_dist.get(status, 0) + 1
            
            # Critical/high count
            critical_high_count = sum(1 for bug in bugs 
                                    if bug.get("severity") in ["critical", "high"] or 
                                    bug.get("priority") in ["highest", "high"])
            
            # Resolution rate
            resolved_bugs = len([b for b in bugs if b.get("status") == "done"])
            resolution_rate = (resolved_bugs / max(total_bugs, 1)) * 100
            
            # Oldest unresolved bugs
            oldest_unresolved = [
                b for b in bugs 
                if b.get("status") != "done"
            ][:10]  # Limit to 10
            
            stats = {
                "total_bugs": total_bugs,
                "severity_distribution": severity_dist,
                "status_distribution": status_dist,
                "critical_high_count": critical_high_count,
                "resolution_rate": resolution_rate,
                "oldest_unresolved": oldest_unresolved
            }
            
            # Add grouped stats if requested
            if group_by == "severity":
                grouped_stats = {}
                for severity, count in severity_dist.items():
                    bugs_for_severity = [b for b in bugs if b.get("severity") == severity]
                    percentage = (count / max(total_bugs, 1)) * 100
                    grouped_stats[severity] = {
                        "count": count,
                        "percentage": percentage,
                        "bugs": bugs_for_severity
                    }
                stats["grouped_stats"] = grouped_stats
            
            return {
                "success": True,
                "statistics": stats
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_tasks(
        self,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        include_subtasks: bool = True,
        include_stats: bool = False
    ) -> Dict[str, Any]:
        """List tasks with filtering"""
        try:
            tasks_data = load_tasks(self.project_root)
            tasks = tasks_data.get("tasks", [])
            
            # Apply filters
            filtered_tasks = tasks
            
            if status_filter:
                filtered_tasks = [t for t in filtered_tasks if t.get("status") == status_filter]
            
            if priority_filter:
                filtered_tasks = [t for t in filtered_tasks if t.get("priority") == priority_filter]
            
            if type_filter:
                filtered_tasks = [t for t in filtered_tasks if t.get("type") == type_filter]
            
            result = {
                "success": True,
                "tasks": filtered_tasks
            }
            
            if include_stats:
                stats = get_tasks_statistics(tasks)
                result["statistics"] = stats
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_task(self, task_id: int) -> Dict[str, Any]:
        """Get a specific task by ID"""
        try:
            tasks_data = load_tasks(self.project_root)
            tasks = tasks_data.get("tasks", [])
            
            task = next((t for t in tasks if t.get("id") == task_id), None)
            
            if task:
                return {
                    "success": True,
                    "task": task
                }
            else:
                return {
                    "success": False,
                    "error": f"Task {task_id} not found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def set_task_status(self, task_id: int, status: str) -> Dict[str, Any]:
        """Update task status"""
        try:
            tasks_data = load_tasks(self.project_root)
            tasks = tasks_data.get("tasks", [])
            
            # Find and update task
            task_found = False
            for task in tasks:
                if task.get("id") == task_id:
                    task["status"] = status
                    task["updated_at"] = datetime.now().isoformat() + "Z"
                    task_found = True
                    break
            
            if not task_found:
                return {
                    "success": False,
                    "error": f"Task {task_id} not found"
                }
            
            # Save updated tasks
            save_tasks(self.project_root, tasks_data)
            
            return {
                "success": True,
                "task_id": task_id,
                "status": status
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_test_coverage(
        self,
        task_id: int,
        achieved_coverage: float,
        test_results: Optional[Dict[str, int]] = None,
        test_report_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update test coverage for a task"""
        try:
            if achieved_coverage < 0 or achieved_coverage > 100:
                return {
                    "success": False,
                    "error": "Coverage must be between 0 and 100"
                }
            
            tasks_data = load_tasks(self.project_root)
            tasks = tasks_data.get("tasks", [])
            
            # Find and update task
            task_found = False
            for task in tasks:
                if task.get("id") == task_id:
                    task["achieved_test_coverage"] = achieved_coverage
                    task["updated_at"] = datetime.now().isoformat() + "Z"
                    
                    if test_report_url:
                        task["test_report_url"] = test_report_url
                    
                    if test_results:
                        task.update(test_results)
                    
                    task_found = True
                    break
            
            if not task_found:
                return {
                    "success": False,
                    "error": f"Task {task_id} not found"
                }
            
            # Save updated tasks
            save_tasks(self.project_root, tasks_data)
            
            # Generate recommendations
            recommendations = []
            target_coverage = task.get("target_test_coverage", 80)
            if achieved_coverage >= target_coverage:
                recommendations.append(f"Great! Coverage target of {target_coverage}% achieved")
            else:
                recommendations.append(f"Coverage below target: {achieved_coverage}% < {target_coverage}%")
            
            return {
                "success": True,
                "coverage_update": {
                    "task_id": task_id,
                    "achieved_coverage": achieved_coverage,
                    "test_report_url": test_report_url,
                    **(test_results or {})
                },
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }