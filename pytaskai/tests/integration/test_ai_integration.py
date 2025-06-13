"""
Integration tests for AI services.

These tests verify the integration between AI services and the application layer,
using mocked OpenAI responses to avoid actual API calls during testing.
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pytaskai.application.container import ApplicationContainer
from pytaskai.application.dto.task_dto import TaskCreateDTO, TaskResponseDTO
from pytaskai.application.use_cases.ai_task_generation import AITaskGenerationUseCase
from pytaskai.application.use_cases.task_management import TaskManagementUseCase
from pytaskai.infrastructure.config.ai_config import AIConfig
from pytaskai.infrastructure.config.database_config import DatabaseConfig
from pytaskai.infrastructure.external.openai_client import OpenAIClient, OpenAIResponse
from pytaskai.infrastructure.external.openai_service import (
    OpenAIResearchService,
    OpenAITaskGenerationService,
)
from pytaskai.infrastructure.persistence.database import Database
from pytaskai.infrastructure.persistence.sqlite_task_repository import (
    SQLiteTaskRepository,
)


class TestAITaskGenerationIntegration:
    """Integration tests for AI task generation use case."""

    @pytest.fixture
    def database_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        yield tmp_path
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    @pytest.fixture
    def app_container(self, database_path):
        """Create application container with real database."""
        db_config = DatabaseConfig(url=f"sqlite:///{database_path}")
        database = Database(db_config)
        database.initialize()

        repository = SQLiteTaskRepository(database)

        container = ApplicationContainer(
            repository=repository,
            ai_generation_service=None,  # Will be mocked
            ai_research_service=None,  # Will be mocked
            notification_service=None,
        )

        yield container

        database.close()

    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client."""
        client = MagicMock(spec=OpenAIClient)
        return client

    @pytest.fixture
    def ai_config(self):
        """Create AI configuration for testing."""
        return AIConfig.for_testing()

    @pytest.fixture
    def ai_task_generation_service(self, mock_openai_client, ai_config):
        """Create AI task generation service with mocked client."""
        return OpenAITaskGenerationService(mock_openai_client, ai_config)

    @pytest.fixture
    def ai_research_service(self, mock_openai_client, ai_config):
        """Create AI research service with mocked client."""
        return OpenAIResearchService(mock_openai_client, ai_config)

    @pytest.fixture
    def ai_use_case(
        self, app_container, ai_task_generation_service, ai_research_service
    ):
        """Create AI task generation use case."""
        task_management_use_case = TaskManagementUseCase(
            repository=app_container.repository,
            task_service=app_container.task_service,
        )

        return AITaskGenerationUseCase(
            task_management_use_case=task_management_use_case,
            ai_generation_service=ai_task_generation_service,
            ai_research_service=ai_research_service,
        )

    @pytest.mark.asyncio
    async def test_generate_tasks_from_prd_integration(
        self, ai_use_case, mock_openai_client
    ):
        """Test complete PRD task generation workflow."""
        # Mock OpenAI response with realistic task data
        prd_response = """[
            {
                "title": "User Registration API",
                "description": "Implement REST API endpoints for user registration",
                "task_type": "Feature",
                "priority": "High",
                "size": "M",
                "tags": ["backend", "api"]
            },
            {
                "title": "User Registration Frontend",
                "description": "Create registration form and validation",
                "task_type": "Feature", 
                "priority": "High",
                "size": "M",
                "tags": ["frontend", "ui"]
            },
            {
                "title": "Registration Unit Tests",
                "description": "Write comprehensive unit tests for registration flow",
                "task_type": "Task",
                "priority": "Medium",
                "size": "S",
                "tags": ["testing"]
            }
        ]"""

        # Mock research context for each task
        research_context = "**Research Context:**\nUser registration is a critical security component..."

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            side_effect=[
                # PRD parsing response
                OpenAIResponse(
                    content=prd_response,
                    model="gpt-4-turbo",
                    tokens_used=200,
                    cost_estimate=0.02,
                    response_time=1.5,
                ),
                # Research responses for each task
                OpenAIResponse(
                    content=research_context,
                    model="gpt-4-turbo",
                    tokens_used=150,
                    cost_estimate=0.015,
                    response_time=1.2,
                ),
                OpenAIResponse(
                    content=research_context,
                    model="gpt-4-turbo",
                    tokens_used=150,
                    cost_estimate=0.015,
                    response_time=1.1,
                ),
                OpenAIResponse(
                    content=research_context,
                    model="gpt-4-turbo",
                    tokens_used=150,
                    cost_estimate=0.015,
                    response_time=1.0,
                ),
            ]
        )

        # Generate tasks from PRD
        generated_tasks = await ai_use_case.generate_tasks_from_prd(
            prd_content="Build a user registration system with secure authentication",
            project="WebApp",
            auto_create=False,
            max_tasks=5,
        )

        # Verify tasks were generated correctly
        assert len(generated_tasks) == 3

        # Check first task (API)
        api_task = generated_tasks[0]
        assert api_task.title == "User Registration API"
        assert api_task.project == "WebApp"
        assert api_task.task_type == "Feature"
        assert api_task.priority == "High"
        assert api_task.size == "M"
        assert "backend" in api_task.tags
        assert "Research Context" in api_task.description

        # Check second task (Frontend)
        frontend_task = generated_tasks[1]
        assert frontend_task.title == "User Registration Frontend"
        assert "frontend" in frontend_task.tags

        # Check third task (Testing)
        test_task = generated_tasks[2]
        assert test_task.title == "Registration Unit Tests"
        assert test_task.task_type == "Task"
        assert "testing" in test_task.tags

        # Verify OpenAI client was called correctly
        assert (
            mock_openai_client.generate_completion_with_retry.call_count == 4
        )  # 1 PRD + 3 research

    @pytest.mark.asyncio
    async def test_generate_tasks_with_auto_create(
        self, ai_use_case, mock_openai_client
    ):
        """Test PRD task generation with automatic task creation."""
        # Mock simple response
        mock_response = """[
            {
                "title": "Simple Task",
                "description": "A simple test task",
                "task_type": "Task",
                "priority": "Medium"
            }
        ]"""

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            return_value=OpenAIResponse(
                content=mock_response,
                model="gpt-3.5-turbo",
                tokens_used=50,
                cost_estimate=0.005,
                response_time=0.8,
            )
        )

        # Generate and auto-create tasks
        generated_tasks = await ai_use_case.generate_tasks_from_prd(
            prd_content="Create a simple feature",
            project="TestProject",
            auto_create=True,
            max_tasks=1,
        )

        assert len(generated_tasks) == 1
        assert generated_tasks[0].title == "Simple Task"

        # Verify task was actually created in database
        # Note: This tests the integration with the task management layer
        task_management = ai_use_case._task_management
        from pytaskai.application.dto.task_dto import TaskListFiltersDTO

        filters = TaskListFiltersDTO()
        all_tasks = await task_management.list_tasks(filters)

        created_task = next((t for t in all_tasks if t.title == "Simple Task"), None)
        assert created_task is not None
        assert created_task.project == "TestProject"

    @pytest.mark.asyncio
    async def test_generate_subtasks_integration(self, ai_use_case, mock_openai_client):
        """Test subtask generation workflow."""
        # First create a parent task
        parent_task_dto = TaskCreateDTO(
            title="Implement Authentication System",
            description="Complete OAuth2 authentication with JWT tokens",
            project="WebApp",
            task_type="Feature",
            status="Todo",
            priority="High",
        )

        task_management = ai_use_case._task_management
        parent_task = await task_management.create_task(parent_task_dto)

        # Mock subtask generation response
        subtasks_response = """[
            {
                "title": "Setup JWT Token Generation",
                "description": "Implement JWT token creation and signing",
                "task_type": "Task",
                "priority": "High",
                "size": "M"
            },
            {
                "title": "Implement OAuth2 Endpoints",
                "description": "Create authorize and token endpoints",
                "task_type": "Task",
                "priority": "High",
                "size": "L"
            },
            {
                "title": "Add Token Validation Middleware",
                "description": "Create middleware to validate JWT tokens",
                "task_type": "Task",
                "priority": "Medium",
                "size": "S"
            }
        ]"""

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            return_value=OpenAIResponse(
                content=subtasks_response,
                model="gpt-3.5-turbo",
                tokens_used=180,
                cost_estimate=0.018,
                response_time=1.3,
            )
        )

        # Generate subtasks
        generated_subtasks = await ai_use_case.generate_subtasks(
            parent_task_id=parent_task.task_id,
            max_subtasks=5,
            auto_create=True,
        )

        # Verify subtasks
        assert len(generated_subtasks) == 3

        # Check that all subtasks have the correct parent_id
        for subtask in generated_subtasks:
            assert subtask.parent_id == parent_task.task_id
            assert subtask.project == parent_task.project
            assert (
                subtask.assignee == parent_task.assignee
            )  # Should inherit from parent

        # Verify subtasks were created in database
        from pytaskai.application.dto.task_dto import TaskListFiltersDTO

        filters = TaskListFiltersDTO()
        all_tasks = await task_management.list_tasks(filters)
        created_subtasks = [t for t in all_tasks if t.parent_id == parent_task.task_id]

        assert len(created_subtasks) == 3
        assert any(t.title == "Setup JWT Token Generation" for t in created_subtasks)
        assert any(t.title == "Implement OAuth2 Endpoints" for t in created_subtasks)
        assert any(
            t.title == "Add Token Validation Middleware" for t in created_subtasks
        )

    @pytest.mark.asyncio
    async def test_enhance_task_with_ai_integration(
        self, ai_use_case, mock_openai_client
    ):
        """Test AI task enhancement workflow."""
        # Create a task without priority and size
        task_dto = TaskCreateDTO(
            title="Refactor user service",
            description="Clean up the user service code and improve performance",
            project="WebApp",
            task_type="Task",
            status="Todo",
        )

        task_management = ai_use_case._task_management
        created_task = await task_management.create_task(task_dto)

        # Mock AI enhancement responses
        mock_openai_client.generate_completion_with_retry = AsyncMock(
            side_effect=[
                # Priority suggestion
                OpenAIResponse(
                    content="Medium",
                    model="gpt-3.5-turbo",
                    tokens_used=10,
                    cost_estimate=0.001,
                    response_time=0.3,
                ),
                # Size estimation
                OpenAIResponse(
                    content="M",
                    model="gpt-3.5-turbo",
                    tokens_used=15,
                    cost_estimate=0.0015,
                    response_time=0.4,
                ),
            ]
        )

        # Enhance task with AI
        enhanced_task = await ai_use_case.enhance_task_with_ai(
            task_id=created_task.task_id,
            enhance_priority=True,
            enhance_size=True,
        )

        # Verify enhancements
        assert enhanced_task.priority == "Medium"
        assert enhanced_task.size == "M"
        assert enhanced_task.title == "Refactor user service"  # Should remain unchanged

        # Verify task was updated in database
        updated_task = await task_management.get_task(created_task.task_id)
        assert updated_task.priority == "Medium"
        assert updated_task.size == "M"

    @pytest.mark.asyncio
    async def test_suggest_follow_up_tasks_integration(
        self, ai_use_case, mock_openai_client
    ):
        """Test follow-up task suggestions workflow."""
        # Create and mark a task as completed
        task_dto = TaskCreateDTO(
            title="Implement User Registration",
            description="Basic user registration functionality",
            project="WebApp",
            task_type="Feature",
            status="Done",
        )

        task_management = ai_use_case._task_management
        completed_task = await task_management.create_task(task_dto)

        # Mock follow-up suggestions response
        follow_up_response = """[
            {
                "title": "Add Email Verification",
                "description": "Implement email verification for new registrations",
                "task_type": "Enhancement",
                "priority": "High",
                "reasoning": "Security improvement for user registration"
            },
            {
                "title": "User Registration Analytics",
                "description": "Track registration conversion rates and user sources",
                "task_type": "Task",
                "priority": "Medium",
                "reasoning": "Data-driven insights for registration optimization"
            }
        ]"""

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            return_value=OpenAIResponse(
                content=follow_up_response,
                model="gpt-4-turbo",
                tokens_used=120,
                cost_estimate=0.012,
                response_time=1.1,
            )
        )

        # Generate follow-up suggestions
        suggested_tasks = await ai_use_case.suggest_follow_up_tasks(
            completed_task_id=completed_task.task_id,
            auto_create=True,
        )

        # Verify suggestions
        assert len(suggested_tasks) == 2

        email_task = suggested_tasks[0]
        assert email_task.title == "Add Email Verification"
        assert email_task.task_type == "Enhancement"
        assert email_task.priority == "High"
        assert email_task.project == "WebApp"

        analytics_task = suggested_tasks[1]
        assert analytics_task.title == "User Registration Analytics"
        assert analytics_task.priority == "Medium"

        # Verify tasks were created in database
        from pytaskai.application.dto.task_dto import TaskListFiltersDTO

        filters = TaskListFiltersDTO()
        all_tasks = await task_management.list_tasks(filters)
        created_suggestions = [
            t
            for t in all_tasks
            if t.title in ["Add Email Verification", "User Registration Analytics"]
        ]

        assert len(created_suggestions) == 2

    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self, ai_use_case, mock_openai_client):
        """Test error handling in AI integration."""
        # Mock OpenAI error
        from pytaskai.application.interfaces.ai_service import AIServiceError
        from pytaskai.infrastructure.external.openai_client import OpenAIError

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            side_effect=OpenAIError("API rate limit exceeded")
        )

        # Test that AIServiceError is properly propagated
        with pytest.raises(AIServiceError, match="Failed to generate tasks from PRD"):
            await ai_use_case.generate_tasks_from_prd(
                prd_content="Test PRD",
                project="TestProject",
            )

    @pytest.mark.asyncio
    async def test_ai_enhancement_graceful_degradation(
        self, ai_use_case, mock_openai_client
    ):
        """Test graceful degradation when AI enhancement fails."""
        # Create a task
        task_dto = TaskCreateDTO(
            title="Test task",
            project="WebApp",
            task_type="Task",
            status="Todo",
        )

        task_management = ai_use_case._task_management
        created_task = await task_management.create_task(task_dto)

        # Mock AI service failure
        from pytaskai.infrastructure.external.openai_client import OpenAIError

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            side_effect=OpenAIError("API timeout")
        )

        # Enhancement should not fail, but return original task
        enhanced_task = await ai_use_case.enhance_task_with_ai(
            task_id=created_task.task_id,
            enhance_priority=True,
            enhance_size=True,
        )

        # Should return original task unchanged
        assert enhanced_task.task_id == created_task.task_id
        assert enhanced_task.title == created_task.title
        assert enhanced_task.priority == created_task.priority  # Should remain None
        assert enhanced_task.size == created_task.size  # Should remain None
