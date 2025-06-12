"""
PyTaskAI - AI Service Module

Advanced AI service using LiteLLM for multi-provider LLM integration with sophisticated
agentic workflows, research capabilities, and intelligent task generation.
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .cache_manager import get_cache_manager, CacheType, RateLimitStatus
from .usage_tracker import get_usage_tracker, OperationType, CallStatus
from .prompts import RESEARCH_SYSTEM_PROMPT, RESEARCH_LTS_VERSIONS_PROMPT


import litellm

# Configure logging
logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported AI model providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GOOGLE = "google"
    XAI = "xai"


class ModelRole(str, Enum):
    """AI model roles for different operations"""

    RESEARCH = "research"              # For LTS research and web searches
    TASK_MANAGEMENT = "task_management"  # For task generation and management
    DEFAULT = "default"                # Default/fallback model
    BEST_PRACTICES = "best_practices"  # For coding best practices analysis


@dataclass
class ModelConfig:
    """Configuration for AI models"""

    name: str
    provider: ModelProvider
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: float = 30.0
    cost_per_1k_tokens: float = 0.001
    supports_json: bool = True
    supports_streaming: bool = True


@dataclass
class AIUsageMetrics:
    """Metrics for AI usage tracking"""

    total_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_latency: float = 0.0
    success_rate: float = 100.0
    by_model: Dict[str, Dict[str, Union[int, float]]] = field(default_factory=dict)
    by_operation: Dict[str, Dict[str, Union[int, float]]] = field(default_factory=dict)


@dataclass
class ResearchResults:
    """Results from AI research operations"""

    lts_versions: Dict[str, str] = field(default_factory=dict)
    best_practices: List[str] = field(default_factory=list)
    research_summary: str = ""
    confidence_level: str = "Medium"
    sources_consulted: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class CacheCompatibilityWrapper:
    """Wrapper to make CacheManager compatible with dict-like access for tests"""

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager

    def __len__(self):
        """Return cache size for compatibility"""
        metrics = self.cache_manager.get_metrics()
        return metrics.get("cache_stats", {}).get("total_entries", 0)

    def clear(self):
        """Clear cache for compatibility"""
        return self.cache_manager.clear_cache()

    def __getattr__(self, name):
        """Delegate to cache manager"""
        return getattr(self.cache_manager, name)


class AIService:
    """
    Advanced AI service with multi-provider support and agentic workflows.

    Supports sophisticated research capabilities, intelligent task generation,
    and seamless integration with multiple LLM providers through LiteLLM.
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize AIService with configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.project_root = project_root
        self.config = config or {}
        self.usage_metrics = AIUsageMetrics()

        # Initialize cache manager and usage tracker
        self.cache_manager = get_cache_manager(project_root)
        self.usage_tracker = get_usage_tracker(project_root)

        # Add compatibility aliases for tests
        self.cache = CacheCompatibilityWrapper(
            self.cache_manager
        )  # Alias for backward compatibility

        # Configure models
        self.models = self._setup_model_configurations()

        # Setup rate limits for compatibility with tests
        self.rate_limits = {
            "openai": {"calls_per_minute": 60, "calls_made": 0, "window_start": 0},
            "anthropic": {"calls_per_minute": 30, "calls_made": 0, "window_start": 0},
            "perplexity": {"calls_per_minute": 20, "calls_made": 0, "window_start": 0},
            "google": {"calls_per_minute": 30, "calls_made": 0, "window_start": 0},
            "xai": {"calls_per_minute": 30, "calls_made": 0, "window_start": 0},
        }

        logger.info("AIService initialized with multi-provider support")

    def _estimate_cost(
        self, input_length: int, output_length: int, model_name: str
    ) -> float:
        """Estimate cost based on token counts."""
        # Rough estimation: 4 characters per token
        input_tokens = input_length // 4
        output_tokens = output_length // 4
        total_tokens = input_tokens + output_tokens

        # Use model cost from config
        model_config = self._get_model_config(model_name)
        cost_per_1k = model_config.cost_per_1k_tokens
        return (total_tokens / 1000) * cost_per_1k

    def _setup_model_configurations(self) -> Dict[str, ModelConfig]:
        """Setup model configurations from environment variables."""
        import os

        # Default model configurations
        defaults = {
            "default_generation": "gpt-4o-mini",
            "research_generation": "anthropic/claude-3-haiku-20240307",
            "lts_search": "perplexity/llama-3-sonar-large-32k-online",
            "best_practices_search": "perplexity/llama-3-sonar-large-32k-online",
            "fallback": "gpt-3.5-turbo",
        }

        # Read model configurations from environment variables
        env_models = {
            "default_generation": os.getenv(
                "PYTASKAI_DEFAULT_MODEL",
                defaults["default_generation"]
            ),
            "research_generation": os.getenv(
                "PYTASKAI_RESEARCH_MODEL",
                defaults["research_generation"]
            ),
            "lts_search": os.getenv("PYTASKAI_LTS_MODEL", defaults["lts_search"]),
            "best_practices_search": os.getenv(
                "PYTASKAI_BEST_PRACTICES_MODEL", defaults["best_practices_search"]
            ),
            "fallback": os.getenv("PYTASKAI_FALLBACK_MODEL", defaults["fallback"]),
        }

        # Temperature and token settings from environment
        default_temp = float(os.getenv("PYTASKAI_DEFAULT_TEMPERATURE", "0.7"))
        research_temp = float(os.getenv("PYTASKAI_RESEARCH_TEMPERATURE", "0.3"))
        search_temp = float(os.getenv("PYTASKAI_SEARCH_TEMPERATURE", "0.1"))
        max_tokens = int(os.getenv("PYTASKAI_MAX_TOKENS", "4096"))

        models = {}

        # Configure each model
        for role, model_name in env_models.items():
            provider = self._detect_provider(model_name)

            # Set temperature based on role
            if role == "default_generation":
                temperature = default_temp
            elif role == "research_generation":
                temperature = research_temp
            else:
                temperature = search_temp

            models[role] = ModelConfig(
                name=model_name,
                provider=provider,
                max_tokens=max_tokens,
                temperature=temperature,
                cost_per_1k_tokens=self._get_model_cost(model_name),
                supports_json=True,
            )

        logger.info("Configured AI models from environment:")
        for role, config in models.items():
            logger.info(f"  {role}: {config.name} ({config.provider.value})")

        return models

    def _detect_provider(self, model_name: str) -> ModelProvider:
        """Detect provider from model name."""
        model_lower = model_name.lower()

        if model_lower.startswith("anthropic/") or "claude" in model_lower:
            return ModelProvider.ANTHROPIC
        elif model_lower.startswith("perplexity/") or "sonar" in model_lower:
            return ModelProvider.PERPLEXITY
        elif model_lower.startswith("google/") or "gemini" in model_lower:
            return ModelProvider.GOOGLE
        elif model_lower.startswith("xai/") or "grok" in model_lower:
            return ModelProvider.XAI
        else:
            return ModelProvider.OPENAI  # Default to OpenAI

    def _get_model_cost(self, model_name: str) -> float:
        """Get cost per 1k tokens for model (rough estimates)."""
        model_lower = model_name.lower()

        # Cost estimates (input + output average per 1k tokens)
        if "gpt-4o" in model_lower:
            return 0.0075 if "mini" not in model_lower else 0.000150
        elif "gpt-4" in model_lower:
            return 0.015
        elif "gpt-3.5" in model_lower:
            return 0.001
        elif "claude-3-opus" in model_lower:
            return 0.0375
        elif "claude-3-sonnet" in model_lower:
            return 0.003
        elif "claude-3-haiku" in model_lower:
            return 0.000250
        elif "perplexity" in model_lower or "sonar" in model_lower:
            return 0.001
        elif "gemini" in model_lower:
            return 0.0005
        else:
            return 0.001  # Default estimate

    async def _research_llm_call(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        operation_type: OperationType = OperationType.GENERAL,
        operation_context: str = "",
        tool_name: Optional[str] = None,
        error_message: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make an async LLM call using LiteLLM with comprehensive tracking.

        Args:
            model_name: Name of the model to use
            system_prompt: System prompt for the AI
            user_prompt: User prompt for the AI
            operation_type: Type of operation for tracking
            operation_context: Context description for tracking
            tool_name: MCP tool name if applicable
            error_message: Error message if this is a retry after error
            **kwargs: Additional arguments for the LLM call

        Returns:
            Parsed JSON response from the AI model
        """
        start_time = time.time()
        model_config, provider = self._get_model_config(model_name)

        try:
            # Check rate limits
            await self.cache_manager.wait_for_rate_limit(provider, model_name)
            self.cache_manager.record_api_call(provider, model_name)

            # Cache is now handled at higher level methods

            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Remove custom parameters that shouldn't be passed to LiteLLM
            force_json = kwargs.pop("force_json", True)

            # Remove all known non-LiteLLM parameters
            non_litellm_params = [
                "mentioned_technologies",
                "topic_for_best_practices",
                "research_query",
                "prompt",
                "operation_type",
                "operation_context",
                "tool_name",
                "error_message",
            ]
            for param in non_litellm_params:
                kwargs.pop(param, None)

            # Debug log remaining kwargs
            if kwargs:
                logger.debug(f"Remaining kwargs for LiteLLM: {list(kwargs.keys())}")

            # Prepare LiteLLM arguments - only use known safe parameters
            llm_args = {
                "model": model_config.name,
                "messages": messages,
                "max_tokens": model_config.max_tokens,
                "temperature": model_config.temperature,
                "timeout": model_config.timeout,
            }

            # Only add kwargs that are known to be safe for LiteLLM
            safe_kwargs = [
                "stream",
                "stop",
                "top_p",
                "frequency_penalty",
                "presence_penalty",
            ]
            for key, value in kwargs.items():
                if key in safe_kwargs:
                    llm_args[key] = value

            # Add JSON format if supported
            if model_config.supports_json and force_json:
                llm_args["response_format"] = {"type": "json_object"}

            logger.info(f"Making AI call to {model_config.name}")
            logger.debug(f"LiteLLM arguments: {llm_args}")

            # Make the call
            response = await litellm.acompletion(**llm_args)

            # Extract content
            content = response.choices[0].message.content

            # Parse JSON if possible
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to parse JSON from {model_config.name}"
                )
                parsed_content = {"raw_content": content, "parsing_error": True}

            # Calculate metrics
            latency = time.time() - start_time
            usage = response.usage
            cost = self._estimate_cost(
                len(user_prompt),
                len(str(response.choices[0].message.content)),
                model_name,
            )

            # Update old metrics
            self._update_metrics(model_name, usage.total_tokens, cost, latency, True)

            # Record detailed usage tracking
            self.usage_tracker.record_usage(
                provider=provider,
                model=model_config.name,
                operation_type=operation_type,
                operation_context=operation_context or f"{model_name} call",
                status=CallStatus.SUCCESS,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                estimated_cost=cost,
                duration_ms=int(latency * 1000),
                cache_hit=False,  # Cache hits are handled at higher level
                tool_name=tool_name,
                cost_per_1k_input=model_config.cost_per_1k_tokens,
                cost_per_1k_output=model_config.cost_per_1k_tokens,
            )

            logger.info(
                f"AI call successful: {usage.total_tokens} tokens, "
                f"${cost:.4f}, {latency:.2f}s"
            )

            return parsed_content

        except litellm.RateLimitError as e:
            latency = time.time() - start_time
            self._update_metrics(model_name, 0, 0, latency, False)

            # Record failed usage tracking
            if provider and model_config:
                self.usage_tracker.record_usage(
                    provider=provider,
                    model=model_config.name,
                    operation_type=operation_type,
                    operation_context=operation_context or f"{model_name} call",
                    status=CallStatus.FAILED,
                    duration_ms=int(latency * 1000),
                    tool_name=tool_name,
                    error_message=str(e),
                )

            logger.error(f"AI call failed for {model_name}: {str(e)}")

            # Try fallback model if available
            if model_name != "fallback":
                logger.info("Attempting fallback model")
                return await self._research_llm_call(
                    "fallback",
                    system_prompt,
                    user_prompt,
                    operation_type=operation_type,
                    operation_context=operation_context,
                    tool_name=tool_name,
                    **kwargs,
                )

            raise AICallError(f"AI call failed: {str(e)}")

        except litellm.APIError as e:
            latency = time.time() - start_time
            self._update_metrics(model_name, 0, 0, latency, False)

            # Record failed usage tracking
            if provider and model_config:
                self.usage_tracker.record_usage(
                    provider=provider,
                    model=model_config.name,
                    operation_type=operation_type,
                    operation_context=operation_context or f"{model_name} call",
                    status=CallStatus.FAILED,
                    duration_ms=int(latency * 1000),
                    tool_name=tool_name,
                    error_message=str(e),
                )

            logger.error(f"AI call failed for {model_name}: {str(e)}")

            # Try fallback model if available
            if model_name != "fallback":
                logger.info("Attempting fallback model")
                return await self._research_llm_call(
                    "fallback",
                    system_prompt,
                    user_prompt,
                    operation_type=operation_type,
                    operation_context=operation_context,
                    tool_name=tool_name,
                    **kwargs,
                )

            raise AICallError(f"AI call failed: {str(e)}")

        except Exception as e:
            latency = time.time() - start_time
            self._update_metrics(model_name, 0, 0, latency, False)

            # Record failed usage tracking
            if provider and model_config:
                self.usage_tracker.record_usage(
                    provider=provider,
                    model=model_config.name,
                    operation_type=operation_type,
                    operation_context=operation_context or f"{model_name} call",
                    status=CallStatus.FAILED,
                    duration_ms=int(latency * 1000),
                    tool_name=tool_name,
                    error_message=str(e),
                )

            logger.error(f"AI call failed for {model_name}: {str(e)}")

            # Try fallback model if available
            if model_name != "fallback":
                logger.info("Attempting fallback model")
                return await self._research_llm_call(
                    "fallback",
                    system_prompt,
                    user_prompt,
                    operation_type=operation_type,
                    operation_context=operation_context,
                    tool_name=tool_name,
                    **kwargs,
                )

            raise AICallError(f"AI call failed: {str(e)}")

    def _get_model_config(self, model_name: str) -> Tuple[ModelConfig, ModelProvider]:
        """Return the model configuration and its provider (simplified)."""
        
        # If model_name is a role key, get the actual model name
        if model_name in self.models:
            actual_model_name = self.models[model_name].name
        else:
            actual_model_name = model_name

        provider = self._detect_provider(actual_model_name)
        model_lower = actual_model_name.lower()

        # Determine token limit
        if provider == ModelProvider.GOOGLE:
            max_tokens = 8192
        elif provider == ModelProvider.OPENAI and "gpt-4o-mini" in model_lower:
            max_tokens = 16384
        else:
            # Anthropic, Perplexity, XAI, other OpenAI models
            max_tokens = 4096

        temperature = 0.7  # Default temperature, overridable via env if needed

        return (
            ModelConfig(
                name=actual_model_name,
                provider=provider,
                max_tokens=max_tokens,
                temperature=temperature,
                cost_per_1k_tokens=self._get_model_cost(actual_model_name),
                supports_json=True,
            ),
            provider,
        )

    async def _get_lts_versions(self, technologies: List[str]) -> Dict[str, str]:
        """
        Get LTS versions for technologies with caching.

        Args:
            technologies: List of technology names to research

        Returns:
            Dict mapping technology names to their LTS versions
        """
        try:
            tech_key = ",".join(sorted(technologies))
            cached = self._get_cached_versions(tech_key, technologies)
            if cached is not None:
                return cached

            user_prompt, result = await self._fetch_lts_data(technologies)
            lts_versions = self._extract_versions(result)
            self._cache_results(tech_key, user_prompt, result, lts_versions)

            return lts_versions
        except Exception as e:
            logger.error(f"Failed to get LTS versions: {str(e)}")
            return {}

    def _get_cached_versions(
        self, tech_key: str, technologies: List[str]
    ) -> Optional[Dict[str, str]]:
        """Check cache for existing LTS versions."""
        cached = self.cache_manager.get(
            prompt=f"lts_versions:{tech_key}",
            model="",
            cache_type=CacheType.LTS_RESEARCH,
        )
        if cached is not None:
            logger.info(
                f"Using cached LTS versions for {len(technologies)} technologies"
            )
            return cached
        return None

    async def _fetch_lts_data(self, technologies: List[str]) -> Tuple[str, Any]:
        """Fetch LTS data from LLM."""
        user_prompt = RESEARCH_LTS_VERSIONS_PROMPT.format(
            technologies=", ".join(technologies)
        )

        result = await self._research_llm_call(
            model_name=self.models["research_generation"].name,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            operation_type=OperationType.LTS_RESEARCH,
            operation_context=(
                f"LTS research for {len(technologies)} technologies: "
                f"{', '.join(technologies[:3])}"
                f"{'...' if len(technologies) > 3 else ''}"
            ),
        )

        return user_prompt, result

    def _extract_versions(self, result: Any) -> Dict[str, str]:
        """Extract LTS versions from API response."""
        lts_versions = {}
        if "technologies" in result:
            for tech_info in result["technologies"]:
                tech_name = tech_info.get("name", "")
                lts_version = tech_info.get("current_lts_version", "")
                if tech_name and lts_version:
                    lts_versions[tech_name] = lts_version
        return lts_versions

    def _cache_results(
        self, tech_key: str, user_prompt: str, result: Any, lts_versions: Dict[str, str]
    ):
        """Cache results and log savings."""
        model_name = self.models["research_generation"].name
        cost_estimate = self._estimate_cost(
            len(user_prompt), len(str(result)), model_name
        )
        self.cache_manager.set(
            prompt=f"lts_versions:{tech_key}",
            model=model_name,
            cache_type=CacheType.LTS_RESEARCH,
            value=lts_versions,
            cost_saved=cost_estimate,
        )
        logger.info(
            f"Found and cached LTS versions for {len(lts_versions)} technologies"
        )

    async def _get_best_practices(self, topic: str, context: str = "") -> List[str]:
        """
        Research current best practices for a specific topic with caching.

        Args:
            topic: Topic to research best practices for
            context: Additional context about the project or requirements

        Returns:
            List of best practice recommendations
        """
        try:
            # Create cache key from topic and context
            cache_key = f"best_practices:{topic}:{context[:100]}"
            model_name = self.models["best_practices_search"].name

            # Check cache first
            cached_result = self.cache_manager.get(
                prompt=cache_key, model=model_name, cache_type=CacheType.BEST_PRACTICES
            )

            if cached_result is not None:
                logger.info(f"Using cached best practices for topic: {topic}")

                # Record cache hit
                self.usage_tracker.record_usage(
                    provider=self.models["best_practices_search"].provider.value,
                    model=model_name,
                    operation_type=OperationType.BEST_PRACTICES,
                    operation_context=f"Best practices for {topic} (cached)",
                    status=CallStatus.CACHED,
                    cache_hit=True,
                )

                return cached_result

            # Import prompt functions
            from .prompts.best_practices_prompt import (
                get_best_practices_system_prompt,
                get_best_practices_user_prompt,
            )

            # Generate prompts
            system_prompt = get_best_practices_system_prompt()
            user_prompt = get_best_practices_user_prompt(
                topic=topic, additional_context=context
            )

            # Check rate limiting
            provider = self.models["best_practices_search"].provider.value
            status = self.cache_manager.check_rate_limit(provider, model_name)

            if status == RateLimitStatus.RATE_LIMITED:
                # Get user-friendly message with configuration instructions
                rate_limit_msg = self.cache_manager.get_rate_limit_message(
                    provider, model_name
                )
                if rate_limit_msg:
                    logger.error(rate_limit_msg)
                logger.warning(
                    f"Rate limited for {provider}, using fallback or cached data"
                )
                return []

            # Wait if approaching limits
            await self.cache_manager.wait_for_rate_limit(provider, model_name)

            # Record API call
            self.cache_manager.record_api_call(provider, model_name)

            # Make research call
            result = await self._research_llm_call(
                "best_practices_search",
                system_prompt,
                user_prompt,
                operation_type=OperationType.BEST_PRACTICES,
                operation_context=f"Best practices research for: {topic}",
            )

            # Extract best practices from result
            best_practices = []
            if "best_practices" in result:
                for practice_info in result["best_practices"]:
                    practice = practice_info.get("practice", "")
                    if practice:
                        # Include implementation details if available
                        implementation = practice_info.get("implementation", "")
                        if implementation:
                            best_practices.append(f"{practice}: {implementation}")
                        else:
                            best_practices.append(practice)

            # Also include quick wins if available
            if "quick_wins" in result:
                for quick_win in result["quick_wins"]:
                    best_practices.append(f"Quick Win: {quick_win}")

            # Cache the result
            cost_estimate = self._estimate_cost(
                len(user_prompt), len(str(result)), model_name
            )
            self.cache_manager.set(
                prompt=cache_key,
                model=model_name,
                cache_type=CacheType.BEST_PRACTICES,
                value=best_practices,
                cost_saved=cost_estimate,
            )

            logger.info(
                f"Found and cached {len(best_practices)} best practices for {topic}"
            )
            return best_practices

        except Exception as e:
            logger.error(f"Failed to get best practices for {topic}: {str(e)}")
            return []

    async def generate_task_with_ai(
        self,
        user_prompt: str,
        use_research: bool = False,
        use_lts_deps: bool = True,
        priority: str = "medium",
        dependencies: Optional[List[int]] = None,
        project_context: Optional[str] = None,
        mentioned_technologies: Optional[List[str]] = None,
        topic_for_best_practices: Optional[str] = None,
        research_query: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a task using AI with sophisticated agentic workflow.

        Args:
            user_prompt: User's description of what they want to accomplish
            use_research: Whether to perform research before task generation
            use_lts_deps: Whether to prefer LTS versions of dependencies
            priority: Priority level for the task
            dependencies: List of task IDs this task depends on
            project_context: Additional project context
            **kwargs: Additional arguments

        Returns:
            Generated task data with research insights
        """
        try:
            logger.info(
                f"Generating task with research={use_research}, lts_deps={use_lts_deps}"
            )

            research_findings = ""

            # Phase 1: Research (if enabled)
            if use_research:
                logger.info("Starting research phase")

                # Extract technologies from user prompt
                technologies = self._extract_technologies(user_prompt)

                # Determine research topic
                research_topic = self._extract_topic(user_prompt)

                # Perform research in parallel
                research_tasks = []

                if technologies and use_lts_deps:
                    research_tasks.append(self._get_lts_versions(technologies))

                if research_topic:
                    research_tasks.append(
                        self._get_best_practices(research_topic, project_context or "")
                    )

                # Execute research tasks in parallel
                if research_tasks:
                    research_results = await asyncio.gather(
                        *research_tasks, return_exceptions=True
                    )

                    # Compile research findings
                    findings_parts = []

                    # Process LTS results
                    if len(research_results) > 0 and isinstance(
                        research_results[0], dict
                    ):
                        lts_results = research_results[0]
                        if lts_results:
                            findings_parts.append("**LTS Version Recommendations:**")
                            for tech, version in lts_results.items():
                                findings_parts.append(f"- {tech}: {version} (LTS)")

                    # Process best practices results
                    if len(research_results) > 1 and isinstance(
                        research_results[1], list
                    ):
                        bp_results = research_results[1]
                        if bp_results:
                            findings_parts.append("\\n**Best Practices:**")
                            for practice in bp_results[:5]:  # Limit to top 5
                                findings_parts.append(f"- {practice}")

                    research_findings = "\\n".join(findings_parts)
                    logger.info(
                        f"Research completed with {len(findings_parts)} findings"
                    )

            # Phase 2: Task Generation – silence unused-parameter lints
            _ = (
                mentioned_technologies,
                topic_for_best_practices,
                research_query,
                kwargs,
            )

            # Continue with Task Generation
            logger.info("Starting task generation phase")

            # Import prompt functions
            from .prompts.add_task_prompt import create_add_task_prompt

            # Generate comprehensive prompt with research findings
            task_prompt = create_add_task_prompt(
                user_prompt=user_prompt,
                dependencies=dependencies or [],
                priority=priority,
                use_research=use_research,
                use_lts_deps=use_lts_deps,
                research_findings=research_findings if research_findings else None,
                project_context=project_context,
            )

            # Use research model if research was performed, otherwise use default
            model_name = "research_generation" if use_research else "default_generation"

            # Generate task
            result = await self._research_llm_call(
                model_name,
                "You are an expert project manager and software architect.",
                task_prompt,
            )

            # Enhance result with metadata
            result["generated_with_research"] = use_research
            result["research_findings_used"] = bool(research_findings)
            result["lts_preference"] = use_lts_deps
            result["generation_timestamp"] = datetime.now().isoformat()
            result["model_used"] = self.models[model_name].name

            if research_findings:
                result["research_summary"] = research_findings

            logger.info("Task generation completed successfully")
            return result

        except TaskGenerationError:
            # Already specific, re-raise
            raise
        except Exception as e:
            logger.error(f"Task generation failed: {str(e)}")
            raise TaskGenerationError(f"Failed to generate task: {str(e)}")

    async def _generate_subtasks(
        self,
        parent_task_id: int,
        title: str,
        description: str,
        task_type: str,
        priority: str,
        target_count: int = 5,
        additional_context: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Generate subtasks for a parent task using AI.

        Args:
            parent_task_id: ID of the parent task
            title: Title of the parent task
            description: Description of the parent task
            task_type: Type of task (task, bug, feature, etc)
            priority: Priority level (high, medium, low)
            target_count: Target number of subtasks to generate
            additional_context: Additional context for subtask generation

        Returns:
            List of generated subtasks
        """
        try:
            system_prompt, user_prompt = self._build_subtask_prompts(
                title,
                description,
                task_type,
                priority,
                target_count,
                additional_context,
            )
            result = await self._make_subtask_request(system_prompt, user_prompt)
            return self._parse_subtask_response(result, parent_task_id)
        except Exception as e:
            logger.error(f"Failed to generate subtasks: {str(e)}")
            return []

    def _build_subtask_prompts(
        self,
        title: str,
        description: str,
        task_type: str,
        priority: str,
        target_count: int,
        additional_context: str,
    ) -> Tuple[str, str]:
        """Build system and user prompts for subtask generation."""
        from .prompts.task_management_prompts import (
            get_subtask_generation_system_prompt,
            get_subtask_generation_user_prompt,
        )

        system_prompt = get_subtask_generation_system_prompt()
        user_prompt = get_subtask_generation_user_prompt(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            target_count=target_count,
            additional_context=additional_context,
        )
        return system_prompt, user_prompt

    async def _make_subtask_request(self, system_prompt: str, user_prompt: str) -> Dict:
        """Make the API request for subtask generation."""
        return await self._research_llm_call(
            model_name=self.models["default_generation"].name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            operation_type=OperationType.TASK_GENERATION,
            operation_context="Generating subtasks",
        )

    def _parse_subtask_response(
        self, result: Dict, parent_task_id: int
    ) -> List[Dict[str, Any]]:
        """Parse the API response to extract subtasks."""
        subtasks = []
        if "subtasks" in result and isinstance(result["subtasks"], list):
            for i, subtask in enumerate(result["subtasks"], 1):
                try:
                    subtask_id = f"{parent_task_id}.{i}"
                    title = subtask.get("title", f"Subtask {subtask_id}")
                    description = subtask.get("description", "")
                    status = "pending"
                    priority = subtask.get("priority", "medium")
                    test_strategy = subtask.get("test_strategy", "")
                    details = subtask.get("details", {})

                    subtasks.append(
                        {
                            "id": subtask_id,
                            "title": title,
                            "description": description,
                            "status": status,
                            "priority": priority,
                            "test_strategy": test_strategy,
                            "details": details,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to process subtask {i}: {str(e)}")
                    continue
        else:
            logger.warning("No valid subtasks found in response")

        logger.info(f"Generated {len(subtasks)} subtasks")
        return subtasks

    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technology names from text."""
        # Common technology patterns
        tech_patterns = [
            r"\b(Python|Node\.js|JavaScript|TypeScript|Java|Go|Rust|PHP|Ruby)\b",
            r"\b(React|Vue|Angular|Svelte|Next\.js|Nuxt\.js)\b",
            r"\b(FastAPI|Express|Django|Flask|Spring|Laravel|Rails)\b",
            r"\b(PostgreSQL|MySQL|MongoDB|Redis|SQLite|Elasticsearch)\b",
            r"\b(Docker|Kubernetes|AWS|GCP|Azure|Terraform)\b",
            r"\b(Git|GitHub|GitLab|Jenkins|CircleCI|Travis)\b",
        ]

        technologies = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            technologies.extend(matches)

        return list(set(technologies))  # Remove duplicates

    def _extract_topic(self, text: str) -> str:
        """Extract main topic from text for best practices research."""
        # Topic keywords mapping
        topic_keywords = {
            "security": [
                "security",
                "authentication",
                "authorization",
                "encryption",
                "oauth",
                "jwt",
            ],
            "performance": [
                "performance",
                "optimization",
                "scaling",
                "caching",
                "speed",
            ],
            "testing": ["testing", "test", "qa", "quality", "coverage"],
            "api": ["api", "rest", "graphql", "endpoint", "service"],
            "database": ["database", "db", "sql", "migration", "schema"],
            "deployment": ["deployment", "deploy", "ci/cd", "docker", "kubernetes"],
            "architecture": [
                "architecture",
                "design",
                "pattern",
                "microservice",
                "monolith",
            ],
        }

        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic

        return "general development"

    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache and rate limiting metrics from cache manager."""
        return self.cache_manager.get_metrics()

    def get_usage_stats(self, **kwargs) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""
        return self.usage_tracker.get_stats(**kwargs)

    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status and recommendations."""
        return self.usage_tracker.check_budget_status()

    def export_usage_data(self, filename: Optional[str] = None) -> str:
        """Export usage data to CSV file."""
        return self.usage_tracker.export_to_csv(filename)

    def _generate_cache_key(
        self, model_name: str, system_prompt: str, user_prompt: str
    ) -> str:
        """Generate cache key for request."""
        import hashlib

        content = f"{model_name}:{system_prompt}:{user_prompt}"
        return hashlib.md5(content.encode()).hexdigest()

    # Cache methods moved to CacheManager

    def _calculate_cost(self, total_tokens: int, cost_per_1k: float) -> float:
        """Calculate cost for token usage."""
        return (total_tokens / 1000) * cost_per_1k

    def _update_metrics(
        self, model_name: str, tokens: int, cost: float, latency: float, success: bool
    ):
        """Update usage metrics."""
        self.usage_metrics.total_calls += 1
        self.usage_metrics.total_tokens += tokens
        self.usage_metrics.total_cost += cost

        # Update average latency
        total_latency = (
            self.usage_metrics.average_latency * (self.usage_metrics.total_calls - 1)
            + latency
        )
        self.usage_metrics.average_latency = (
            total_latency / self.usage_metrics.total_calls
        )

        # Update success rate
        successful_calls = (
            self.usage_metrics.success_rate * (self.usage_metrics.total_calls - 1) / 100
        )
        if success:
            successful_calls += 1
        self.usage_metrics.success_rate = (
            successful_calls / self.usage_metrics.total_calls
        ) * 100

        # Update by-model metrics
        if model_name not in self.usage_metrics.by_model:
            self.usage_metrics.by_model[model_name] = {
                "calls": 0,
                "tokens": 0,
                "cost": 0.0,
            }

        self.usage_metrics.by_model[model_name]["calls"] += 1
        self.usage_metrics.by_model[model_name]["tokens"] += tokens
        self.usage_metrics.by_model[model_name]["cost"] += cost

    def get_usage_metrics(self) -> AIUsageMetrics:
        """Get current usage metrics."""
        return self.usage_metrics

    def clear_cache(self):
        """Clear the AI response cache via cache manager."""
        cleared_count = self.cache_manager.clear_cache()
        logger.info(f"AI response cache cleared: {cleared_count} entries removed")

    def _cache_result(self, cache_key: str, result: Any, cost_estimate: float = 0.0):
        """Cache a result for future use."""
        # Delegate to cache manager
        self.cache_manager.set(
            prompt=cache_key,
            model="default",
            cache_type=CacheType.AI_RESPONSE,
            value=result,
            cost_saved=cost_estimate,
        )

    async def _check_rate_limit(self, model_or_provider: str) -> bool:
        """Check if rate limit allows making a call."""
        import time

        # If model_or_provider is a model role name, get the actual model
        if model_or_provider in self.models:
            model_config = self.models[model_or_provider]
            provider = model_config.provider.value
        else:
            # Assume it's a provider name or model name
            provider = self._detect_provider(model_or_provider).value

        current_time = time.time()
        rate_info = self.rate_limits.get(provider, {})

        # Reset window if needed
        if current_time - rate_info.get("window_start", 0) >= 60:
            rate_info["calls_made"] = 0
            rate_info["window_start"] = current_time

        # Check if we can make the call
        calls_per_minute = rate_info.get("calls_per_minute", 60)
        calls_made = rate_info.get("calls_made", 0)

        if calls_made >= calls_per_minute:
            logger.warning(
                f"Rate limit exceeded for {provider}: {calls_made}/{calls_per_minute}"
            )
            return False

        # Increment call count
        rate_info["calls_made"] = calls_made + 1
        self.rate_limits[provider] = rate_info

        return True

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result by key."""
        return self.cache_manager.get(
            prompt=cache_key, model="default", cache_type=CacheType.AI_RESPONSE
        )

    def _get_provider_from_model(self, model_name: str) -> str:
        """Get provider name from model name."""
        # If model_name is a role name, get the actual model
        if model_name in self.models:
            return self.models[model_name].provider.value
        else:
            return self._detect_provider(model_name).value


# Custom exception classes
class AICallError(RuntimeError):
    """Raised when an AI model call fails after fallback attempts."""


class TaskGenerationError(RuntimeError):
    """Raised when the task generation pipeline fails irrecoverably."""


# Export the main class
__all__ = [
    "AIService",
    "ModelConfig",
    "ModelProvider",
    "AIUsageMetrics",
    "ResearchResults",
]
