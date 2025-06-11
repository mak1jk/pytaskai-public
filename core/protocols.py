"""
PyTaskAI Core Protocols

Abstract base classes and protocols defining the interfaces for major components.
These protocols enable dependency inversion and make components easily testable.
"""

from abc import ABC, abstractmethod
from typing import (
    Any, Dict, List, Optional, Union, Tuple, 
    Protocol, TypeVar, Generic, AsyncIterator
)
from datetime import datetime, timedelta
from enum import Enum

from .exceptions import AIServiceError, CacheError, UsageTrackingError


# Type variables for generic protocols
T = TypeVar('T')
K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type


class CacheType(str, Enum):
    """Cache type enumeration for different cache categories."""
    AI_RESPONSE = "ai_response"
    LTS_RESEARCH = "lts_research"
    BEST_PRACTICES = "best_practices"
    TASK_GENERATION = "task_generation"
    GENERAL = "general"


class RateLimitStatus(str, Enum):
    """Rate limit status enumeration."""
    OK = "ok"
    APPROACHING_LIMIT = "approaching_limit"
    RATE_LIMITED = "rate_limited"


class LLMProvider(Protocol):
    """Protocol for AI/LLM provider implementations."""
    
    @property
    def name(self) -> str:
        """Provider name (e.g., 'openai', 'anthropic')."""
        ...
    
    @property
    def supported_models(self) -> List[str]:
        """List of supported model names."""
        ...
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generate completion from messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Provider-specific parameters
            
        Returns:
            Dict containing response with usage statistics
            
        Raises:
            AIServiceError: If completion fails
        """
        ...
    
    async def estimate_cost(
        self, 
        input_tokens: int, 
        output_tokens: int, 
        model: str
    ) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens  
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        ...
    
    def validate_model(self, model: str) -> bool:
        """Check if model is supported by this provider."""
        ...


class CacheBackend(Protocol[K, V]):
    """Protocol for cache backend implementations."""
    
    async def get(
        self, 
        key: K, 
        default: Optional[V] = None
    ) -> Optional[V]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        ...
    
    async def set(
        self, 
        key: K, 
        value: V, 
        ttl: Optional[timedelta] = None
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (None for no expiration)
        """
        ...
    
    async def delete(self, key: K) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key existed and was deleted
        """
        ...
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            pattern: Optional pattern to match keys (None clears all)
            
        Returns:
            Number of entries cleared
        """
        ...
    
    async def exists(self, key: K) -> bool:
        """Check if key exists in cache."""
        ...
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        ...


class UsageTracker(Protocol):
    """Protocol for usage tracking implementations."""
    
    def record_usage(
        self,
        provider: str,
        model: str,
        operation_type: str,
        operation_context: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        estimated_cost: float = 0.0,
        duration_ms: int = 0,
        status: str = "success",
        **metadata: Any
    ) -> None:
        """
        Record AI usage event.
        
        Args:
            provider: AI provider name
            model: Model name used
            operation_type: Type of operation
            operation_context: Operation context/description
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            estimated_cost: Estimated cost in USD
            duration_ms: Operation duration in milliseconds
            status: Operation status (success, failed, cached)
            **metadata: Additional metadata
        """
        ...
    
    def get_usage_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
        operation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Args:
            start_date: Start date filter
            end_date: End date filter  
            provider: Provider filter
            operation_type: Operation type filter
            
        Returns:
            Usage statistics dictionary
        """
        ...
    
    def get_cost_breakdown(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get cost breakdown by provider/model."""
        ...
    
    def export_usage_data(
        self, 
        format: str = "csv",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export usage data in specified format."""
        ...


class TaskRepository(Protocol):
    """Protocol for task persistence implementations."""
    
    async def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        ...
    
    async def create_task(self, task_data: Dict[str, Any]) -> int:
        """Create new task and return ID."""
        ...
    
    async def update_task(self, task_id: int, updates: Dict[str, Any]) -> bool:
        """Update task and return success status."""
        ...
    
    async def delete_task(self, task_id: int) -> bool:
        """Delete task and return success status."""
        ...
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filters."""
        ...
    
    async def get_dependencies(self, task_id: int) -> List[int]:
        """Get task dependencies."""
        ...
    
    async def add_dependency(self, task_id: int, dependency_id: int) -> bool:
        """Add task dependency."""
        ...
    
    async def remove_dependency(self, task_id: int, dependency_id: int) -> bool:
        """Remove task dependency."""
        ...


class PromptRegistry(Protocol):
    """Protocol for prompt template management."""
    
    def get_prompt(
        self, 
        template_name: str, 
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get rendered prompt template.
        
        Args:
            template_name: Name of the template
            variables: Template variables
            
        Returns:
            Rendered prompt string
        """
        ...
    
    def register_template(
        self, 
        name: str, 
        template: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a new prompt template."""
        ...
    
    def list_templates(self) -> List[str]:
        """List available template names."""
        ...
    
    def validate_template(self, template: str) -> bool:
        """Validate template syntax."""
        ...


class ConfigurationProvider(Protocol):
    """Protocol for configuration management."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        ...
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        ...
    
    def reload(self) -> None:
        """Reload configuration from source."""
        ...
    
    def validate(self) -> List[str]:
        """Validate configuration and return errors."""
        ...


class EventEmitter(Protocol):
    """Protocol for event emission and handling."""
    
    def emit(self, event: str, data: Any = None) -> None:
        """Emit an event with optional data."""
        ...
    
    def on(self, event: str, handler) -> None:
        """Register event handler."""
        ...
    
    def off(self, event: str, handler) -> None:
        """Unregister event handler."""
        ...


class MetricsCollector(Protocol):
    """Protocol for metrics collection."""
    
    def increment(self, metric: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        ...
    
    def gauge(self, metric: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        ...
    
    def histogram(self, metric: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram value."""
        ...
    
    def timer(self, metric: str, tags: Optional[Dict[str, str]] = None):
        """Create a context manager for timing operations."""
        ...


# Abstract base classes for common implementations

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers with common functionality."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod  
    def supported_models(self) -> List[str]:
        """Supported models."""
        pass
    
    def validate_model(self, model: str) -> bool:
        """Default model validation."""
        return model in self.supported_models
    
    @abstractmethod
    async def complete(self, **kwargs) -> Dict[str, Any]:
        """Abstract completion method."""
        pass


class BaseCacheBackend(ABC, Generic[K, V]):
    """Abstract base class for cache backends."""
    
    def __init__(self, default_ttl: Optional[timedelta] = None):
        self.default_ttl = default_ttl or timedelta(hours=1)
    
    @abstractmethod
    async def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        pass
    
    @abstractmethod
    async def set(self, key: K, value: V, ttl: Optional[timedelta] = None) -> None:
        pass
    
    @abstractmethod
    async def delete(self, key: K) -> bool:
        pass
    
    async def get_or_set(
        self, 
        key: K, 
        factory, 
        ttl: Optional[timedelta] = None
    ) -> V:
        """Get value from cache or compute and cache it."""
        value = await self.get(key)
        if value is None:
            value = await factory() if hasattr(factory, '__await__') else factory()
            await self.set(key, value, ttl or self.default_ttl)
        return value