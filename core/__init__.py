"""
PyTaskAI Core Module

Pure domain layer containing:
- Domain models and value objects
- Business exceptions hierarchy  
- Abstract protocols and interfaces
- Core utilities and constants

This module has no dependencies on infrastructure or external services.
"""

__version__ = "0.1.0"
__all__ = [
    # Exceptions
    "PyTaskAIError",
    "ValidationError", 
    "ConfigurationError",
    "AIServiceError",
    "TaskNotFoundError",
    "DependencyError",
    
    # Protocols
    "LLMProvider",
    "CacheBackend", 
    "UsageTracker",
    "TaskRepository",
    
    # Models (re-exported from shared for compatibility)
    "Task",
    "TaskStatus",
    "TaskPriority", 
    "TaskType",
    "BugSeverity",
]

# Import and re-export core components
from .exceptions import (
    PyTaskAIError,
    ValidationError,
    ConfigurationError, 
    AIServiceError,
    TaskNotFoundError,
    DependencyError,
)

from .protocols import (
    LLMProvider,
    CacheBackend,
    UsageTracker, 
    TaskRepository,
)

# Re-export shared models for backward compatibility
try:
    from shared.models import (
        Task as SharedTask,
        TaskStatus as SharedTaskStatus,
        TaskPriority as SharedTaskPriority,
        TaskType as SharedTaskType, 
        BugSeverity as SharedBugSeverity,
    )
    # Create aliases for backward compatibility
    Task = SharedTask
    TaskStatus = SharedTaskStatus
    TaskPriority = SharedTaskPriority
    TaskType = SharedTaskType
    BugSeverity = SharedBugSeverity
except ImportError:
    # If shared models not available, use our own
    from .models import (
        Task,
        TaskStatus,
        TaskPriority,
        TaskType,
        BugSeverity,
    )