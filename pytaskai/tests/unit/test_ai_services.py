"""
Unit tests for AI services implementation.

These tests focus on testing the OpenAI service adapter and AI configuration
without requiring actual OpenAI API calls.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pytaskai.application.dto.task_dto import TaskCreateDTO, TaskResponseDTO
from pytaskai.application.interfaces.ai_service import AIServiceError
from pytaskai.infrastructure.config.ai_config import (
    AIConfig,
    AIModel,
    AIProvider,
    ModelConfig,
    create_ai_config,
)
from pytaskai.infrastructure.external.openai_client import (
    OpenAIClient,
    OpenAIError,
    OpenAIResponse,
    create_openai_client,
)
from pytaskai.infrastructure.external.openai_service import (
    OpenAIResearchService,
    OpenAITaskGenerationService,
    create_openai_services,
)
from pytaskai.infrastructure.external.prompt_templates import (
    PromptContext,
    PromptTemplateFactory,
    PromptType,
    TaskBreakdownTemplate,
    create_prompt_context,
)


class TestAIConfig:
    """Test suite for AI configuration."""

    def test_ai_config_initialization(self):
        """Test basic AI config initialization."""
        config = AIConfig(
            openai_api_key="test-key",
            default_model=AIModel.GPT_3_5_TURBO.value,
        )

        assert config.openai_api_key == "test-key"
        assert config.default_model == AIModel.GPT_3_5_TURBO.value
        assert config.is_configured()
        assert config.has_openai_access()

    def test_ai_config_from_environment(self):
        """Test AI config creation from environment."""
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "env-key",
                "PYTASKAI_DEFAULT_MODEL": "gpt-4",
                "PYTASKAI_TEMPERATURE": "0.8",
            },
        ):
            config = AIConfig.from_environment()

            assert config.openai_api_key == "env-key"
            assert config.default_model == "gpt-4"
            assert config.temperature == 0.8

    def test_ai_config_for_testing(self):
        """Test AI config for testing environment."""
        config = AIConfig.for_testing()

        assert config.openai_api_key == "test-key"
        assert config.max_tokens == 100
        assert config.temperature == 0.0
        assert config.enable_cost_tracking

    def test_model_config_retrieval(self):
        """Test model configuration retrieval."""
        config = AIConfig()

        gpt4_config = config.get_model_config(AIModel.GPT_4.value)
        assert gpt4_config is not None
        assert gpt4_config.provider == AIProvider.OPENAI
        assert gpt4_config.supports_function_calling

        unknown_config = config.get_model_config("unknown-model")
        assert unknown_config is None

    def test_cost_estimation(self):
        """Test cost estimation functionality."""
        config = AIConfig()

        # Test GPT-3.5 Turbo cost estimation
        cost = config.estimate_cost(AIModel.GPT_3_5_TURBO.value, 1000, 500)
        expected_cost = (1000 / 1000) * 0.0015 + (500 / 1000) * 0.002
        assert abs(cost - expected_cost) < 0.0001

    def test_optimal_model_selection(self):
        """Test optimal model selection for tasks."""
        config = AIConfig(
            default_model=AIModel.GPT_3_5_TURBO.value,
            research_model=AIModel.GPT_4_TURBO.value,
            lts_model=AIModel.GPT_3_5_TURBO.value,
        )

        # High complexity should use research model
        model = config.get_optimal_model_for_task("analysis", "high")
        assert model == AIModel.GPT_4_TURBO.value

        # Low complexity should use LTS model
        model = config.get_optimal_model_for_task("suggestions", "low")
        assert model == AIModel.GPT_3_5_TURBO.value

        # Medium complexity should use default model
        model = config.get_optimal_model_for_task("breakdown", "medium")
        assert model == AIModel.GPT_3_5_TURBO.value

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Valid configuration
        valid_config = AIConfig(openai_api_key="test-key")
        errors = valid_config.validate_configuration()
        assert len(errors) == 0

        # Invalid configuration
        invalid_config = AIConfig(
            max_tokens=-1,
            temperature=3.0,
            request_timeout=0,
        )
        errors = invalid_config.validate_configuration()
        assert len(errors) > 0
        assert any("max_tokens" in error for error in errors)
        assert any("temperature" in error for error in errors)
        assert any("request_timeout" in error for error in errors)

    def test_create_ai_config_factory(self):
        """Test AI config factory function."""
        # Test with environment loading
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            config = create_ai_config(environment=True)
            assert config.openai_api_key == "env-key"

        # Test with overrides
        config = create_ai_config(
            environment=False,
            openai_api_key="override-key",
            temperature=0.9,
        )
        assert config.openai_api_key == "override-key"
        assert config.temperature == 0.9


class TestOpenAIClient:
    """Test suite for OpenAI client wrapper."""

    @pytest.fixture
    def ai_config(self):
        """Create test AI configuration."""
        return AIConfig.for_testing()

    @pytest.fixture
    def mock_openai_client(self, ai_config):
        """Create OpenAI client with mocked AsyncOpenAI."""
        with patch("pytaskai.infrastructure.external.openai_client.AsyncOpenAI"):
            return OpenAIClient(ai_config)

    def test_openai_client_initialization(self, ai_config):
        """Test OpenAI client initialization."""
        with patch(
            "pytaskai.infrastructure.external.openai_client.AsyncOpenAI"
        ) as mock_client:
            client = OpenAIClient(ai_config)

            assert client._config == ai_config
            assert client._total_cost == 0.0
            assert client._request_count == 0
            mock_client.assert_called_once_with(api_key=ai_config.openai_api_key)

    @pytest.mark.asyncio
    async def test_generate_completion_success(self, mock_openai_client):
        """Test successful completion generation."""
        # Mock successful OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.total_tokens = 100

        mock_openai_client._client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        response = await mock_openai_client.generate_completion(
            prompt="Test prompt",
            system_prompt="Test system prompt",
        )

        assert isinstance(response, OpenAIResponse)
        assert response.content == "Test response"
        assert response.tokens_used == 100
        assert response.success
        assert response.cost_estimate > 0

    @pytest.mark.asyncio
    async def test_generate_completion_with_retry_success(self, mock_openai_client):
        """Test completion generation with retry logic."""
        # Mock successful response on second attempt
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Success"
        mock_response.usage.total_tokens = 50

        # First call fails, second succeeds
        mock_openai_client._client.chat.completions.create = AsyncMock(
            side_effect=[Exception("Rate limit"), mock_response]
        )

        with patch.object(mock_openai_client, "_async_sleep", new_callable=AsyncMock):
            response = await mock_openai_client.generate_completion_with_retry(
                prompt="Test prompt",
                max_retries=2,
            )

        assert response.content == "Success"
        assert response.tokens_used == 50

    @pytest.mark.asyncio
    async def test_generate_completion_failure(self, mock_openai_client):
        """Test completion generation failure handling."""
        # Mock OpenAI API error
        from pytaskai.infrastructure.external.openai_client import OpenAIError

        mock_openai_client._client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        with pytest.raises(OpenAIError):
            await mock_openai_client.generate_completion("Test prompt")

    @pytest.mark.asyncio
    async def test_health_check(self, mock_openai_client):
        """Test OpenAI client health check."""
        # Mock successful health check
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "OK"
        mock_response.usage.total_tokens = 5

        mock_openai_client._client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        is_healthy = await mock_openai_client.health_check()
        assert is_healthy

        # Mock failed health check
        mock_openai_client._client.chat.completions.create = AsyncMock(
            side_effect=Exception("Connection error")
        )

        is_healthy = await mock_openai_client.health_check()
        assert not is_healthy

    def test_usage_stats(self, mock_openai_client):
        """Test usage statistics tracking."""
        # Simulate some usage
        mock_openai_client._request_count = 5
        mock_openai_client._total_cost = 0.25

        stats = mock_openai_client.get_usage_stats()

        assert stats["total_requests"] == 5
        assert stats["total_cost"] == 0.25
        assert stats["average_cost_per_request"] == 0.05

    def test_create_openai_client_factory(self, ai_config):
        """Test OpenAI client factory function."""
        with patch("pytaskai.infrastructure.external.openai_client.AsyncOpenAI"):
            client = create_openai_client(ai_config)
            assert isinstance(client, OpenAIClient)
            assert client._config == ai_config


class TestPromptTemplates:
    """Test suite for prompt templates."""

    def test_prompt_template_factory(self):
        """Test prompt template factory."""
        factory = PromptTemplateFactory()

        # Test creating different template types
        breakdown_template = factory.create_template(PromptType.TASK_BREAKDOWN)
        assert isinstance(breakdown_template, TaskBreakdownTemplate)

        suggestions_template = factory.create_template(PromptType.TASK_SUGGESTIONS)
        assert suggestions_template is not None

        # Test unsupported type
        with pytest.raises(ValueError, match="Unsupported prompt type"):
            factory.create_template("unsupported_type")

        # Test supported types list
        supported_types = factory.get_supported_types()
        assert PromptType.TASK_BREAKDOWN in supported_types
        assert PromptType.TASK_SUGGESTIONS in supported_types

    def test_task_breakdown_template(self):
        """Test task breakdown template generation."""
        template = TaskBreakdownTemplate()

        context = PromptContext(
            user_input="Implement user authentication system",
            project_context="Web application",
            max_items=5,
        )

        system_prompt, user_prompt = template.generate_prompt_pair(context)

        assert "project manager" in system_prompt.lower()
        assert "JSON array" in system_prompt
        assert "Implement user authentication system" in user_prompt
        assert "5 subtasks" in user_prompt
        assert "Web application" in user_prompt

    def test_task_breakdown_template_with_context(self):
        """Test task breakdown template with rich context."""
        template = TaskBreakdownTemplate()

        # Create task DTO for context
        task_dto = TaskResponseDTO(
            id="task123",
            title="Authentication System",
            description="Implement OAuth2 authentication",
            project="WebApp",
            task_type="Feature",
            status="Todo",
            assignee=None,
            parent_id=None,
            tags=[],
            priority="High",
            start_at=None,
            due_at=None,
            size=None,
            external_url=None,
            created_at=None,
            updated_at=None,
        )

        existing_tasks = [
            TaskResponseDTO(
                id="task456",
                title="Database Setup",
                project="WebApp",
                task_type="Task",
                status="Done",
                assignee=None,
                parent_id=None,
                tags=[],
                priority=None,
                start_at=None,
                due_at=None,
                size=None,
                external_url=None,
                description=None,
                created_at=None,
                updated_at=None,
            ),
        ]

        context = PromptContext(
            user_input="Break down authentication system",
            task_context=task_dto,
            project_context="E-commerce platform",
            existing_tasks=existing_tasks,
            breakdown_approach="functional",
            max_items=3,
        )

        system_prompt, user_prompt = template.generate_prompt_pair(context)

        assert "OAuth2 authentication" in user_prompt
        assert "High" in user_prompt
        assert "Database Setup" in user_prompt
        assert "functional" in user_prompt
        assert "3 subtasks" in user_prompt

    def test_create_prompt_context_factory(self):
        """Test prompt context factory function."""
        context = create_prompt_context(
            user_input="Test input",
            project_context="Test project",
            breakdown_approach="temporal",
            max_items=10,
        )

        assert context.user_input == "Test input"
        assert context.project_context == "Test project"
        assert context.breakdown_approach == "temporal"
        assert context.max_items == 10


class TestOpenAITaskGenerationService:
    """Test suite for OpenAI task generation service."""

    @pytest.fixture
    def ai_config(self):
        """Create test AI configuration."""
        return AIConfig.for_testing()

    @pytest.fixture
    def mock_openai_client(self, ai_config):
        """Create mock OpenAI client."""
        client = MagicMock(spec=OpenAIClient)
        client._config = ai_config
        return client

    @pytest.fixture
    def task_generation_service(self, mock_openai_client, ai_config):
        """Create task generation service with mocked client."""
        return OpenAITaskGenerationService(mock_openai_client, ai_config)

    @pytest.mark.asyncio
    async def test_generate_tasks_from_prd_success(
        self, task_generation_service, mock_openai_client
    ):
        """Test successful PRD task generation."""
        # Mock successful OpenAI response with JSON
        mock_response = OpenAIResponse(
            content='[{"title": "User Registration", "description": "Implement user signup", "task_type": "Feature", "priority": "High"}]',
            model="gpt-3.5-turbo",
            tokens_used=100,
            cost_estimate=0.01,
            response_time=1.0,
        )

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            return_value=mock_response
        )

        tasks = await task_generation_service.generate_tasks_from_prd(
            prd_content="Build a user registration system",
            project="TestProject",
            max_tasks=5,
        )

        assert len(tasks) == 1
        assert tasks[0].title == "User Registration"
        assert tasks[0].project == "TestProject"
        assert tasks[0].task_type == "Feature"
        assert tasks[0].priority == "High"

    @pytest.mark.asyncio
    async def test_generate_subtasks_success(
        self, task_generation_service, mock_openai_client
    ):
        """Test successful subtask generation."""
        # Mock successful response
        mock_response = OpenAIResponse(
            content='[{"title": "Setup Database Schema", "description": "Create user tables", "priority": "High"}]',
            model="gpt-3.5-turbo",
            tokens_used=75,
            cost_estimate=0.008,
            response_time=0.8,
        )

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            return_value=mock_response
        )

        subtasks = await task_generation_service.generate_subtasks(
            parent_task_description="Implement user authentication",
            project="TestProject",
            max_subtasks=3,
        )

        assert len(subtasks) == 1
        assert subtasks[0].title == "Setup Database Schema"
        assert subtasks[0].project == "TestProject"

    @pytest.mark.asyncio
    async def test_suggest_task_priority(
        self, task_generation_service, mock_openai_client
    ):
        """Test task priority suggestion."""
        mock_response = OpenAIResponse(
            content="High",
            model="gpt-3.5-turbo",
            tokens_used=10,
            cost_estimate=0.001,
            response_time=0.3,
        )

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            return_value=mock_response
        )

        priority = await task_generation_service.suggest_task_priority(
            task_title="Fix security vulnerability",
            task_description="SQL injection in login form",
        )

        assert priority == "High"

    @pytest.mark.asyncio
    async def test_estimate_task_size(
        self, task_generation_service, mock_openai_client
    ):
        """Test task size estimation."""
        mock_response = OpenAIResponse(
            content="L (Large)",
            model="gpt-3.5-turbo",
            tokens_used=15,
            cost_estimate=0.001,
            response_time=0.4,
        )

        mock_openai_client.generate_completion_with_retry = AsyncMock(
            return_value=mock_response
        )

        size = await task_generation_service.estimate_task_size(
            task_title="Implement complete user management system",
            task_description="Full CRUD operations with permissions",
        )

        assert size == "L"

    @pytest.mark.asyncio
    async def test_generate_tasks_openai_error(
        self, task_generation_service, mock_openai_client
    ):
        """Test error handling in task generation."""
        mock_openai_client.generate_completion_with_retry = AsyncMock(
            side_effect=OpenAIError("API rate limit exceeded")
        )

        with pytest.raises(AIServiceError, match="Failed to generate tasks from PRD"):
            await task_generation_service.generate_tasks_from_prd(
                prd_content="Test PRD",
                project="TestProject",
            )

    @pytest.mark.asyncio
    async def test_priority_suggestion_fallback(
        self, task_generation_service, mock_openai_client
    ):
        """Test priority suggestion fallback on error."""
        mock_openai_client.generate_completion_with_retry = AsyncMock(
            side_effect=OpenAIError("API timeout")
        )

        # Should return Medium as fallback, not raise exception
        priority = await task_generation_service.suggest_task_priority(
            task_title="Some task",
        )

        assert priority == "Medium"

    def test_parse_tasks_response_success(self, task_generation_service):
        """Test successful JSON parsing of tasks response."""
        json_response = """[
            {
                "title": "Task 1",
                "description": "Description 1",
                "task_type": "Feature",
                "priority": "High",
                "tags": ["backend"]
            },
            {
                "title": "Task 2",
                "description": "Description 2",
                "priority": "Medium"
            }
        ]"""

        tasks = task_generation_service._parse_tasks_response(
            json_response, "TestProject"
        )

        assert len(tasks) == 2
        assert tasks[0].title == "Task 1"
        assert tasks[0].project == "TestProject"
        assert tasks[0].task_type == "Feature"
        assert tasks[0].tags == ["backend"]
        assert tasks[1].title == "Task 2"
        assert tasks[1].priority == "Medium"

    def test_parse_tasks_response_fallback(self, task_generation_service):
        """Test fallback when JSON parsing fails."""
        invalid_response = "This is not valid JSON content"

        tasks = task_generation_service._parse_tasks_response(
            invalid_response, "TestProject"
        )

        # Should return fallback task
        assert len(tasks) == 1
        assert tasks[0].title == "Review AI Generated Tasks"
        assert tasks[0].project == "TestProject"
        assert "This is not valid JSON" in tasks[0].description


class TestCreateOpenAIServices:
    """Test suite for OpenAI services factory function."""

    def test_create_openai_services_success(self):
        """Test successful creation of OpenAI services."""
        config = AIConfig(openai_api_key="test-key")

        with patch(
            "pytaskai.infrastructure.external.openai_client.create_openai_client"
        ) as mock_create_client:
            mock_client = MagicMock(spec=OpenAIClient)
            mock_create_client.return_value = mock_client

            task_service, research_service = create_openai_services(config)

            assert isinstance(task_service, OpenAITaskGenerationService)
            assert isinstance(research_service, OpenAIResearchService)
            mock_create_client.assert_called_once_with(config)

    def test_create_openai_services_no_api_key(self):
        """Test error when OpenAI API key is not configured."""
        config = AIConfig()  # No API key

        with pytest.raises(AIServiceError, match="OpenAI API key not configured"):
            create_openai_services(config)
