"""
PyTaskAI Core Exceptions

Centralized exception hierarchy for the PyTaskAI system.
All exceptions inherit from PyTaskAIError for consistent error handling.
"""

from typing import Optional, Dict, Any


class PyTaskAIError(Exception):
    """Base exception for all PyTaskAI errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class ValidationError(PyTaskAIError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = value
        super().__init__(message, details)
        self.field = field
        self.value = value


class ConfigurationError(PyTaskAIError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details)
        self.config_key = config_key


class AIServiceError(PyTaskAIError):
    """Base exception for AI service related errors."""
    
    def __init__(self, message: str, provider: Optional[str] = None, model: Optional[str] = None):
        details = {}
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model
        super().__init__(message, details)
        self.provider = provider
        self.model = model


class AICallError(AIServiceError):
    """Raised when AI model calls fail after retries."""
    
    def __init__(self, message: str, provider: Optional[str] = None, model: Optional[str] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, provider, model)
        self.original_error = original_error
        if original_error:
            self.details["original_error"] = str(original_error)


class RateLimitError(AIServiceError):
    """Raised when AI service rate limits are exceeded."""
    
    def __init__(self, message: str, provider: Optional[str] = None, 
                 retry_after: Optional[int] = None):
        super().__init__(message, provider)
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after_seconds"] = retry_after


class TaskGenerationError(AIServiceError):
    """Raised when task generation fails irrecoverably."""
    pass


class TaskNotFoundError(PyTaskAIError):
    """Raised when a requested task does not exist."""
    
    def __init__(self, task_id: Any, message: Optional[str] = None):
        if message is None:
            message = f"Task not found: {task_id}"
        super().__init__(message, {"task_id": task_id})
        self.task_id = task_id


class DependencyError(PyTaskAIError):
    """Raised when task dependency operations fail."""
    
    def __init__(self, message: str, task_id: Optional[Any] = None, 
                 dependency_id: Optional[Any] = None):
        details = {}
        if task_id:
            details["task_id"] = task_id
        if dependency_id:
            details["dependency_id"] = dependency_id
        super().__init__(message, details)
        self.task_id = task_id
        self.dependency_id = dependency_id


class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected."""
    
    def __init__(self, task_id: Any, dependency_path: list):
        message = f"Circular dependency detected: {' -> '.join(map(str, dependency_path))}"
        super().__init__(message, task_id)
        self.dependency_path = dependency_path


class CacheError(PyTaskAIError):
    """Base exception for cache operations."""
    
    def __init__(self, message: str, cache_key: Optional[str] = None):
        details = {}
        if cache_key:
            details["cache_key"] = cache_key
        super().__init__(message, details)
        self.cache_key = cache_key


class UsageTrackingError(PyTaskAIError):
    """Raised when usage tracking operations fail."""
    pass


class DatabaseError(PyTaskAIError):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 table: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        super().__init__(message, details)
        self.operation = operation
        self.table = table


class MigrationError(PyTaskAIError):
    """Raised when data migration operations fail."""
    
    def __init__(self, message: str, from_version: Optional[str] = None, 
                 to_version: Optional[str] = None):
        details = {}
        if from_version:
            details["from_version"] = from_version
        if to_version:
            details["to_version"] = to_version
        super().__init__(message, details)
        self.from_version = from_version
        self.to_version = to_version


class PromptError(PyTaskAIError):
    """Raised when prompt template operations fail."""
    
    def __init__(self, message: str, template_name: Optional[str] = None):
        details = {}
        if template_name:
            details["template_name"] = template_name
        super().__init__(message, details)
        self.template_name = template_name


class AuthenticationError(PyTaskAIError):
    """Raised when authentication with external services fails."""
    
    def __init__(self, message: str, service: Optional[str] = None):
        details = {}
        if service:
            details["service"] = service
        super().__init__(message, details)
        self.service = service


# Backwards compatibility aliases
class AICallError(AICallError):
    """Legacy alias for AICallError - already defined above."""
    pass


class TaskGenerationError(TaskGenerationError):
    """Legacy alias for TaskGenerationError - already defined above."""
    pass