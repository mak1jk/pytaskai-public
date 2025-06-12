"""
Base LLM Provider Protocol and Models

Defines the abstract interface for all LLM providers with common models
and error handling.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Protocol
import logging

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported LLM provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GOOGLE = "google"
    XAI = "xai"


class ModelRole(str, Enum):
    """Model roles for different use cases"""
    RESEARCH = "research"              # Web research and LTS lookups
    TASK_GENERATION = "task_generation"  # Task creation and management
    BEST_PRACTICES = "best_practices"  # Code quality and standards
    DEFAULT = "default"                # General purpose fallback


@dataclass
class ModelConfig:
    """Configuration for an LLM model"""
    name: str
    provider: ProviderType
    max_tokens: int = 4096
    temperature: float = 0.1
    cost_per_1k_tokens: float = 0.0
    supports_system_prompt: bool = True
    context_window: int = 4096
    rate_limit_per_minute: int = 60
    role: ModelRole = ModelRole.DEFAULT


@dataclass
class LLMResponse:
    """Response from LLM provider"""
    content: str
    model: str
    provider: ProviderType
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class LLMError(Exception):
    """Base exception for LLM provider errors"""
    
    def __init__(self, message: str, provider: ProviderType, 
                 model: str = "", error_code: str = ""):
        self.provider = provider
        self.model = model
        self.error_code = error_code
        super().__init__(message)


class RateLimitError(LLMError):
    """Raised when rate limit is exceeded"""
    pass


class QuotaExceededError(LLMError):
    """Raised when quota/billing limit is exceeded"""
    pass


class ModelNotFoundError(LLMError):
    """Raised when requested model is not available"""
    pass


class LLMProvider(Protocol):
    """Protocol defining the interface for LLM providers"""
    
    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type"""
        ...
    
    @property
    def supported_models(self) -> List[str]:
        """Return list of supported model names"""
        ...
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available (has API key, etc.)"""
        ...
    
    async def generate_response(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate response using the specified model"""
        ...
    
    async def health_check(self) -> bool:
        """Check if provider is healthy and responsive"""
        ...
    
    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        ...


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self._initialized = False
        self._last_health_check = None
        self._health_status = False
        
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type"""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of supported model names"""
        pass
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.api_key is not None and self._initialized
    
    async def initialize(self) -> bool:
        """Initialize the provider"""
        try:
            if not self.api_key:
                logger.warning(f"{self.provider_type} provider missing API key")
                return False
                
            # Perform provider-specific initialization
            await self._initialize_provider()
            self._initialized = True
            logger.info(f"{self.provider_type} provider initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider_type}: {e}")
            return False
    
    @abstractmethod
    async def _initialize_provider(self) -> None:
        """Provider-specific initialization logic"""
        pass
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate response using the specified model"""
        pass
    
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        try:
            # Cache health check for 5 minutes
            now = datetime.now()
            if (self._last_health_check and 
                (now - self._last_health_check).seconds < 300 and
                self._health_status):
                return self._health_status
            
            # Perform actual health check
            self._health_status = await self._perform_health_check()
            self._last_health_check = now
            return self._health_status
            
        except Exception as e:
            logger.warning(f"Health check failed for {self.provider_type}: {e}")
            self._health_status = False
            return False
    
    @abstractmethod
    async def _perform_health_check(self) -> bool:
        """Provider-specific health check"""
        pass
    
    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        # Default implementation - providers should override
        if model in self.supported_models:
            return ModelConfig(
                name=model,
                provider=self.provider_type,
                max_tokens=4096,
                temperature=0.1
            )
        return None