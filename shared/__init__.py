"""
PyTaskAI - Shared Package

Shared models, schemas, and utilities used across the PyTaskAI system.
"""

__version__ = "0.1.0"

from .models import *
from .schemas import *

__all__ = [
    "models",
    "schemas",
    # Core models
    "Task",
    "SubTask",
    "TaskStatus",
    "TaskPriority",
    # MCP Request models
    "AddTaskRequest",
    "ExpandTaskRequest",
    "UpdateSubtaskRequest",
    "SetTaskStatusRequest",
    "NextTaskRequest",
    "AnalyzeComplexityRequest",
    "DependencyRequest",
    # Report models
    "ComplexityReport",
    "ProjectComplexityReport",
    "ValidationReport",
    # Usage tracking
    "AIUsageRecord",
    "UsageSummary",
    # Response models
    "TaskResponse",
    "MCPToolResponse",
    # UI models
    "KanbanBoard",
    "KanbanColumn",
    "TaskCardData",
    # Analytics
    "VelocityMetrics",
    "BurndownData",
    "ProjectInsights",
    # Collaboration
    "User",
    "TaskAssignment",
    "Comment",
    "ActivityEvent",
]
