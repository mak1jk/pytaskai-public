"""
AI-powered task generation use cases for PyTaskAI application layer.
"""

from typing import List, Optional

from pytaskai.application.dto.task_dto import TaskCreateDTO, TaskResponseDTO
from pytaskai.application.interfaces.ai_service import (
    AIResearchService,
    AITaskGenerationService,
)
from pytaskai.application.use_cases.task_management import TaskManagementUseCase


class AITaskGenerationUseCase:
    """
    Use case for AI-powered task generation and enhancement.

    This use case orchestrates AI services with task management
    to provide intelligent task generation functionality.
    """

    def __init__(
        self,
        task_management_use_case: TaskManagementUseCase,
        ai_generation_service: AITaskGenerationService,
        ai_research_service: Optional[AIResearchService] = None,
    ) -> None:
        self._task_management = task_management_use_case
        self._ai_generation = ai_generation_service
        self._ai_research = ai_research_service

    async def generate_tasks_from_prd(
        self,
        prd_content: str,
        project: str,
        auto_create: bool = False,
        max_tasks: int = 20,
    ) -> List[TaskCreateDTO]:
        """
        Generate tasks from a Product Requirements Document.

        Args:
            prd_content: The PRD content to parse
            project: Project name for generated tasks
            auto_create: Whether to automatically create the tasks
            max_tasks: Maximum number of tasks to generate

        Returns:
            List of generated task DTOs

        Raises:
            AIServiceError: If AI service fails
        """
        # Generate tasks using AI service
        generated_tasks = await self._ai_generation.generate_tasks_from_prd(
            prd_content=prd_content,
            project=project,
            max_tasks=max_tasks,
        )

        # Enhance tasks with AI research if available
        if self._ai_research:
            enhanced_tasks = []
            for task_dto in generated_tasks:
                try:
                    # Research additional context for the task
                    context = await self._ai_research.research_task_context(
                        task_title=task_dto.title,
                        task_description=task_dto.description,
                    )

                    # Append research context to description
                    enhanced_description = task_dto.description or ""
                    if context:
                        enhanced_description = f"{enhanced_description}\n\n**Research Context:**\n{context}"

                    # Create enhanced task DTO
                    enhanced_task = TaskCreateDTO(
                        title=task_dto.title,
                        project=task_dto.project,
                        task_type=task_dto.task_type,
                        status=task_dto.status,
                        description=enhanced_description,
                        assignee=task_dto.assignee,
                        parent_id=task_dto.parent_id,
                        tags=task_dto.tags,
                        priority=task_dto.priority,
                        start_at=task_dto.start_at,
                        due_at=task_dto.due_at,
                        size=task_dto.size,
                    )
                    enhanced_tasks.append(enhanced_task)

                except Exception:
                    # If research fails, use original task
                    enhanced_tasks.append(task_dto)

            generated_tasks = enhanced_tasks

        # Auto-create tasks if requested
        if auto_create:
            created_tasks = []
            for task_dto in generated_tasks:
                try:
                    created_task = await self._task_management.create_task(task_dto)
                    created_tasks.append(created_task)
                except Exception:
                    # Continue with other tasks if one fails
                    continue

        return generated_tasks

    async def generate_subtasks(
        self,
        parent_task_id: str,
        max_subtasks: int = 10,
        auto_create: bool = False,
    ) -> List[TaskCreateDTO]:
        """
        Generate subtasks for a complex task.

        Args:
            parent_task_id: ID of the parent task
            max_subtasks: Maximum number of subtasks to generate
            auto_create: Whether to automatically create the subtasks

        Returns:
            List of generated subtask DTOs

        Raises:
            ValueError: If parent task not found
            AIServiceError: If AI service fails
        """
        # Get parent task
        parent_task = await self._task_management.get_task(parent_task_id)
        if not parent_task:
            raise ValueError(f"Parent task {parent_task_id} not found")

        # Generate subtasks using AI service
        subtask_description = f"{parent_task.title}\n\n{parent_task.description or ''}"
        generated_subtasks = await self._ai_generation.generate_subtasks(
            parent_task_description=subtask_description,
            project=parent_task.project,
            max_subtasks=max_subtasks,
        )

        # Set parent_id for all generated subtasks
        subtasks_with_parent = []
        for subtask_dto in generated_subtasks:
            subtask_with_parent = TaskCreateDTO(
                title=subtask_dto.title,
                project=subtask_dto.project,
                task_type=subtask_dto.task_type,
                status=subtask_dto.status,
                description=subtask_dto.description,
                assignee=subtask_dto.assignee or parent_task.assignee,
                parent_id=parent_task_id,  # Set parent reference
                tags=subtask_dto.tags,
                priority=subtask_dto.priority or parent_task.priority,
                start_at=subtask_dto.start_at,
                due_at=subtask_dto.due_at,
                size=subtask_dto.size,
            )
            subtasks_with_parent.append(subtask_with_parent)

        # Auto-create subtasks if requested
        if auto_create:
            for subtask_dto in subtasks_with_parent:
                try:
                    await self._task_management.create_task(subtask_dto)
                except Exception:
                    # Continue with other subtasks if one fails
                    continue

        return subtasks_with_parent

    async def enhance_task_with_ai(
        self, task_id: str, enhance_priority: bool = True, enhance_size: bool = True
    ) -> TaskResponseDTO:
        """
        Enhance an existing task with AI-suggested priority and size.

        Args:
            task_id: ID of the task to enhance
            enhance_priority: Whether to enhance priority
            enhance_size: Whether to enhance size estimation

        Returns:
            Enhanced task DTO

        Raises:
            ValueError: If task not found
            AIServiceError: If AI service fails
        """
        # Get current task
        current_task = await self._task_management.get_task(task_id)
        if not current_task:
            raise ValueError(f"Task {task_id} not found")

        # Containers for enhancements – None means enhancement failed or not requested
        suggested_priority: Optional[str] = None
        estimated_size: Optional[str] = None

        # Local import to avoid circular dependency issues and keep scope limited
        from pytaskai.application.dto.task_dto import TaskUpdateDTO

        # ------------------------------------------------------------------
        # Priority enhancement
        # ------------------------------------------------------------------
        if enhance_priority and not current_task.priority:
            try:
                suggested_priority = await self._ai_generation.suggest_task_priority(
                    task_title=current_task.title,
                    task_description=current_task.description,
                    project_context=current_task.project,
                    use_fallback=False,  # Don't use fallbacks, raise exceptions for graceful degradation
                )
            except Exception:
                # Explicitly keep as None when enhancement fails
                suggested_priority = None

        # ------------------------------------------------------------------
        # Size estimation enhancement
        # ------------------------------------------------------------------
        if enhance_size and not current_task.size:
            try:
                estimated_size = await self._ai_generation.estimate_task_size(
                    task_title=current_task.title,
                    task_description=current_task.description,
                    use_fallback=False,  # Don't use fallbacks, raise exceptions for graceful degradation
                )
            except Exception:
                estimated_size = None

        # ------------------------------------------------------------------
        # Apply updates only if *all* requested enhancements succeeded.
        # If any requested enhancement failed (value stayed ``None``), we return
        # the original task unchanged to provide graceful degradation behaviour.
        # ------------------------------------------------------------------
        enhancements_succeeded = True
        if enhance_priority and not current_task.priority:
            enhancements_succeeded = enhancements_succeeded and (
                suggested_priority is not None
            )
        if enhance_size and not current_task.size:
            enhancements_succeeded = enhancements_succeeded and (
                estimated_size is not None
            )

        # No enhancement or at least one failed – return original task
        if not enhancements_succeeded:
            return current_task

        # Build update DTO with successful enhancements
        update_fields = {}
        if suggested_priority is not None:
            update_fields["priority"] = suggested_priority
        if estimated_size is not None:
            update_fields["size"] = estimated_size

        if update_fields:
            update_data = TaskUpdateDTO(task_id=task_id, **update_fields)
            return await self._task_management.update_task(update_data)

        return current_task

    async def suggest_follow_up_tasks(
        self,
        completed_task_id: str,
        auto_create: bool = False,
    ) -> List[TaskCreateDTO]:
        """
        Suggest follow-up tasks based on a completed task.

        Args:
            completed_task_id: ID of the completed task
            auto_create: Whether to automatically create suggested tasks

        Returns:
            List of suggested follow-up task DTOs

        Raises:
            ValueError: If task not found or not completed
        """
        if not self._ai_research:
            return []

        # Get completed task
        completed_task = await self._task_management.get_task(completed_task_id)
        if not completed_task:
            raise ValueError(f"Task {completed_task_id} not found")

        if completed_task.status != "Done":
            raise ValueError(f"Task {completed_task_id} is not completed")

        # Generate follow-up suggestions using AI research service
        suggested_tasks = await self._ai_research.suggest_related_tasks(
            completed_task_title=completed_task.title,
            project=completed_task.project,
        )

        # Auto-create suggested tasks if requested
        if auto_create:
            for task_dto in suggested_tasks:
                try:
                    await self._task_management.create_task(task_dto)
                except Exception:
                    # Continue with other suggestions if one fails
                    continue

        return suggested_tasks
