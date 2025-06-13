"""
CLI Adapter dependency injection setup.

This module provides dependency injection configuration for the CLI adapter layer,
following the same patterns as the MCP adapter to ensure zero duplication of
business logic by reusing the same application container.
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


class CLIContainer:
    """
    CLI Adapter dependency injection container.

    This container reuses the same application layer as the MCP adapter,
    ensuring zero duplication of business logic while providing CLI-specific
    configuration and lifecycle management.
    """

    def __init__(
        self,
        database_path: Optional[str] = None,
        ai_generation_service: Optional[AITaskGenerationService] = None,
        ai_research_service: Optional[AIResearchService] = None,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        """
        Initialize CLI container with optional service overrides.

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

        # Initialize application container (same as MCP adapter)
        self._app_container = ApplicationContainer(
            repository=self._repository,
            ai_generation_service=ai_generation_service,
            ai_research_service=ai_research_service,
            notification_service=notification_service,
        )

    @staticmethod
    def _get_default_database_path() -> str:
        """Get default database path from environment or use fallback."""
        # Use same logic as MCP adapter for consistency
        project_root = os.getcwd()
        db_dir = os.path.join(project_root, ".pytaskai")
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, "tasks.db")

    @property
    def application_container(self) -> ApplicationContainer:
        """Get application container instance (same as MCP adapter)."""
        return self._app_container

    @property
    def database(self) -> Database:
        """Get database instance."""
        return self._database

    @property
    def database_path(self) -> str:
        """Get database file path."""
        return self._database_path

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
        """Get status of all services (same as MCP adapter)."""
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

    def cleanup(self) -> None:
        """Cleanup resources on CLI exit."""
        try:
            self.close_database()
        except Exception:
            pass  # Ignore cleanup errors


def create_cli_container(
    database_path: Optional[str] = None,
    ai_generation_service: Optional[AITaskGenerationService] = None,
    ai_research_service: Optional[AIResearchService] = None,
    notification_service: Optional[NotificationService] = None,
) -> CLIContainer:
    """
    Factory function to create and configure CLI container.

    This factory function creates the same container configuration as the MCP
    adapter, ensuring identical business logic execution between CLI and MCP.

    Args:
        database_path: Optional database path override
        ai_generation_service: Optional AI generation service override
        ai_research_service: Optional AI research service override
        notification_service: Optional notification service override

    Returns:
        Configured CLIContainer instance
    """
    container = CLIContainer(
        database_path=database_path,
        ai_generation_service=ai_generation_service,
        ai_research_service=ai_research_service,
        notification_service=notification_service,
    )

    # Initialize database on creation
    container.initialize_database()

    return container


def create_cli_container_with_ai() -> CLIContainer:
    """
    Create CLI container with AI services automatically configured.

    This function attempts to load AI services from environment variables
    and creates a fully configured container for CLI operations.

    Returns:
        CLIContainer with AI services if available

    Raises:
        ValueError: If AI configuration is invalid
    """
    ai_generation_service = None
    ai_research_service = None

    # Try to load AI services from environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from pytaskai.infrastructure.config.ai_config import AIConfig
            from pytaskai.infrastructure.external.openai_service import (
                OpenAIResearchService,
                OpenAITaskGenerationService,
            )

            ai_config = AIConfig.from_environment()
            ai_generation_service = OpenAITaskGenerationService(ai_config)
            ai_research_service = OpenAIResearchService(ai_config)

        except ImportError:
            # AI services not available, continue without AI
            pass
        except Exception as e:
            raise ValueError(f"Failed to initialize AI services: {e}")

    return create_cli_container(
        ai_generation_service=ai_generation_service,
        ai_research_service=ai_research_service,
    )
