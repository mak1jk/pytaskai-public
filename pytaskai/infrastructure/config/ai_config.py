"""
AI configuration for PyTaskAI infrastructure layer.

This module provides configuration management for AI services,
following the configuration pattern to centralize all AI-related settings.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class AIProvider(Enum):
    """Supported AI providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GOOGLE = "google"
    XAI = "xai"


class AIModel(Enum):
    """Supported AI models with their identifiers."""

    # OpenAI models
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K = "gpt-3.5-turbo-16k"

    # Anthropic models (for future implementation)
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

    # Perplexity models (for future implementation)
    PERPLEXITY_LLAMA = "llama-3.1-sonar-large-128k-online"
    PERPLEXITY_MIXTRAL = "mixtral-8x7b-instruct"


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for a specific AI model."""

    name: str
    provider: AIProvider
    max_tokens: int
    cost_per_1k_input: float  # USD per 1000 input tokens
    cost_per_1k_output: float  # USD per 1000 output tokens
    context_window: int  # Maximum context window size
    supports_function_calling: bool = False
    supports_json_mode: bool = False


@dataclass
class AIConfig:
    """
    Configuration for AI services in PyTaskAI.

    This class centralizes all AI-related configuration including
    API keys, model preferences, and operational parameters.
    """

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None

    # Model Configuration
    default_model: str = AIModel.GPT_3_5_TURBO.value
    research_model: str = AIModel.GPT_4_TURBO.value
    lts_model: str = AIModel.GPT_3_5_TURBO.value
    fallback_model: str = AIModel.GPT_3_5_TURBO.value

    # Request Configuration
    max_tokens: int = 2000
    temperature: float = 0.7
    request_timeout: int = 60  # seconds
    max_retries: int = 3

    # Cost Management
    max_cost_per_request: float = 0.50  # USD
    daily_cost_limit: float = 10.0  # USD
    enable_cost_tracking: bool = True

    # Feature Flags
    enable_ai_services: bool = True
    enable_task_breakdown: bool = True
    enable_smart_suggestions: bool = True
    enable_template_generation: bool = True
    enable_task_analysis: bool = True

    # Rate Limiting
    requests_per_minute: int = 20
    requests_per_hour: int = 200

    # Model Configurations (immutable)
    model_configs: Dict[str, ModelConfig] = field(
        default_factory=lambda: {
            AIModel.GPT_4.value: ModelConfig(
                name="GPT-4",
                provider=AIProvider.OPENAI,
                max_tokens=8192,
                cost_per_1k_input=0.03,
                cost_per_1k_output=0.06,
                context_window=8192,
                supports_function_calling=True,
                supports_json_mode=True,
            ),
            AIModel.GPT_4_TURBO.value: ModelConfig(
                name="GPT-4 Turbo",
                provider=AIProvider.OPENAI,
                max_tokens=4096,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
                context_window=128000,
                supports_function_calling=True,
                supports_json_mode=True,
            ),
            AIModel.GPT_3_5_TURBO.value: ModelConfig(
                name="GPT-3.5 Turbo",
                provider=AIProvider.OPENAI,
                max_tokens=4096,
                cost_per_1k_input=0.0015,
                cost_per_1k_output=0.002,
                context_window=16385,
                supports_function_calling=True,
                supports_json_mode=True,
            ),
            AIModel.GPT_3_5_TURBO_16K.value: ModelConfig(
                name="GPT-3.5 Turbo 16K",
                provider=AIProvider.OPENAI,
                max_tokens=4096,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.004,
                context_window=16385,
                supports_function_calling=True,
                supports_json_mode=True,
            ),
        }
    )

    @classmethod
    def from_environment(cls) -> "AIConfig":
        """
        Create AI configuration from environment variables.

        Returns:
            AIConfig instance populated from environment
        """
        return cls(
            # API Keys
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            xai_api_key=os.getenv("XAI_API_KEY"),
            # Model Selection
            default_model=os.getenv(
                "PYTASKAI_DEFAULT_MODEL", AIModel.GPT_3_5_TURBO.value
            ),
            research_model=os.getenv(
                "PYTASKAI_RESEARCH_MODEL", AIModel.GPT_4_TURBO.value
            ),
            lts_model=os.getenv("PYTASKAI_LTS_MODEL", AIModel.GPT_3_5_TURBO.value),
            fallback_model=os.getenv(
                "PYTASKAI_FALLBACK_MODEL", AIModel.GPT_3_5_TURBO.value
            ),
            # Request Configuration
            max_tokens=int(os.getenv("PYTASKAI_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("PYTASKAI_TEMPERATURE", "0.7")),
            request_timeout=int(os.getenv("PYTASKAI_REQUEST_TIMEOUT", "60")),
            max_retries=int(os.getenv("PYTASKAI_MAX_RETRIES", "3")),
            # Cost Management
            max_cost_per_request=float(
                os.getenv("PYTASKAI_MAX_COST_PER_REQUEST", "0.50")
            ),
            daily_cost_limit=float(os.getenv("PYTASKAI_DAILY_COST_LIMIT", "10.0")),
            enable_cost_tracking=os.getenv(
                "PYTASKAI_ENABLE_COST_TRACKING", "true"
            ).lower()
            == "true",
            # Feature Flags
            enable_ai_services=os.getenv("PYTASKAI_ENABLE_AI_SERVICES", "true").lower()
            == "true",
            enable_task_breakdown=os.getenv(
                "PYTASKAI_ENABLE_TASK_BREAKDOWN", "true"
            ).lower()
            == "true",
            enable_smart_suggestions=os.getenv(
                "PYTASKAI_ENABLE_SMART_SUGGESTIONS", "true"
            ).lower()
            == "true",
            enable_template_generation=os.getenv(
                "PYTASKAI_ENABLE_TEMPLATE_GENERATION", "true"
            ).lower()
            == "true",
            enable_task_analysis=os.getenv(
                "PYTASKAI_ENABLE_TASK_ANALYSIS", "true"
            ).lower()
            == "true",
            # Rate Limiting
            requests_per_minute=int(os.getenv("PYTASKAI_REQUESTS_PER_MINUTE", "20")),
            requests_per_hour=int(os.getenv("PYTASKAI_REQUESTS_PER_HOUR", "200")),
        )

    @classmethod
    def for_testing(cls) -> "AIConfig":
        """
        Create AI configuration for testing with safe defaults.

        Returns:
            AIConfig instance configured for testing
        """
        return cls(
            openai_api_key="test-key",
            default_model=AIModel.GPT_3_5_TURBO.value,
            max_tokens=100,
            temperature=0.0,
            request_timeout=10,
            max_retries=1,
            max_cost_per_request=0.01,
            daily_cost_limit=1.0,
            enable_cost_tracking=True,
            requests_per_minute=5,
            requests_per_hour=20,
        )

    def is_configured(self) -> bool:
        """
        Check if AI configuration is properly set up.

        Returns:
            True if at least one API key is configured
        """
        return any(
            [
                self.openai_api_key,
                self.anthropic_api_key,
                self.perplexity_api_key,
                self.google_api_key,
                self.xai_api_key,
            ]
        )

    def has_openai_access(self) -> bool:
        """
        Check if OpenAI API access is configured.

        Returns:
            True if OpenAI API key is set
        """
        return bool(self.openai_api_key and self.openai_api_key.strip())

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """
        Get configuration for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            ModelConfig if found, None otherwise
        """
        return self.model_configs.get(model_name)

    def get_available_models(self) -> list[str]:
        """
        Get list of available model names.

        Returns:
            List of configured model names
        """
        return list(self.model_configs.keys())

    def estimate_cost(
        self, model_name: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Estimate cost for an AI request.

        Args:
            model_name: Name of the model
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        model_config = self.get_model_config(model_name)
        if not model_config:
            return 0.0

        input_cost = (input_tokens / 1000) * model_config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model_config.cost_per_1k_output

        return input_cost + output_cost

    def get_optimal_model_for_task(
        self, task_type: str, complexity: str = "medium"
    ) -> str:
        """
        Get optimal model for a specific task type and complexity.

        Args:
            task_type: Type of AI task (breakdown, suggestions, etc.)
            complexity: Task complexity (low, medium, high)

        Returns:
            Recommended model name
        """
        # Simple heuristics for model selection
        if complexity == "high" or task_type in ["analysis", "research"]:
            return self.research_model
        elif complexity == "low" or task_type in ["suggestions", "templates"]:
            return self.lts_model
        else:
            return self.default_model

    def validate_configuration(self) -> list[str]:
        """
        Validate the configuration and return any issues.

        Returns:
            List of validation error messages
        """
        errors = []

        if not self.is_configured():
            errors.append("No AI API keys configured")

        if self.max_tokens <= 0:
            errors.append("max_tokens must be positive")

        if not (0.0 <= self.temperature <= 2.0):
            errors.append("temperature must be between 0.0 and 2.0")

        if self.request_timeout <= 0:
            errors.append("request_timeout must be positive")

        if self.max_cost_per_request <= 0:
            errors.append("max_cost_per_request must be positive")

        if self.daily_cost_limit <= 0:
            errors.append("daily_cost_limit must be positive")

        return errors


def create_ai_config(environment: bool = True, **overrides) -> AIConfig:
    """
    Factory function to create AI configuration.

    Args:
        environment: Whether to load from environment variables
        **overrides: Configuration overrides

    Returns:
        Configured AIConfig instance
    """
    if environment:
        config = AIConfig.from_environment()
    else:
        config = AIConfig()

    # Apply any overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config
