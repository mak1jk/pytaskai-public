"""
LLM Provider Factory

Factory pattern implementation for managing multiple LLM providers with
intelligent fallback mechanisms, cost optimization, and health monitoring.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from .base import (
    LLMProvider, LLMResponse, LLMError, RateLimitError, 
    QuotaExceededError, ModelNotFoundError, ProviderType, ModelRole
)
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .perplexity_provider import PerplexityProvider

logger = logging.getLogger(__name__)


@dataclass
class ProviderHealth:
    """Health status for a provider"""
    is_healthy: bool = True
    last_check: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    last_error: Optional[str] = None
    consecutive_failures: int = 0


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior"""
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    health_check_interval_minutes: int = 5
    max_consecutive_failures: int = 3
    cost_optimization: bool = True
    prefer_cached: bool = True


class LLMProviderFactory:
    """Factory for managing multiple LLM providers with intelligent fallback"""
    
    # Provider class mapping
    PROVIDER_CLASSES: Dict[ProviderType, Type[LLMProvider]] = {
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.ANTHROPIC: AnthropicProvider,
        ProviderType.PERPLEXITY: PerplexityProvider,
    }
    
    # Default fallback chains by role
    DEFAULT_FALLBACK_CHAINS = {
        ModelRole.RESEARCH: [
            ("perplexity", "llama-3.1-sonar-small-128k-online"),
            ("perplexity", "llama-3.1-sonar-large-128k-online"),
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-haiku-20240307")
        ],
        ModelRole.TASK_GENERATION: [
            ("openai", "gpt-4o-mini"),
            ("openai", "gpt-4o"),
            ("anthropic", "claude-3-5-haiku-20241022"),
            ("anthropic", "claude-3-5-sonnet-20241022")
        ],
        ModelRole.BEST_PRACTICES: [
            ("anthropic", "claude-3-5-sonnet-20241022"),
            ("anthropic", "claude-3-opus-20240229"),
            ("openai", "gpt-4o"),
            ("openai", "gpt-4-turbo")
        ],
        ModelRole.DEFAULT: [
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-haiku-20240307"),
            ("perplexity", "llama-3.1-8b-instruct"),
            ("openai", "gpt-3.5-turbo")
        ]
    }
    
    def __init__(self, config: Optional[FallbackConfig] = None):
        self.config = config or FallbackConfig()
        self._providers: Dict[ProviderType, LLMProvider] = {}
        self._health_status: Dict[ProviderType, ProviderHealth] = {}
        self._initialized = False
        self._cost_tracker: Dict[str, float] = {}
        
    async def initialize(self) -> bool:
        """Initialize all available providers"""
        try:
            # Initialize providers
            for provider_type, provider_class in self.PROVIDER_CLASSES.items():
                try:
                    provider = provider_class()
                    if await provider.initialize():
                        self._providers[provider_type] = provider
                        self._health_status[provider_type] = ProviderHealth()
                        logger.info(f"Initialized {provider_type} provider")
                    else:
                        logger.warning(f"Failed to initialize {provider_type} provider")
                except Exception as e:
                    logger.error(f"Error initializing {provider_type}: {e}")
                    
            self._initialized = True
            logger.info(f"LLM Factory initialized with {len(self._providers)} providers")
            return len(self._providers) > 0
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM factory: {e}")
            return False
    
    @property
    def available_providers(self) -> List[ProviderType]:
        """Get list of available provider types"""
        return list(self._providers.keys())
    
    @property
    def healthy_providers(self) -> List[ProviderType]:
        """Get list of healthy provider types"""
        return [
            provider_type for provider_type, health in self._health_status.items()
            if health.is_healthy and provider_type in self._providers
        ]
    
    async def get_provider(self, provider_type: ProviderType) -> Optional[LLMProvider]:
        """Get a specific provider by type"""
        if not self._initialized:
            await self.initialize()
            
        return self._providers.get(provider_type)
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[ProviderType] = None,
        role: ModelRole = ModelRole.DEFAULT,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate response with intelligent fallback"""
        
        if not self._initialized:
            await self.initialize()
        
        # Determine fallback chain
        if provider and model:
            # Use specific provider and model
            fallback_chain = [(provider.value, model)]
        elif model:
            # Find provider that supports this model
            fallback_chain = await self._find_provider_for_model(model)
        else:
            # Use default fallback chain for role
            fallback_chain = self.DEFAULT_FALLBACK_CHAINS.get(role, self.DEFAULT_FALLBACK_CHAINS[ModelRole.DEFAULT])
        
        # Try each provider/model in fallback chain
        last_error = None
        for attempt, (provider_name, model_name) in enumerate(fallback_chain):
            try:
                provider_type = ProviderType(provider_name)
                provider_instance = await self.get_provider(provider_type)
                
                if not provider_instance:
                    logger.warning(f"Provider {provider_type} not available")
                    continue
                
                # Check provider health
                if not await self._check_provider_health(provider_type):
                    logger.warning(f"Provider {provider_type} is unhealthy, skipping")
                    continue
                
                # Generate response
                response = await provider_instance.generate_response(
                    prompt=prompt,
                    model=model_name,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Update health status (success)
                self._update_health_status(provider_type, success=True)
                
                # Track cost
                self._track_cost(provider_type, model_name, response.cost)
                
                logger.info(f"Successfully generated response using {provider_type}/{model_name}")
                return response
                
            except (RateLimitError, QuotaExceededError) as e:
                logger.warning(f"Provider {provider_name} error: {e}")
                self._update_health_status(ProviderType(provider_name), success=False, error=str(e))
                last_error = e
                
                # Wait before trying next provider
                if attempt < len(fallback_chain) - 1:
                    await asyncio.sleep(self.config.retry_delay_seconds)
                continue
                
            except ModelNotFoundError as e:
                logger.warning(f"Model {model_name} not found in {provider_name}: {e}")
                last_error = e
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error with {provider_name}: {e}")
                self._update_health_status(ProviderType(provider_name), success=False, error=str(e))
                last_error = e
                continue
        
        # All providers failed
        raise LLMError(f"All providers failed. Last error: {last_error}", ProviderType.OPENAI)
    
    async def _find_provider_for_model(self, model: str) -> List[tuple]:
        """Find which providers support a given model"""
        providers_with_model = []
        
        for provider_type, provider in self._providers.items():
            if model in provider.supported_models:
                providers_with_model.append((provider_type.value, model))
        
        return providers_with_model if providers_with_model else [(ProviderType.OPENAI.value, "gpt-4o-mini")]
    
    async def _check_provider_health(self, provider_type: ProviderType) -> bool:
        """Check and update provider health"""
        health = self._health_status.get(provider_type)
        if not health:
            return False
        
        # Check if we need to update health status
        now = datetime.now()
        if (now - health.last_check).seconds > self.config.health_check_interval_minutes * 60:
            provider = self._providers.get(provider_type)
            if provider:
                try:
                    health.is_healthy = await provider.health_check()
                    health.last_check = now
                    if health.is_healthy:
                        health.consecutive_failures = 0
                except Exception as e:
                    health.is_healthy = False
                    health.last_error = str(e)
                    health.consecutive_failures += 1
        
        return health.is_healthy and health.consecutive_failures < self.config.max_consecutive_failures
    
    def _update_health_status(self, provider_type: ProviderType, success: bool, error: Optional[str] = None):
        """Update provider health status"""
        health = self._health_status.get(provider_type)
        if not health:
            return
        
        if success:
            health.is_healthy = True
            health.consecutive_failures = 0
            health.error_count = max(0, health.error_count - 1)  # Decrease error count on success
        else:
            health.is_healthy = False
            health.consecutive_failures += 1
            health.error_count += 1
            health.last_error = error
        
        health.last_check = datetime.now()
    
    def _track_cost(self, provider_type: ProviderType, model: str, cost: float):
        """Track costs by provider and model"""
        key = f"{provider_type.value}/{model}"
        self._cost_tracker[key] = self._cost_tracker.get(key, 0.0) + cost
    
    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost summary by provider/model"""
        return self._cost_tracker.copy()
    
    def get_health_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get health summary for all providers"""
        summary = {}
        for provider_type, health in self._health_status.items():
            summary[provider_type.value] = {
                "is_healthy": health.is_healthy,
                "last_check": health.last_check.isoformat(),
                "error_count": health.error_count,
                "consecutive_failures": health.consecutive_failures,
                "last_error": health.last_error
            }
        return summary


# Global factory instance
_factory_instance: Optional[LLMProviderFactory] = None


async def get_llm_provider(
    prompt: str,
    model: Optional[str] = None,
    provider: Optional[Union[str, ProviderType]] = None,
    role: ModelRole = ModelRole.DEFAULT,
    **kwargs
) -> LLMResponse:
    """Convenience function to get LLM response using global factory"""
    global _factory_instance
    
    if _factory_instance is None:
        _factory_instance = LLMProviderFactory()
        await _factory_instance.initialize()
    
    # Convert string provider to enum
    if isinstance(provider, str):
        provider = ProviderType(provider)
    
    return await _factory_instance.generate_response(
        prompt=prompt,
        model=model,
        provider=provider,
        role=role,
        **kwargs
    )


async def get_factory() -> LLMProviderFactory:
    """Get the global factory instance"""
    global _factory_instance
    
    if _factory_instance is None:
        _factory_instance = LLMProviderFactory()
        await _factory_instance.initialize()
    
    return _factory_instance