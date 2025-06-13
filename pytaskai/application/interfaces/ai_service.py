"""
Abstract interfaces for AI services in PyTaskAI application layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from pytaskai.application.dto.task_dto import TaskCreateDTO


class AITaskGenerationService(ABC):
    """
    Abstract interface for AI-powered task generation services.

    This interface defines the contract for AI services that can generate
    tasks from various inputs like PRDs, descriptions, or existing tasks.
    """

    @abstractmethod
    async def generate_tasks_from_prd(
        self, prd_content: str, project: str, max_tasks: int = 20
    ) -> List[TaskCreateDTO]:
        """
        Generate tasks from a Product Requirements Document.

        Args:
            prd_content: The PRD content to parse
            project: Project name for generated tasks
            max_tasks: Maximum number of tasks to generate

        Returns:
            List of TaskCreateDTO objects representing generated tasks

        Raises:
            AIServiceError: If AI service fails or returns invalid data
        """

    @abstractmethod
    async def generate_subtasks(
        self, parent_task_description: str, project: str, max_subtasks: int = 10
    ) -> List[TaskCreateDTO]:
        """
        Generate subtasks for a complex task.

        Args:
            parent_task_description: Description of the parent task
            project: Project name for generated subtasks
            max_subtasks: Maximum number of subtasks to generate

        Returns:
            List of TaskCreateDTO objects representing subtasks

        Raises:
            AIServiceError: If AI service fails or returns invalid data
        """

    @abstractmethod
    async def suggest_task_priority(
        self,
        task_title: str,
        task_description: Optional[str] = None,
        project_context: Optional[str] = None,
        use_fallback: bool = True,
    ) -> str:
        """
        Suggest priority for a task based on its content.

        Args:
            task_title: Title of the task
            task_description: Optional description of the task
            project_context: Optional context about the project

        Returns:
            Suggested priority (Low, Medium, High, Critical)

        Raises:
            AIServiceError: If AI service fails
        """

    @abstractmethod
    async def estimate_task_size(
        self,
        task_title: str,
        task_description: Optional[str] = None,
        use_fallback: bool = True,
    ) -> str:
        """
        Estimate the size/complexity of a task.

        Args:
            task_title: Title of the task
            task_description: Optional description of the task

        Returns:
            Estimated size (Small, Medium, Large, Extra Large)

        Raises:
            AIServiceError: If AI service fails
        """


class AIResearchService(ABC):
    """
    Abstract interface for AI-powered research services.

    This interface defines the contract for AI services that can perform
    research and provide contextual information for tasks.
    """

    @abstractmethod
    async def research_task_context(
        self, task_title: str, task_description: Optional[str] = None
    ) -> str:
        """
        Research additional context for a task.

        Args:
            task_title: Title of the task
            task_description: Optional description of the task

        Returns:
            Research findings and contextual information

        Raises:
            AIServiceError: If research fails
        """

    @abstractmethod
    async def suggest_related_tasks(
        self, completed_task_title: str, project: str
    ) -> List[TaskCreateDTO]:
        """
        Suggest follow-up tasks based on a completed task.

        Args:
            completed_task_title: Title of the completed task
            project: Project name for suggested tasks

        Returns:
            List of suggested follow-up tasks

        Raises:
            AIServiceError: If AI service fails
        """


class AIServiceError(Exception):
    """Exception raised when AI service operations fail."""

    def __init__(self, message: str, service_name: str = "AI Service") -> None:
        self.message = message
        self.service_name = service_name
        super().__init__(f"{service_name} error: {message}")
