"""
Domain services for PyTaskAI task management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pytaskai.domain.entities.task import Document, Task
from pytaskai.domain.repositories.task_repository import TaskManagementRepository
from pytaskai.domain.value_objects.task_types import TaskId


class TaskService:
    """
    Domain service for complex PyTaskAI task operations.
    """

    def __init__(self, repository: TaskManagementRepository) -> None:
        self._repository = repository

    async def get_overdue_tasks(self, assignee: Optional[str] = None) -> List[Task]:
        """Get all overdue tasks for an assignee."""
        tasks = await self._repository.tasks.list_tasks(
            assignee=assignee, due_at_before=datetime.now()
        )
        return [task for task in tasks if task.is_overdue()]

    async def get_high_priority_tasks(
        self, assignee: Optional[str] = None, project: Optional[str] = None
    ) -> List[Task]:
        """Get all high priority tasks."""
        tasks = await self._repository.tasks.list_tasks(
            assignee=assignee, project=project
        )
        return [task for task in tasks if task.is_high_priority()]

    async def get_my_active_tasks(self, assignee: str) -> List[Task]:
        """Get active tasks for a specific assignee."""
        tasks = await self._repository.tasks.list_tasks(assignee=assignee)
        return [task for task in tasks if not task.is_completed()]

    async def get_tasks_by_project(self, project: str) -> Dict[str, List[Task]]:
        """Group tasks by status within a project."""
        tasks = await self._repository.tasks.list_tasks(project=project)
        grouped: Dict[str, List[Task]] = {}

        for task in tasks:
            status_key = str(task.status)
            if status_key not in grouped:
                grouped[status_key] = []
            grouped[status_key].append(task)

        return grouped

    async def clone_task(
        self, source_task_id: TaskId, new_title: Optional[str] = None
    ) -> Task:
        """Clone an existing task with optional new title."""
        source_task = await self._repository.tasks.get_task(source_task_id)
        if not source_task:
            raise ValueError(f"Task {source_task_id} not found")

        title = new_title or f"Copy of {source_task.title}"

        return await self._repository.tasks.create_task(
            title=title,
            description=source_task.description,
            priority=(str(source_task.priority) if source_task.priority else None),
            size=str(source_task.size) if source_task.size else None,
            project=str(source_task.project),
            tags=[str(tag) for tag in source_task.tags],
        )

    async def bulk_update_status(
        self, task_ids: List[TaskId], new_status: str
    ) -> List[Task]:
        """Update status for multiple tasks."""
        updated_tasks = []
        for task_id in task_ids:
            try:
                updated_task = await self._repository.tasks.update_task(
                    task_id=task_id, status=new_status
                )
                updated_tasks.append(updated_task)
            except Exception:
                # Log error but continue with other tasks
                continue

        return updated_tasks

    async def get_task_hierarchy(self, root_task_id: TaskId) -> List[Task]:
        """Get a task and all its subtasks."""
        root_task = await self._repository.tasks.get_task(root_task_id)
        if not root_task:
            return []

        # Get all tasks and filter for children
        all_tasks = await self._repository.tasks.list_tasks()

        def find_children(parent_id: TaskId) -> List[Task]:
            children = [
                task
                for task in all_tasks
                if task.parent_id and task.parent_id.value == parent_id.value
            ]
            result = []
            for child in children:
                result.append(child)
                result.extend(find_children(child.id))
            return result

        hierarchy = [root_task]
        hierarchy.extend(find_children(root_task_id))
        return hierarchy


class DocumentService:
    """
    Domain service for complex PyTaskAI document operations.
    """

    def __init__(self, repository: TaskManagementRepository) -> None:
        self._repository = repository

    async def get_docs_by_folder(self, folder: str) -> List[Document]:
        """Get all documents in a specific folder."""
        return await self._repository.docs.list_docs(folder=folder)

    async def search_docs_content(self, search_term: str) -> List[Document]:
        """Search documents by content."""
        return await self._repository.docs.list_docs(search=search_term)

    async def get_empty_docs(self) -> List[Document]:
        """Get all empty documents."""
        docs = await self._repository.docs.list_docs()
        return [doc for doc in docs if doc.is_empty()]

    async def duplicate_doc(
        self,
        source_doc_id: str,
        new_title: Optional[str] = None,
        target_folder: Optional[str] = None,
    ) -> Document:
        """Duplicate an existing document."""
        source_doc = await self._repository.docs.get_doc(source_doc_id)
        if not source_doc:
            raise ValueError(f"Document {source_doc_id} not found")

        title = new_title or f"Copy of {source_doc.title}"
        folder = target_folder or source_doc.folder

        return await self._repository.docs.create_doc(
            title=title, text=source_doc.text, folder=folder
        )


class WorkspaceService:
    """
    Domain service for workspace-level PyTaskAI operations.
    """

    def __init__(self, repository: TaskManagementRepository) -> None:
        self._repository = repository

    async def get_workspace_summary(self) -> Dict[str, Any]:
        """Get a summary of the workspace."""
        # Access configuration via nested tasks repository to align with
        # TaskManagementRepository interface and allow easier mocking in tests.
        config = await self._repository.tasks.get_config()
        tasks = await self._repository.tasks.list_tasks()
        docs = await self._repository.docs.list_docs()

        # Task statistics
        completed_tasks = [t for t in tasks if t.is_completed()]
        overdue_tasks = [t for t in tasks if t.is_overdue()]
        high_priority_tasks = [t for t in tasks if t.is_high_priority()]

        # Group by project
        project_stats = {}
        for task in tasks:
            project_name = str(task.project)
            if project_name not in project_stats:
                project_stats[project_name] = {
                    "total": 0,
                    "completed": 0,
                    "overdue": 0,
                    "high_priority": 0,
                }

            project_stats[project_name]["total"] += 1
            if task.is_completed():
                project_stats[project_name]["completed"] += 1
            if task.is_overdue():
                project_stats[project_name]["overdue"] += 1
            if task.is_high_priority():
                project_stats[project_name]["high_priority"] += 1

        return {
            "workspace_config": {
                "assignees_count": len(config.assignees),
                "projects_count": len(config.projects),
                "statuses_count": len(config.statuses),
                "priorities_count": len(config.priorities),
                "tags_count": len(config.tags),
            },
            "task_summary": {
                "total_tasks": len(tasks),
                "completed_tasks": len(completed_tasks),
                "overdue_tasks": len(overdue_tasks),
                "high_priority_tasks": len(high_priority_tasks),
                "completion_rate": (len(completed_tasks) / len(tasks) if tasks else 0),
            },
            "doc_summary": {
                "total_docs": len(docs),
                "draft_docs": len([d for d in docs if d.is_draft]),
                "empty_docs": len([d for d in docs if d.is_empty()]),
            },
            "project_stats": project_stats,
        }
