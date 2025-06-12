"""
Perplexity LLM Provider Implementation

Provides Perplexity models with web search capabilities, cost tracking,
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


class PerplexityProvider(BaseLLMProvider):
    """Perplexity provider implementation using LiteLLM"""
    
    # Perplexity model configurations with costs per 1K tokens (as of 2024)
    MODEL_CONFIGS = {
        "llama-3.1-sonar-large-128k-online": ModelConfig(
            name="llama-3.1-sonar-large-128k-online",
            provider=ProviderType.PERPLEXITY,
            max_tokens=4096,
            cost_per_1k_tokens=0.002,  # $0.002 per 1K tokens
            context_window=128000,
            role=ModelRole.RESEARCH
        ),
        "llama-3.1-sonar-small-128k-online": ModelConfig(
            name="llama-3.1-sonar-small-128k-online",
            provider=ProviderType.PERPLEXITY,
            max_tokens=4096,
            cost_per_1k_tokens=0.0005,  # $0.0005 per 1K tokens
            context_window=128000,
            role=ModelRole.RESEARCH
        ),
        "llama-3.1-sonar-large-128k-chat": ModelConfig(
            name="llama-3.1-sonar-large-128k-chat",
            provider=ProviderType.PERPLEXITY,
            max_tokens=4096,
            cost_per_1k_tokens=0.002,  # $0.002 per 1K tokens
            context_window=128000,
            role=ModelRole.DEFAULT
        ),
        "llama-3.1-sonar-small-128k-chat": ModelConfig(
            name="llama-3.1-sonar-small-128k-chat",
            provider=ProviderType.PERPLEXITY,
            max_tokens=4096,
            cost_per_1k_tokens=0.0005,  # $0.0005 per 1K tokens
            context_window=128000,
            role=ModelRole.DEFAULT
        ),
        "llama-3.1-8b-instruct": ModelConfig(
            name="llama-3.1-8b-instruct",
            provider=ProviderType.PERPLEXITY,
            max_tokens=4096,
            cost_per_1k_tokens=0.0002,  # $0.0002 per 1K tokens
            context_window=128000,
            role=ModelRole.DEFAULT
        ),
        "llama-3.1-70b-instruct": ModelConfig(
            name="llama-3.1-70b-instruct",
            provider=ProviderType.PERPLEXITY,
            max_tokens=4096,
            cost_per_1k_tokens=0.001,  # $0.001 per 1K tokens
            context_window=128000,
            role=ModelRole.TASK_GENERATION
        )
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        if api_key is None:
            api_key = os.getenv("PERPLEXITY_API_KEY")
        super().__init__(api_key, **kwargs)
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.PERPLEXITY
    
    @property
    def supported_models(self) -> List[str]:
        return list(self.MODEL_CONFIGS.keys())
    
    def has_web_search(self, model: str) -> bool:
        """Check if model supports web search"""
        return "online" in model
    
    async def _initialize_provider(self) -> None:
        """Initialize Perplexity provider"""
        if not self.api_key:
            raise LLMError("Perplexity API key not provided", ProviderType.PERPLEXITY)
        
        # Set API key for litellm
        os.environ["PERPLEXITY_API_KEY"] = self.api_key
        logger.info("Perplexity provider initialized with API key")
    
    async def _perform_health_check(self) -> bool:
        """Perform health check by making a minimal API call"""
        try:
            response = await self.generate_response(
                prompt="Hello",
                model="llama-3.1-8b-instruct",
                max_tokens=10
            )
            return response.content is not None
        except Exception as e:
            logger.warning(f"Perplexity health check failed: {e}")
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
        """Generate response using Perplexity model"""
        start_time = time.time()
        
        try:
            if model not in self.supported_models:
                raise ModelNotFoundError(
                    f"Model {model} not supported by Perplexity provider",
                    ProviderType.PERPLEXITY,
                    model
                )
            
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Make API call using litellm with perplexity/ prefix
            full_model_name = f"perplexity/{model}"
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
            
            # Extract citations if available (Perplexity specific)
            citations = []
            if hasattr(response, 'citations'):
                citations = response.citations
            
            return LLMResponse(
                content=content,
                model=model,
                provider=ProviderType.PERPLEXITY,
                tokens_used=tokens_used,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": response.choices[0].finish_reason if response.choices else None,
                    "response_id": response.id if hasattr(response, 'id') else None,
                    "citations": citations,
                    "web_search": self.has_web_search(model)
                }
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Handle specific Perplexity errors
            error_message = str(e).lower()
            
            if "rate limit" in error_message or "rate_limit" in error_message:
                raise RateLimitError(
                    f"Perplexity rate limit exceeded: {e}",
                    ProviderType.PERPLEXITY,
                    model,
                    "rate_limit"
                )
            elif "quota" in error_message or "billing" in error_message or "credit" in error_message:
                raise QuotaExceededError(
                    f"Perplexity quota exceeded: {e}",
                    ProviderType.PERPLEXITY,
                    model,
                    "quota_exceeded"
                )
            elif "model" in error_message and ("not found" in error_message or "not available" in error_message):
                raise ModelNotFoundError(
                    f"Perplexity model not found: {e}",
                    ProviderType.PERPLEXITY,
                    model,
                    "model_not_found"
                )
            else:
                raise LLMError(
                    f"Perplexity API error: {e}",
                    ProviderType.PERPLEXITY,
                    model,
                    "api_error"
                )
    
    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Get configuration for Perplexity model"""
        return self.MODEL_CONFIGS.get(model)