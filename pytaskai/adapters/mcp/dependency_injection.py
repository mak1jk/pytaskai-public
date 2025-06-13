"""
MCP Adapter dependency injection setup.

This module provides dependency injection configuration for the MCP adapter layer,
following the Dependency Inversion Principle by allowing easy swapping of
implementations without modifying the adapter code.
"""

import os
from typing import Optional

from pytaskai.application.container import ApplicationContainer
from pytaskai.application.interfaces.ai_service import (
    AIResearchService,
    AITaskGenerationService,
)
from pytaskai.application.interfaces.notification_service import NotificationService
from pytaskai.infrastructure.config.database_config import DatabaseConfig
from pytaskai.infrastructure.persistence.database import Database
from pytaskai.infrastructure.persistence.sqlite_task_repository import (
    SQLiteTaskRepository,
)


class MCPContainer:
    """
    MCP Adapter dependency injection container.

    This container manages the creation and configuration of all dependencies
    needed by the MCP adapter layer, following the Adapter pattern to isolate
    the MCP protocol concerns from the business logic.
    """

    def __init__(
        self,
        database_path: Optional[str] = None,
        ai_generation_service: Optional[AITaskGenerationService] = None,
        ai_research_service: Optional[AIResearchService] = None,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        """
        Initialize MCP container with optional service overrides.

        Args:
            database_path: Optional database path override
            ai_generation_service: Optional AI generation service override
            ai_research_service: Optional AI research service override
            notification_service: Optional notification service override
        """
        self._database_path = database_path or self._get_default_database_path()
        self._ai_generation_service = ai_generation_service
        self._ai_research_service = ai_research_service
        self._notification_service = notification_service

        # Initialize infrastructure layer
        self._db_config = DatabaseConfig(url=f"sqlite:///{self._database_path}")
        self._database = Database(self._db_config)
        self._database.initialize()
        self._repository = SQLiteTaskRepository(self._database)

        # Initialize application container
        self._app_container = ApplicationContainer(
            repository=self._repository,
            ai_generation_service=ai_generation_service,
            ai_research_service=ai_research_service,
            notification_service=notification_service,
        )

    @staticmethod
    def _get_default_database_path() -> str:
        """Get default database path from environment or use fallback."""
        project_root = os.getcwd()
        db_dir = os.path.join(project_root, ".pytaskai")
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, "tasks.db")

    @property
    def application_container(self) -> ApplicationContainer:
        """Get application container instance."""
        return self._app_container

    @property
    def database(self) -> Database:
        """Get database instance."""
        return self._database

    def initialize_database(self) -> None:
        """Initialize database schema if needed."""
        self._database.create_tables()

    def close_database(self) -> None:
        """Close database connections."""
        self._database.close()

    def is_ready(self) -> bool:
        """Check if container is ready for use."""
        try:
            # Test database connection
            self._database.get_session()
            return True
        except Exception:
            return False

    def get_service_status(self) -> dict[str, bool]:
        """Get status of all services."""
        return {
            "database": self.is_ready(),
            "ai_generation": self._app_container.has_ai_services(),
            "notification": self._app_container.has_notification_service(),
        }

    def update_ai_generation_service(
        self, ai_generation_service: AITaskGenerationService
    ) -> None:
        """
        Update AI generation service at runtime.

        Args:
            ai_generation_service: New AI generation service implementation
        """
        self._ai_generation_service = ai_generation_service
        self._app_container.update_ai_generation_service(ai_generation_service)

    def update_notification_service(
        self, notification_service: NotificationService
    ) -> None:
        """
        Update notification service at runtime.

        Args:
            notification_service: New notification service implementation
        """
        self._notification_service = notification_service
        self._app_container.update_notification_service(notification_service)


def create_mcp_container(
    database_path: Optional[str] = None,
    ai_generation_service: Optional[AITaskGenerationService] = None,
    ai_research_service: Optional[AIResearchService] = None,
    notification_service: Optional[NotificationService] = None,
) -> MCPContainer:
    """
    Factory function to create and configure MCP container.

    Args:
        database_path: Optional database path override
        ai_generation_service: Optional AI generation service override
        ai_research_service: Optional AI research service override
        notification_service: Optional notification service override

    Returns:
        Configured MCPContainer instance
    """
    container = MCPContainer(
        database_path=database_path,
        ai_generation_service=ai_generation_service,
        ai_research_service=ai_research_service,
        notification_service=notification_service,
    )

    # Initialize database on creation
    container.initialize_database()

    return container
