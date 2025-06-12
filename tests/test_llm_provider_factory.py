"""
Comprehensive tests for LLM Provider Factory Pattern

Tests provider implementations, factory fallback mechanisms, 
cost tracking, and error handling.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from services.llm.base import (
    LLMProvider, LLMResponse, LLMError, RateLimitError, 
    QuotaExceededError, ModelNotFoundError, ProviderType, ModelRole
)
from services.llm.factory import LLMProviderFactory, FallbackConfig, get_llm_provider, ProviderHealth
from services.llm.openai_provider import OpenAIProvider
from services.llm.anthropic_provider import AnthropicProvider
from services.llm.perplexity_provider import PerplexityProvider


class MockProvider(LLMProvider):
    """Mock provider for testing"""
    
    def __init__(self, provider_type: ProviderType, should_fail: bool = False, 
                 should_rate_limit: bool = False):
        self._provider_type = provider_type
        self._should_fail = should_fail
        self._should_rate_limit = should_rate_limit
        self._supported_models = ["test-model-1", "test-model-2"]
        self._is_available = True
        self._initialized = True
    
    async def initialize(self) -> bool:
        """Initialize mock provider"""
        return not self._should_fail
        
    @property
    def provider_type(self) -> ProviderType:
        return self._provider_type
    
    @property
    def supported_models(self) -> list:
        return self._supported_models
    
    @property
    def is_available(self) -> bool:
        return self._is_available
    
    async def generate_response(self, prompt: str, model: str, **kwargs) -> LLMResponse:
        if self._should_rate_limit:
            raise RateLimitError("Rate limit exceeded", self._provider_type, model)
        if self._should_fail:
            raise LLMError("Provider failed", self._provider_type, model)
        
        return LLMResponse(
            content=f"Mock response from {self._provider_type.value} using {model}",
            model=model,
            provider=self._provider_type,
            tokens_used=100,
            cost=0.001,
            latency_ms=500
        )
    
    async def health_check(self) -> bool:
        return not self._should_fail
    
    def get_model_config(self, model: str):
        return None


@pytest.fixture
def mock_openai_provider():
    """Mock OpenAI provider"""
    return MockProvider(ProviderType.OPENAI)


@pytest.fixture
def mock_anthropic_provider():
    """Mock Anthropic provider"""
    return MockProvider(ProviderType.ANTHROPIC)


@pytest.fixture
def mock_failing_provider():
    """Mock failing provider"""
    return MockProvider(ProviderType.PERPLEXITY, should_fail=True)


@pytest.fixture
def mock_rate_limited_provider():
    """Mock rate limited provider"""
    return MockProvider(ProviderType.OPENAI, should_rate_limit=True)


@pytest.fixture
def factory_config():
    """Test factory configuration"""
    return FallbackConfig(
        max_retries=2,
        retry_delay_seconds=0.1,
        health_check_interval_minutes=1,
        max_consecutive_failures=2
    )


class TestLLMProviderFactory:
    """Test LLM Provider Factory"""
    
    def test_factory_initialization(self, factory_config):
        """Test factory initialization"""
        factory = LLMProviderFactory(factory_config)
        assert factory.config == factory_config
        assert not factory._initialized
        assert len(factory._providers) == 0
    
    @pytest.mark.asyncio
    async def test_factory_with_mocked_providers(self, factory_config):
        """Test factory with mocked providers"""
        factory = LLMProviderFactory(factory_config)
        
        # Mock the provider classes
        with patch.dict(factory.PROVIDER_CLASSES, {
            ProviderType.OPENAI: lambda: MockProvider(ProviderType.OPENAI),
            ProviderType.ANTHROPIC: lambda: MockProvider(ProviderType.ANTHROPIC)
        }):
            # Mock initialize method for providers
            with patch.object(MockProvider, 'initialize', return_value=True):
                success = await factory.initialize()
                assert success
                assert len(factory.available_providers) == 2
                assert ProviderType.OPENAI in factory.available_providers
                assert ProviderType.ANTHROPIC in factory.available_providers
    
    @pytest.mark.asyncio
    async def test_successful_response_generation(self, factory_config):
        """Test successful response generation"""
        factory = LLMProviderFactory(factory_config)
        
        # Add mock providers
        openai_provider = MockProvider(ProviderType.OPENAI)
        factory._providers[ProviderType.OPENAI] = openai_provider
        factory._health_status[ProviderType.OPENAI] = ProviderHealth(is_healthy=True, consecutive_failures=0)
        factory._initialized = True
        
        response = await factory.generate_response(
            prompt="Test prompt",
            provider=ProviderType.OPENAI,
            model="test-model-1"
        )
        
        assert response.content == "Mock response from openai using test-model-1"
        assert response.provider == ProviderType.OPENAI
        assert response.model == "test-model-1"
        assert response.tokens_used == 100
        assert response.cost == 0.001
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, factory_config):
        """Test fallback to secondary provider when primary fails"""
        factory = LLMProviderFactory(factory_config)
        
        # Add providers - first one fails, second succeeds
        failing_provider = MockProvider(ProviderType.OPENAI, should_fail=True)
        working_provider = MockProvider(ProviderType.ANTHROPIC)
        
        factory._providers[ProviderType.OPENAI] = failing_provider
        factory._providers[ProviderType.ANTHROPIC] = working_provider
        factory._health_status[ProviderType.OPENAI] = ProviderHealth(is_healthy=True, consecutive_failures=0)
        factory._health_status[ProviderType.ANTHROPIC] = ProviderHealth(is_healthy=True, consecutive_failures=0)
        factory._initialized = True
        
        # Set custom fallback chain
        factory.DEFAULT_FALLBACK_CHAINS[ModelRole.DEFAULT] = [
            ("openai", "test-model-1"),
            ("anthropic", "test-model-1")
        ]
        
        response = await factory.generate_response(
            prompt="Test prompt",
            role=ModelRole.DEFAULT
        )
        
        # Should fallback to Anthropic
        assert response.provider == ProviderType.ANTHROPIC
        assert "anthropic" in response.content
    
    @pytest.mark.asyncio
    async def test_rate_limit_fallback(self, factory_config):
        """Test fallback when provider hits rate limit"""
        factory = LLMProviderFactory(factory_config)
        
        rate_limited_provider = MockProvider(ProviderType.OPENAI, should_rate_limit=True)
        working_provider = MockProvider(ProviderType.ANTHROPIC)
        
        factory._providers[ProviderType.OPENAI] = rate_limited_provider
        factory._providers[ProviderType.ANTHROPIC] = working_provider
        factory._health_status[ProviderType.OPENAI] = ProviderHealth(is_healthy=True, consecutive_failures=0)
        factory._health_status[ProviderType.ANTHROPIC] = ProviderHealth(is_healthy=True, consecutive_failures=0)
        factory._initialized = True
        
        factory.DEFAULT_FALLBACK_CHAINS[ModelRole.DEFAULT] = [
            ("openai", "test-model-1"),
            ("anthropic", "test-model-1")
        ]
        
        response = await factory.generate_response(
            prompt="Test prompt",
            role=ModelRole.DEFAULT
        )
        
        assert response.provider == ProviderType.ANTHROPIC
    
    @pytest.mark.asyncio
    async def test_all_providers_fail(self, factory_config):
        """Test behavior when all providers fail"""
        factory = LLMProviderFactory(factory_config)
        
        failing_provider1 = MockProvider(ProviderType.OPENAI, should_fail=True)
        failing_provider2 = MockProvider(ProviderType.ANTHROPIC, should_fail=True)
        
        factory._providers[ProviderType.OPENAI] = failing_provider1
        factory._providers[ProviderType.ANTHROPIC] = failing_provider2
        factory._health_status[ProviderType.OPENAI] = ProviderHealth(is_healthy=True, consecutive_failures=0)
        factory._health_status[ProviderType.ANTHROPIC] = ProviderHealth(is_healthy=True, consecutive_failures=0)
        factory._initialized = True
        
        factory.DEFAULT_FALLBACK_CHAINS[ModelRole.DEFAULT] = [
            ("openai", "test-model-1"),
            ("anthropic", "test-model-1")
        ]
        
        with pytest.raises(LLMError, match="All providers failed"):
            await factory.generate_response(
                prompt="Test prompt",
                role=ModelRole.DEFAULT
            )
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, factory_config):
        """Test cost tracking functionality"""
        factory = LLMProviderFactory(factory_config)
        
        provider = MockProvider(ProviderType.OPENAI)
        factory._providers[ProviderType.OPENAI] = provider
        factory._health_status[ProviderType.OPENAI] = ProviderHealth(is_healthy=True, consecutive_failures=0)
        factory._initialized = True
        
        # Generate multiple responses
        for i in range(3):
            await factory.generate_response(
                prompt=f"Test prompt {i}",
                provider=ProviderType.OPENAI,
                model="test-model-1"
            )
        
        cost_summary = factory.get_cost_summary()
        assert "openai/test-model-1" in cost_summary
        assert cost_summary["openai/test-model-1"] == 0.003  # 3 * 0.001
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, factory_config):
        """Test provider health monitoring"""
        factory = LLMProviderFactory(factory_config)
        
        healthy_provider = MockProvider(ProviderType.OPENAI)
        unhealthy_provider = MockProvider(ProviderType.ANTHROPIC, should_fail=True)
        
        factory._providers[ProviderType.OPENAI] = healthy_provider
        factory._providers[ProviderType.ANTHROPIC] = unhealthy_provider
        # Initialize health status with expired timestamps to force health checks
        from datetime import datetime, timedelta
        expired_time = datetime.now() - timedelta(minutes=10)
        factory._health_status[ProviderType.OPENAI] = ProviderHealth(is_healthy=True, consecutive_failures=0, last_check=expired_time)
        factory._health_status[ProviderType.ANTHROPIC] = ProviderHealth(is_healthy=True, consecutive_failures=0, last_check=expired_time)
        factory._initialized = True
        
        # Check health
        openai_health = await factory._check_provider_health(ProviderType.OPENAI)
        anthropic_health = await factory._check_provider_health(ProviderType.ANTHROPIC)
        
        assert openai_health is True
        # Anthropic should fail health check since provider.should_fail = True
        assert anthropic_health is False
        
        health_summary = factory.get_health_summary()
        assert "openai" in health_summary
        assert "anthropic" in health_summary
        assert health_summary["openai"]["is_healthy"] is True
        assert health_summary["anthropic"]["is_healthy"] is False


class TestOpenAIProvider:
    """Test OpenAI provider implementation"""
    
    def test_provider_initialization(self):
        """Test OpenAI provider initialization"""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.provider_type == ProviderType.OPENAI
        assert len(provider.supported_models) > 0
        assert "gpt-4o-mini" in provider.supported_models
    
    def test_model_configurations(self):
        """Test model configurations"""
        provider = OpenAIProvider()
        
        config = provider.get_model_config("gpt-4o-mini")
        assert config is not None
        assert config.name == "gpt-4o-mini"
        assert config.provider == ProviderType.OPENAI
        assert config.cost_per_1k_tokens > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_with_mock(self):
        """Test response generation with mocked litellm"""
        provider = OpenAIProvider(api_key="test-key")
        provider._initialized = True
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 150
        mock_response.id = "test-id"
        
        with patch('services.llm.openai_provider.completion', return_value=mock_response):
            response = await provider.generate_response(
                prompt="Test prompt",
                model="gpt-4o-mini"
            )
            
            assert response.content == "Test response"
            assert response.model == "gpt-4o-mini"
            assert response.provider == ProviderType.OPENAI
            assert response.tokens_used == 150
    
    @pytest.mark.asyncio
    async def test_model_not_found_error(self):
        """Test model not found error handling"""
        provider = OpenAIProvider(api_key="test-key")
        provider._initialized = True
        
        # Should raise ModelNotFoundError which gets caught and re-raised as LLMError
        with pytest.raises((ModelNotFoundError, LLMError)):
            await provider.generate_response(
                prompt="Test prompt",
                model="nonexistent-model"
            )


class TestAnthropicProvider:
    """Test Anthropic provider implementation"""
    
    def test_provider_initialization(self):
        """Test Anthropic provider initialization"""
        provider = AnthropicProvider(api_key="test-key")
        assert provider.provider_type == ProviderType.ANTHROPIC
        assert len(provider.supported_models) > 0
        assert "claude-3-haiku-20240307" in provider.supported_models
    
    def test_model_configurations(self):
        """Test model configurations"""
        provider = AnthropicProvider()
        
        config = provider.get_model_config("claude-3-haiku-20240307")
        assert config is not None
        assert config.name == "claude-3-haiku-20240307"
        assert config.provider == ProviderType.ANTHROPIC
        assert config.cost_per_1k_tokens > 0


class TestPerplexityProvider:
    """Test Perplexity provider implementation"""
    
    def test_provider_initialization(self):
        """Test Perplexity provider initialization"""
        provider = PerplexityProvider(api_key="test-key")
        assert provider.provider_type == ProviderType.PERPLEXITY
        assert len(provider.supported_models) > 0
        assert "llama-3.1-8b-instruct" in provider.supported_models
    
    def test_web_search_detection(self):
        """Test web search capability detection"""
        provider = PerplexityProvider()
        
        assert provider.has_web_search("llama-3.1-sonar-small-128k-online") is True
        assert provider.has_web_search("llama-3.1-8b-instruct") is False


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test convenience function with mocked providers"""
        with patch('services.llm.factory._factory_instance', None):
            # Mock the factory initialization
            mock_factory = Mock()
            mock_factory.initialize = AsyncMock()
            mock_factory.generate_response = AsyncMock(return_value=LLMResponse(
                content="Test response",
                model="test-model",
                provider=ProviderType.OPENAI,
                tokens_used=100,
                cost=0.001
            ))
            
            with patch('services.llm.factory.LLMProviderFactory', return_value=mock_factory):
                response = await get_llm_provider(
                    prompt="Test prompt",
                    model="gpt-4o-mini"
                )
                
                assert response.content == "Test response"
                mock_factory.initialize.assert_called_once()
                mock_factory.generate_response.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])