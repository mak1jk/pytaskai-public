"""
OpenAI API client wrapper for PyTaskAI infrastructure layer.

This module provides a clean wrapper around the OpenAI API,
following the Adapter pattern to isolate external API concerns
from the business logic.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import openai
from openai import AsyncOpenAI
from pydantic import BaseModel

from pytaskai.infrastructure.config.ai_config import AIConfig

# Configure logging
logger = logging.getLogger(__name__)


class OpenAIResponse(BaseModel):
    """Standardized response from OpenAI API."""

    content: str
    model: str
    tokens_used: int
    cost_estimate: float
    response_time: float
    success: bool = True
    error_message: Optional[str] = None


class OpenAIError(Exception):
    """Custom exception for OpenAI API errors."""

    def __init__(
        self, message: str, original_error: Optional[Exception] = None
    ) -> None:
        super().__init__(message)
        self.original_error = original_error


class OpenAIClient:
    """
    OpenAI API client wrapper with error handling and cost optimization.

    This class provides a clean interface to OpenAI API operations,
    implementing retry logic, error handling, and cost tracking.
    """

    def __init__(self, config: AIConfig) -> None:
        """
        Initialize OpenAI client with configuration.

        Args:
            config: AI configuration containing API keys and settings
        """
        self._config = config
        self._client = AsyncOpenAI(api_key=config.openai_api_key)
        self._total_cost = 0.0
        self._request_count = 0

        # Model pricing (per 1000 tokens) - as of December 2024
        self._pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
        }

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> OpenAIResponse:
        """
        Generate a completion using OpenAI API.

        Args:
            prompt: User prompt for completion
            system_prompt: Optional system prompt for context
            model: Model to use (defaults to config default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            OpenAIResponse with completion and metadata

        Raises:
            OpenAIError: If API call fails after retries
        """
        start_time = time.time()

        # Use configured model if not specified
        model = model or self._config.default_model
        max_tokens = max_tokens or self._config.max_tokens

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            logger.info(f"Making OpenAI API call with model {model}")

            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self._config.request_timeout,
            )

            # Extract response data
            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Calculate cost estimate
            cost = self._calculate_cost(model, tokens_used)
            self._total_cost += cost
            self._request_count += 1

            response_time = time.time() - start_time

            logger.info(
                f"OpenAI API call successful: {tokens_used} tokens, "
                f"${cost:.4f} cost, {response_time:.2f}s"
            )

            return OpenAIResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                cost_estimate=cost,
                response_time=response_time,
            )

        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded: {e}")
            raise OpenAIError(f"Rate limit exceeded: {e}", e)

        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            raise OpenAIError(f"Authentication failed: {e}", e)

        except openai.APITimeoutError as e:
            logger.warning(f"OpenAI API timeout: {e}")
            raise OpenAIError(f"API timeout: {e}", e)

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(f"API error: {e}", e)

        except Exception as e:
            logger.error(f"Unexpected error in OpenAI API call: {e}")
            raise OpenAIError(f"Unexpected error: {e}", e)

    async def generate_completion_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> OpenAIResponse:
        """
        Generate completion with exponential backoff retry logic.

        Args:
            prompt: User prompt for completion
            system_prompt: Optional system prompt
            model: Model to use
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments for generate_completion

        Returns:
            OpenAIResponse with completion and metadata

        Raises:
            OpenAIError: If all retry attempts fail
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return await self.generate_completion(
                    prompt=prompt, system_prompt=system_prompt, model=model, **kwargs
                )

            except OpenAIError as e:
                last_error = e

                # Don't retry on authentication errors
                if "authentication" in str(e).lower():
                    raise

                if attempt < max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"OpenAI API call failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await self._async_sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed for OpenAI API call")

        # If we get here, all retries failed
        raise last_error or OpenAIError("All retry attempts failed")

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for this client session.

        Returns:
            Dictionary with usage statistics
        """
        return {
            "total_requests": self._request_count,
            "total_cost": self._total_cost,
            "average_cost_per_request": (
                self._total_cost / self._request_count if self._request_count > 0 else 0
            ),
        }

    def _calculate_cost(self, model: str, tokens_used: int) -> float:
        """
        Calculate estimated cost for API call.

        Args:
            model: Model used for the call
            tokens_used: Total tokens used

        Returns:
            Estimated cost in USD
        """
        if model not in self._pricing:
            logger.warning(f"Unknown model {model}, using gpt-3.5-turbo pricing")
            model = "gpt-3.5-turbo"

        # Simplified cost calculation (assumes equal input/output tokens)
        pricing = self._pricing[model]
        avg_price = (pricing["input"] + pricing["output"]) / 2

        return (tokens_used / 1000) * avg_price

    async def _async_sleep(self, seconds: float) -> None:
        """
        Async sleep helper for retry logic.

        Args:
            seconds: Number of seconds to sleep
        """
        import asyncio

        await asyncio.sleep(seconds)

    async def health_check(self) -> bool:
        """
        Perform a health check on the OpenAI API.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = await self.generate_completion(
                prompt="Hello",
                max_tokens=5,
                temperature=0,
            )
            return response.success

        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False


def create_openai_client(config: AIConfig) -> OpenAIClient:
    """
    Factory function to create OpenAI client.

    Args:
        config: AI configuration

    Returns:
        Configured OpenAI client
    """
    return OpenAIClient(config)
