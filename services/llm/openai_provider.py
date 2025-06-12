"""
OpenAI LLM Provider Implementation

Provides OpenAI models with GPT-4, GPT-3.5-turbo support, cost tracking,
and intelligent error handling.
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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation using LiteLLM"""
    
    # OpenAI model configurations with costs per 1K tokens (as of 2024)
    MODEL_CONFIGS = {
        "gpt-4o": ModelConfig(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            max_tokens=4096,
            cost_per_1k_tokens=0.0075,  # $0.0075 per 1K tokens
            context_window=128000,
            role=ModelRole.TASK_GENERATION
        ),
        "gpt-4o-mini": ModelConfig(
            name="gpt-4o-mini", 
            provider=ProviderType.OPENAI,
            max_tokens=16384,
            cost_per_1k_tokens=0.00015,  # $0.00015 per 1K tokens
            context_window=128000,
            role=ModelRole.DEFAULT
        ),
        "gpt-4-turbo": ModelConfig(
            name="gpt-4-turbo",
            provider=ProviderType.OPENAI,
            max_tokens=4096,
            cost_per_1k_tokens=0.01,  # $0.01 per 1K tokens
            context_window=128000,
            role=ModelRole.TASK_GENERATION
        ),
        "gpt-3.5-turbo": ModelConfig(
            name="gpt-3.5-turbo",
            provider=ProviderType.OPENAI,
            max_tokens=4096,
            cost_per_1k_tokens=0.001,  # $0.001 per 1K tokens
            context_window=16385,
            role=ModelRole.DEFAULT
        )
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        super().__init__(api_key, **kwargs)
        
        # Configure LiteLLM for OpenAI
        if self.api_key:
            litellm.api_key = self.api_key
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    @property
    def supported_models(self) -> List[str]:
        return list(self.MODEL_CONFIGS.keys())
    
    async def _initialize_provider(self) -> None:
        """Initialize OpenAI provider"""
        if not self.api_key:
            raise LLMError("OpenAI API key not provided", ProviderType.OPENAI)
        
        # Set API key for litellm
        litellm.api_key = self.api_key
        logger.info("OpenAI provider initialized with API key")
    
    async def _perform_health_check(self) -> bool:
        """Perform health check by making a minimal API call"""
        try:
            response = await self.generate_response(
                prompt="Hello",
                model="gpt-4o-mini",
                max_tokens=10
            )
            return response.content is not None
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
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
        """Generate response using OpenAI model"""
        start_time = time.time()
        
        try:
            if model not in self.supported_models:
                raise ModelNotFoundError(
                    f"Model {model} not supported by OpenAI provider",
                    ProviderType.OPENAI,
                    model
                )
            
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Make API call using litellm
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: completion(
                    model=model,
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
                provider=ProviderType.OPENAI,
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
            
            # Handle specific OpenAI errors
            error_message = str(e).lower()
            
            if "rate limit" in error_message or "rate_limit" in error_message:
                raise RateLimitError(
                    f"OpenAI rate limit exceeded: {e}",
                    ProviderType.OPENAI,
                    model,
                    "rate_limit"
                )
            elif "quota" in error_message or "billing" in error_message:
                raise QuotaExceededError(
                    f"OpenAI quota exceeded: {e}",
                    ProviderType.OPENAI,
                    model,
                    "quota_exceeded"
                )
            elif "model" in error_message and "not found" in error_message:
                raise ModelNotFoundError(
                    f"OpenAI model not found: {e}",
                    ProviderType.OPENAI,
                    model,
                    "model_not_found"
                )
            else:
                raise LLMError(
                    f"OpenAI API error: {e}",
                    ProviderType.OPENAI,
                    model,
                    "api_error"
                )
    
    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Get configuration for OpenAI model"""
        return self.MODEL_CONFIGS.get(model)