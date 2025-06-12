"""
Anthropic LLM Provider Implementation

Provides Claude models with cost tracking and intelligent error handling.
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import litellm
from litellm import completion

from .base import (
    BaseLLMProvider, LLMResponse, LLMError, RateLimitError, 
    QuotaExceededError, ModelNotFoundError, ProviderType, ModelConfig, ModelRole
)

import logging
logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider implementation using LiteLLM"""
    
    # Anthropic model configurations with costs per 1K tokens (as of 2024)
    MODEL_CONFIGS = {
        "claude-3-5-sonnet-20241022": ModelConfig(
            name="claude-3-5-sonnet-20241022",
            provider=ProviderType.ANTHROPIC,
            max_tokens=8192,
            cost_per_1k_tokens=0.003,  # $0.003 per 1K tokens
            context_window=200000,
            role=ModelRole.TASK_GENERATION
        ),
        "claude-3-5-haiku-20241022": ModelConfig(
            name="claude-3-5-haiku-20241022",
            provider=ProviderType.ANTHROPIC,
            max_tokens=8192,
            cost_per_1k_tokens=0.0008,  # $0.0008 per 1K tokens  
            context_window=200000,
            role=ModelRole.DEFAULT
        ),
        "claude-3-opus-20240229": ModelConfig(
            name="claude-3-opus-20240229",
            provider=ProviderType.ANTHROPIC,
            max_tokens=4096,
            cost_per_1k_tokens=0.015,  # $0.015 per 1K tokens
            context_window=200000,
            role=ModelRole.BEST_PRACTICES
        ),
        "claude-3-sonnet-20240229": ModelConfig(
            name="claude-3-sonnet-20240229",
            provider=ProviderType.ANTHROPIC,
            max_tokens=4096,
            cost_per_1k_tokens=0.003,  # $0.003 per 1K tokens
            context_window=200000,
            role=ModelRole.TASK_GENERATION
        ),
        "claude-3-haiku-20240307": ModelConfig(
            name="claude-3-haiku-20240307",
            provider=ProviderType.ANTHROPIC,
            max_tokens=4096,
            cost_per_1k_tokens=0.00025,  # $0.00025 per 1K tokens
            context_window=200000,
            role=ModelRole.DEFAULT
        )
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        super().__init__(api_key, **kwargs)
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC
    
    @property
    def supported_models(self) -> List[str]:
        return list(self.MODEL_CONFIGS.keys())
    
    async def _initialize_provider(self) -> None:
        """Initialize Anthropic provider"""
        if not self.api_key:
            raise LLMError("Anthropic API key not provided", ProviderType.ANTHROPIC)
        
        # Set API key for litellm
        os.environ["ANTHROPIC_API_KEY"] = self.api_key
        logger.info("Anthropic provider initialized with API key")
    
    async def _perform_health_check(self) -> bool:
        """Perform health check by making a minimal API call"""
        try:
            response = await self.generate_response(
                prompt="Hello",
                model="claude-3-haiku-20240307",
                max_tokens=10
            )
            return response.content is not None
        except Exception as e:
            logger.warning(f"Anthropic health check failed: {e}")
            return False
    
    async def generate_response(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Anthropic model"""
        start_time = time.time()
        
        try:
            if model not in self.supported_models:
                raise ModelNotFoundError(
                    f"Model {model} not supported by Anthropic provider",
                    ProviderType.ANTHROPIC,
                    model
                )
            
            # Prepare messages for Anthropic format
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Make API call using litellm with anthropic/ prefix
            full_model_name = f"anthropic/{model}"
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: completion(
                    model=full_model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            )
            
            # Calculate metrics
            latency_ms = int((time.time() - start_time) * 1000)
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Calculate cost
            model_config = self.get_model_config(model)
            cost = (tokens_used / 1000) * model_config.cost_per_1k_tokens if model_config else 0.0
            
            # Extract content
            content = response.choices[0].message.content if response.choices else ""
            
            return LLMResponse(
                content=content,
                model=model,
                provider=ProviderType.ANTHROPIC,
                tokens_used=tokens_used,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": response.choices[0].finish_reason if response.choices else None,
                    "response_id": response.id if hasattr(response, 'id') else None
                }
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Handle specific Anthropic errors
            error_message = str(e).lower()
            
            if "rate limit" in error_message or "rate_limit" in error_message:
                raise RateLimitError(
                    f"Anthropic rate limit exceeded: {e}",
                    ProviderType.ANTHROPIC,
                    model,
                    "rate_limit"
                )
            elif "quota" in error_message or "billing" in error_message or "credit" in error_message:
                raise QuotaExceededError(
                    f"Anthropic quota exceeded: {e}",
                    ProviderType.ANTHROPIC,
                    model,
                    "quota_exceeded"
                )
            elif "model" in error_message and ("not found" in error_message or "not available" in error_message):
                raise ModelNotFoundError(
                    f"Anthropic model not found: {e}",
                    ProviderType.ANTHROPIC,
                    model,
                    "model_not_found"
                )
            else:
                raise LLMError(
                    f"Anthropic API error: {e}",
                    ProviderType.ANTHROPIC,
                    model,
                    "api_error"
                )
    
    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Get configuration for Anthropic model"""
        return self.MODEL_CONFIGS.get(model)