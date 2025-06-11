"""
PyTaskAI Core Constants

Centralized constants and configuration values used across the system.
"""

from typing import Dict, List
from datetime import timedelta

# Application Constants
APP_NAME = "PyTaskAI"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "AI-powered task management system"

# Default Configuration Values
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000
DEFAULT_CACHE_TTL_HOURS = 24
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
MAX_TASK_TITLE_LENGTH = 200
MAX_TASK_DESCRIPTION_LENGTH = 10000

# Task Management Constants
MAX_TASK_DEPENDENCIES = 50
MAX_SUBTASKS_PER_TASK = 100
DEFAULT_TASK_PRIORITY = "medium"
DEFAULT_TASK_STATUS = "pending"
DEFAULT_TASK_TYPE = "task"

# AI Service Constants
DEFAULT_AI_TIMEOUT = 30.0
DEFAULT_AI_TEMPERATURE = 0.7
DEFAULT_AI_MAX_TOKENS = 4096
MAX_AI_RETRIES = 3
AI_FALLBACK_MODEL = "gpt-3.5-turbo"

# Rate Limiting Constants  
DEFAULT_RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_WARNING_THRESHOLD = 0.8  # 80% of limit
RATE_LIMIT_WINDOW_SECONDS = 60

# Cache Constants
CACHE_KEY_SEPARATOR = ":"
CACHE_VERSION = "v1"
DEFAULT_CACHE_TTL = timedelta(hours=DEFAULT_CACHE_TTL_HOURS)

# Cache TTL by type (in hours)
CACHE_TTL_CONFIG = {
    "ai_response": 24,
    "lts_research": 168,  # 7 days
    "best_practices": 48,  # 2 days
    "task_generation": 12,
    "general": 24,
}

# Error Messages
ERROR_MESSAGES = {
    "task_not_found": "Task with ID {task_id} not found",
    "invalid_task_status": "Invalid task status: {status}",
    "circular_dependency": "Circular dependency detected: {path}",
    "ai_service_error": "AI service error: {error}",
    "rate_limit_exceeded": "Rate limit exceeded for {provider}",
    "validation_error": "Validation error: {error}",
    "configuration_error": "Configuration error: {error}",
    "database_error": "Database error: {error}",
    "authentication_error": "Authentication failed for {service}",
    "permission_denied": "Permission denied for operation: {operation}",
}

# Success Messages
SUCCESS_MESSAGES = {
    "task_created": "Task created successfully with ID {task_id}",
    "task_updated": "Task {task_id} updated successfully",
    "task_deleted": "Task {task_id} deleted successfully",
    "dependency_added": "Dependency {dependency_id} added to task {task_id}",
    "dependency_removed": "Dependency {dependency_id} removed from task {task_id}",
    "ai_call_success": "AI call successful: {tokens} tokens, ${cost:.4f}, {duration:.2f}s",
    "cache_hit": "Cache hit for key: {key}",
    "cache_miss": "Cache miss for key: {key}",
}

# AI Provider Configuration
AI_PROVIDER_MODELS = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini", 
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
    ],
    "anthropic": [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229", 
        "claude-3-haiku-20240307",
    ],
    "perplexity": [
        "llama-3-sonar-large-32k-online",
        "llama-3-sonar-small-32k-online",
        "llama-3-8b-instruct",
        "llama-3-70b-instruct",
    ],
    "google": [
        "gemini-pro",
        "gemini-pro-vision",
        "text-bison",
    ],
    "xai": [
        "grok-beta",
    ],
}

# Cost estimates per 1K tokens (USD)
AI_MODEL_COSTS = {
    # OpenAI
    "gpt-4o": 0.0050,
    "gpt-4o-mini": 0.000150,
    "gpt-4-turbo": 0.0030,
    "gpt-4": 0.0300,
    "gpt-3.5-turbo": 0.0015,
    
    # Anthropic  
    "claude-3-opus-20240229": 0.0375,
    "claude-3-sonnet-20240229": 0.0030,
    "claude-3-haiku-20240307": 0.0002,
    
    # Perplexity
    "llama-3-sonar-large-32k-online": 0.0010,
    "llama-3-sonar-small-32k-online": 0.0005,
    "llama-3-8b-instruct": 0.0002,
    "llama-3-70b-instruct": 0.0008,
    
    # Google
    "gemini-pro": 0.0005,
    "gemini-pro-vision": 0.0005,
    "text-bison": 0.0005,
    
    # XAI
    "grok-beta": 0.0010,
}

# Default model configuration per role
DEFAULT_MODEL_CONFIG = {
    "default_generation": "gpt-4o-mini",
    "research_generation": "anthropic/claude-3-haiku-20240307", 
    "lts_search": "perplexity/llama-3-sonar-large-32k-online",
    "best_practices_search": "perplexity/llama-3-sonar-large-32k-online",
    "fallback": "gpt-3.5-turbo",
}

# Environment variable names
ENV_VARS = {
    "api_keys": {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "google": "GOOGLE_API_KEY", 
        "xai": "XAI_API_KEY",
    },
    "models": {
        "default": "PYTASKAI_DEFAULT_MODEL",
        "research": "PYTASKAI_RESEARCH_MODEL",
        "lts": "PYTASKAI_LTS_MODEL",
        "best_practices": "PYTASKAI_BEST_PRACTICES_MODEL",
        "fallback": "PYTASKAI_FALLBACK_MODEL",
    },
    "settings": {
        "temperature": "PYTASKAI_DEFAULT_TEMPERATURE",
        "max_tokens": "PYTASKAI_MAX_TOKENS", 
        "debug": "PYTASKAI_DEBUG",
        "log_level": "PYTASKAI_LOG_LEVEL",
        "cache_ttl": "PYTASKAI_CACHE_TTL",
    },
}

# File and Directory Constants
DATA_DIR = ".pytaskai"
TASKS_DIR = "tasks"
CACHE_DIR = "cache"
LOGS_DIR = "logs"
REPORTS_DIR = "reports"
BACKUPS_DIR = "backups"

DEFAULT_DB_NAME = "tasks.db"
DEFAULT_CACHE_NAME = "cache.db"
DEFAULT_CONFIG_NAME = "config.json"
DEFAULT_LOG_NAME = "pytaskai.log"

# File Extensions
SUPPORTED_IMPORT_FORMATS = [".json", ".csv", ".xlsx", ".md"]
SUPPORTED_EXPORT_FORMATS = [".json", ".csv", ".xlsx", ".pdf", ".md"]

# Task Complexity Weights
COMPLEXITY_WEIGHTS = {
    "description_length": 0.1,
    "subtask_count": 0.3,
    "dependency_count": 0.2,
    "estimated_hours": 0.4,
}

# Quality Metrics Thresholds
QUALITY_THRESHOLDS = {
    "max_cyclomatic_complexity": 15,
    "min_test_coverage": 80,
    "max_file_lines": 500,
    "max_function_lines": 50,
    "max_dependencies_per_module": 15,
}

# Status Transitions (allowed status changes)
ALLOWED_STATUS_TRANSITIONS = {
    "pending": ["in-progress", "blocked", "cancelled"],
    "in-progress": ["review", "done", "blocked", "pending"],
    "review": ["done", "in-progress", "pending"], 
    "done": ["pending"],  # Allow reopening
    "blocked": ["pending", "in-progress", "cancelled"],
    "cancelled": ["pending"],  # Allow reopening
    "deferred": ["pending", "cancelled"],
}

# Priority Ordering (for sorting)
PRIORITY_ORDER = {
    "lowest": 0,
    "low": 1, 
    "medium": 2,
    "high": 3,
    "highest": 4,
}

# Bug Severity Ordering
SEVERITY_ORDER = {
    "trivial": 0,
    "minor": 1,
    "major": 2, 
    "critical": 3,
    "blocker": 4,
}

# Regular Expressions
PATTERNS = {
    "task_id": r"^\d+$",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "url": r"^https?://[^\s/$.?#].[^\s]*$",
    "version": r"^\d+\.\d+\.\d+$",
    "tag": r"^[a-zA-Z0-9_-]+$",
}

# HTTP Status Codes (for API responses)
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}

# Logging Configuration
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Feature Flags (for gradual rollout)
FEATURE_FLAGS = {
    "ai_service_v2": False,
    "enhanced_caching": True,
    "structured_logging": True,
    "event_driven_architecture": False,
    "performance_monitoring": True,
}

# Export/Import Limits
MAX_EXPORT_TASKS = 10000
MAX_IMPORT_TASKS = 1000
MAX_CONCURRENT_OPERATIONS = 10

# Notification Types
NOTIFICATION_TYPES = [
    "task_created",
    "task_updated", 
    "task_completed",
    "dependency_added",
    "deadline_approaching",
    "ai_call_failed",
    "rate_limit_warning",
]