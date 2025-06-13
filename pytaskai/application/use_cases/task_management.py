"""
Task management use cases for PyTaskAI application layer.
"""

from typing import List, Optional

from pytaskai.application.dto.task_dto import (
    TaskCreateDTO,
    TaskListFiltersDTO,
    TaskResponseDTO,
    TaskUpdateDTO,
)
from pytaskai.application.interfaces.notification_service import (
    NotificationChannel,
    NotificationService,
)
from pytaskai.domain.entities.task import Task
from pytaskai.domain.repositories.task_repository import TaskManagementRepository
from pytaskai.domain.services.task_service import TaskService
from pytaskai.domain.value_objects.task_types import (
    ProjectName,
    TagName,
    TaskId,
    TaskPriority,
    TaskSize,
    TaskStatus,
    TaskType,
)


class TaskManagementUseCase:
    """
    Use case for task management operations (CRUD).

    This use case orchestrates domain services and repositories
    to provide task management functionality for external adapters.
    """

    def __init__(
        self,
        repository: TaskManagementRepository,
        task_service: TaskService,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        self._repository = repository
        self._task_service = task_service
        self._notification_service = notification_service

    async def create_task(self, task_data: TaskCreateDTO) -> TaskResponseDTO:
        """
        Create a new task.

        Args:
            task_data: Task creation data

        Returns:
            Created task as DTO

        Raises:
            ValueError: If task data is invalid
        """
        # Convert DTO to domain objects
        tags = [TagName(tag) for tag in task_data.tags] if task_data.tags else []
        priority = TaskPriority(task_data.priority) if task_data.priority else None
        size = TaskSize(task_data.size) if task_data.size else None
        parent_id = TaskId(task_data.parent_id) if task_data.parent_id else None

        # Create task through repository
        task = await self._repository.tasks.create_task(
            title=task_data.title,
            description=task_data.description,
            priority=str(priority) if priority else None,
            size=str(size) if size else None,
            project=task_data.project,
            task_type=task_data.task_type,
            status=task_data.status,
            assignee=task_data.assignee,
            parent_id=str(parent_id) if parent_id else None,
            tags=[str(tag) for tag in tags],
            start_at=task_data.start_at,
            due_at=task_data.due_at,
        )

        # Send notification if service is available
        if self._notification_service and task_data.assignee:
            try:
                await self._notification_service.send_task_created_notification(
                    task_id=str(task.id),
                    task_title=task.title,
                    assignee=task_data.assignee,
                    channel=NotificationChannel.IN_APP,
                )
            except Exception:
                # Don't fail task creation if notification fails
                pass

        return self._task_to_dto(task)

    async def get_task(self, task_id: str) -> Optional[TaskResponseDTO]:
        """
        Get a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task as DTO or None if not found
        """
        task = await self._repository.tasks.get_task(TaskId(task_id))
        return self._task_to_dto(task) if task else None

    async def list_tasks(
        self, filters: Optional[TaskListFiltersDTO] = None
    ) -> List[TaskResponseDTO]:
        """
        List tasks with optional filtering.

        Args:
            filters: Optional filtering parameters

        Returns:
            List of tasks as DTOs
        """
        # Apply filters from DTO
        kwargs = {}
        if filters:
            if filters.assignee:
                kwargs["assignee"] = filters.assignee
            if filters.project:
                kwargs["project"] = filters.project
            if filters.status:
                kwargs["status"] = filters.status
            if filters.priority:
                kwargs["priority"] = filters.priority
            if filters.task_type:
                kwargs["task_type"] = filters.task_type
            if filters.tag:
                kwargs["tag"] = filters.tag
            if filters.due_at_before:
                kwargs["due_at_before"] = filters.due_at_before
            if filters.due_at_after:
                kwargs["due_at_after"] = filters.due_at_after
            if filters.parent_id:
                kwargs["parent_id"] = filters.parent_id

        tasks = await self._repository.tasks.list_tasks(**kwargs)

        # Filter out completed tasks if requested
        if filters and not filters.include_completed:
            tasks = [task for task in tasks if not task.is_completed()]

        return [self._task_to_dto(task) for task in tasks]

    async def update_task(self, update_data: TaskUpdateDTO) -> TaskResponseDTO:
        """
        Update an existing task.

        Args:
            update_data: Task update data

        Returns:
            Updated task as DTO

        Raises:
            ValueError: If task not found or update data is invalid
        """
        # Get current task
        current_task = await self._repository.tasks.get_task(
            TaskId(update_data.task_id)
        )
        if not current_task:
            raise ValueError(f"Task {update_data.task_id} not found")

        # Prepare update parameters
        kwargs = {"task_id": TaskId(update_data.task_id)}

        if update_data.title is not None:
            kwargs["title"] = update_data.title
        if update_data.status is not None:
            kwargs["status"] = update_data.status
        if update_data.description is not None:
            kwargs["description"] = update_data.description
        if update_data.assignee is not None:
            kwargs["assignee"] = update_data.assignee
        if update_data.priority is not None:
            kwargs["priority"] = update_data.priority
        if update_data.size is not None:
            kwargs["size"] = update_data.size
        if update_data.start_at is not None:
            kwargs["start_at"] = update_data.start_at
        if update_data.due_at is not None:
            kwargs["due_at"] = update_data.due_at
        if update_data.tags is not None:
            kwargs["tags"] = update_data.tags

        # Update task through repository
        updated_task = await self._repository.tasks.update_task(**kwargs)

        # Send assignment notification if assignee changed
        if (
            self._notification_service
            and update_data.assignee
            and update_data.assignee != current_task.assignee
        ):
            try:
                await self._notification_service.send_task_assigned_notification(
                    task_id=str(updated_task.id),
                    task_title=updated_task.title,
                    assignee=update_data.assignee,
                )
            except Exception:
                # Don't fail update if notification fails
                pass

        return self._task_to_dto(updated_task)

    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was deleted

        Raises:
            ValueError: If task not found
        """
        task = await self._repository.tasks.get_task(TaskId(task_id))
        if not task:
            raise ValueError(f"Task {task_id} not found")

        return await self._repository.tasks.delete_task(TaskId(task_id))

    async def get_overdue_tasks(
        self, assignee: Optional[str] = None
    ) -> List[TaskResponseDTO]:
        """
        Get overdue tasks using domain service.

        Args:
            assignee: Optional assignee filter

        Returns:
            List of overdue tasks as DTOs
        """
        overdue_tasks = await self._task_service.get_overdue_tasks(assignee)
        return [self._task_to_dto(task) for task in overdue_tasks]

    async def get_high_priority_tasks(
        self, assignee: Optional[str] = None, project: Optional[str] = None
    ) -> List[TaskResponseDTO]:
        """
        Get high priority tasks using domain service.

        Args:
            assignee: Optional assignee filter
            project: Optional project filter

        Returns:
            List of high priority tasks as DTOs
        """
        high_priority_tasks = await self._task_service.get_high_priority_tasks(
            assignee, project
        )
        return [self._task_to_dto(task) for task in high_priority_tasks]

    async def clone_task(
        self, source_task_id: str, new_title: Optional[str] = None
    ) -> TaskResponseDTO:
        """
        Clone an existing task using domain service.

        Args:
            source_task_id: ID of task to clone
            new_title: Optional new title for cloned task

        Returns:
            Cloned task as DTO

        Raises:
            ValueError: If source task not found
        """
        cloned_task = await self._task_service.clone_task(
            TaskId(source_task_id), new_title
        )
        return self._task_to_dto(cloned_task)

    def _task_to_dto(self, task: Task) -> TaskResponseDTO:
        """Convert domain Task entity to TaskResponseDTO."""
        return TaskResponseDTO(
            id=str(task.id),
            title=task.title,
            external_url=task.external_url,
            project=str(task.project),
            task_type=str(task.task_type),
            status=str(task.status),
            assignee=task.assignee,
            parent_id=str(task.parent_id) if task.parent_id else None,
            tags=[str(tag) for tag in task.tags],
            priority=str(task.priority) if task.priority else None,
            start_at=task.start_at,
            due_at=task.due_at,
            size=str(task.size) if task.size else None,
            description=task.description,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
