"""
Dependency injection container for PyTaskAI application layer.
"""

from typing import Optional

from pytaskai.application.interfaces.ai_service import (
    AIResearchService,
    AITaskGenerationService,
)
from pytaskai.application.interfaces.notification_service import NotificationService
from pytaskai.application.use_cases.ai_task_generation import AITaskGenerationUseCase
from pytaskai.application.use_cases.document_management import DocumentManagementUseCase
from pytaskai.application.use_cases.task_management import TaskManagementUseCase
from pytaskai.domain.repositories.task_repository import TaskManagementRepository
from pytaskai.domain.services.task_service import (
    DocumentService,
    TaskService,
    WorkspaceService,
)


class ApplicationContainer:
    """
    Dependency injection container for application layer components.

    This container manages the creation and wiring of use cases,
    domain services, and external service interfaces following
    the dependency inversion principle.
    """

    def __init__(
        self,
        repository: TaskManagementRepository,
        ai_generation_service: Optional[AITaskGenerationService] = None,
        ai_research_service: Optional[AIResearchService] = None,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        """
        Initialize the application container.

        Args:
            repository: Task management repository implementation
            ai_generation_service: Optional AI task generation service
            ai_research_service: Optional AI research service
            notification_service: Optional notification service
        """
        self._repository = repository
        self._ai_generation_service = ai_generation_service
        self._ai_research_service = ai_research_service
        self._notification_service = notification_service

        # Initialize domain services
        self._task_service = TaskService(repository)
        self._document_service = DocumentService(repository)
        self._workspace_service = WorkspaceService(repository)

        # Initialize use cases with dependency injection
        self._task_management_use_case = TaskManagementUseCase(
            repository=repository,
            task_service=self._task_service,
            notification_service=notification_service,
        )

        self._document_management_use_case = DocumentManagementUseCase(
            repository=repository,
            document_service=self._document_service,
        )

        self._ai_task_generation_use_case: Optional[AITaskGenerationUseCase] = None
        if ai_generation_service:
            self._ai_task_generation_use_case = AITaskGenerationUseCase(
                task_management_use_case=self._task_management_use_case,
                ai_generation_service=ai_generation_service,
                ai_research_service=ai_research_service,
            )

    @property
    def task_management_use_case(self) -> TaskManagementUseCase:
        """Get task management use case."""
        return self._task_management_use_case

    @property
    def document_management_use_case(self) -> DocumentManagementUseCase:
        """Get document management use case."""
        return self._document_management_use_case

    @property
    def ai_task_generation_use_case(self) -> Optional[AITaskGenerationUseCase]:
        """Get AI task generation use case (if available)."""
        return self._ai_task_generation_use_case

    @property
    def task_service(self) -> TaskService:
        """Get task domain service."""
        return self._task_service

    @property
    def document_service(self) -> DocumentService:
        """Get document domain service."""
        return self._document_service

    @property
    def workspace_service(self) -> WorkspaceService:
        """Get workspace domain service."""
        return self._workspace_service

    @property
    def repository(self) -> TaskManagementRepository:
        """Get repository instance."""
        return self._repository

    def has_ai_services(self) -> bool:
        """Check if AI services are available."""
        return self._ai_generation_service is not None

    def has_notification_service(self) -> bool:
        """Check if notification service is available."""
        return self._notification_service is not None

    def update_ai_generation_service(
        self, ai_generation_service: AITaskGenerationService
    ) -> None:
        """
        Update AI generation service and recreate dependent use cases.

        Args:
            ai_generation_service: New AI generation service implementation
        """
        self._ai_generation_service = ai_generation_service
        self._ai_task_generation_use_case = AITaskGenerationUseCase(
            task_management_use_case=self._task_management_use_case,
            ai_generation_service=ai_generation_service,
            ai_research_service=self._ai_research_service,
        )

    def update_notification_service(
        self, notification_service: NotificationService
    ) -> None:
        """
        Update notification service and recreate dependent use cases.

        Args:
            notification_service: New notification service implementation
        """
        self._notification_service = notification_service
        self._task_management_use_case = TaskManagementUseCase(
            repository=self._repository,
            task_service=self._task_service,
            notification_service=notification_service,
        )

        # Recreate AI use case if it exists
        if self._ai_generation_service:
            self._ai_task_generation_use_case = AITaskGenerationUseCase(
                task_management_use_case=self._task_management_use_case,
                ai_generation_service=self._ai_generation_service,
                ai_research_service=self._ai_research_service,
            )
