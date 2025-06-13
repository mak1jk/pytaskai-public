"""
MCP-specific error handling for PyTaskAI adapter layer.

This module provides centralized error handling and conversion between
application layer exceptions and MCP protocol error responses, following
the Command pattern for consistent error handling across all MCP tools.
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, TypeVar

from fastmcp.exceptions import McpError

from pytaskai.adapters.mcp.dto_mappers import MCPErrorMapper

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


class MCPErrorCodes:
    """Standard MCP error codes for PyTaskAI."""

    # General errors
    UNKNOWN = "UNKNOWN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"

    # Business logic errors
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    WORKSPACE_NOT_FOUND = "WORKSPACE_NOT_FOUND"
    DUPLICATE_TASK = "DUPLICATE_TASK"
    INVALID_TASK_STATUS = "INVALID_TASK_STATUS"
    CIRCULAR_DEPENDENCY = "CIRCULAR_DEPENDENCY"

    # Service errors
    DATABASE_ERROR = "DATABASE_ERROR"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    NOTIFICATION_SERVICE_ERROR = "NOTIFICATION_SERVICE_ERROR"

    # Permission errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"


class MCPTaskError(McpError):
    """Base exception for MCP task-related errors."""

    def __init__(self, message: str, error_code: str = MCPErrorCodes.UNKNOWN) -> None:
        super().__init__(message)
        self.error_code = error_code


class MCPValidationError(MCPTaskError):
    """Exception for validation errors in MCP requests."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"Validation failed for field '{field}': {message}")
        self.error_code = MCPErrorCodes.VALIDATION_ERROR
        self.field = field


class MCPTaskNotFoundError(MCPTaskError):
    """Exception for task not found errors."""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task not found: {task_id}")
        self.error_code = MCPErrorCodes.TASK_NOT_FOUND
        self.task_id = task_id


class MCPDocumentNotFoundError(MCPTaskError):
    """Exception for document not found errors."""

    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document not found: {document_id}")
        self.error_code = MCPErrorCodes.DOCUMENT_NOT_FOUND
        self.document_id = document_id


class MCPDatabaseError(MCPTaskError):
    """Exception for database-related errors."""

    def __init__(self, message: str, original_error: Exception) -> None:
        super().__init__(f"Database error: {message}")
        self.error_code = MCPErrorCodes.DATABASE_ERROR
        self.original_error = original_error


class MCPServiceError(MCPTaskError):
    """Exception for external service errors."""

    def __init__(
        self, service_name: str, message: str, original_error: Exception
    ) -> None:
        super().__init__(f"{service_name} error: {message}")
        self.error_code = MCPErrorCodes.AI_SERVICE_ERROR
        self.service_name = service_name
        self.original_error = original_error


def mcp_error_handler(func: F) -> F:
    """
    Decorator for handling exceptions in MCP tools.

    This decorator catches exceptions from the application layer and converts
    them to appropriate MCP error responses, following the Command pattern
    for consistent error handling.

    Args:
        func: MCP tool function to wrap

    Returns:
        Wrapped function with error handling
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)

        except MCPTaskError as e:
            # MCP-specific errors - re-raise as McpError
            logger.warning(f"MCP error in {func.__name__}: {e}")
            raise McpError(str(e))

        except ValueError as e:
            # Validation errors from DTOs
            logger.warning(f"Validation error in {func.__name__}: {e}")
            raise McpError(f"Validation error: {e}")

        except KeyError as e:
            # Missing required fields
            logger.warning(f"Missing field in {func.__name__}: {e}")
            raise McpError(f"Missing required field: {e}")

        except AttributeError as e:
            # Missing attributes (usually DTOs or entities)
            logger.warning(f"Attribute error in {func.__name__}: {e}")
            raise McpError(f"Invalid object state: {e}")

        except TypeError as e:
            # Type errors from incorrect usage
            logger.warning(f"Type error in {func.__name__}: {e}")
            raise McpError(f"Invalid parameter type: {e}")

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise McpError(f"Internal server error: {e}")

    return wrapper


class MCPErrorHandler:
    """Centralized error handling for MCP adapter layer."""

    @staticmethod
    def handle_application_error(error: Exception, context: str = "") -> MCPTaskError:
        """
        Convert application layer exceptions to MCP exceptions.

        Args:
            error: Original exception from application layer
            context: Additional context about where the error occurred

        Returns:
            Appropriate MCPTaskError subclass
        """
        error_context = f" in {context}" if context else ""

        # Map common application errors to MCP errors
        if isinstance(error, ValueError):
            if "not found" in str(error).lower():
                if "task" in str(error).lower():
                    return MCPTaskNotFoundError("unknown")
                elif "document" in str(error).lower():
                    return MCPDocumentNotFoundError("unknown")
            return MCPValidationError("unknown", str(error))

        elif isinstance(error, KeyError):
            return MCPValidationError(str(error), "Missing required field")

        elif "database" in str(error).lower() or "sql" in str(error).lower():
            return MCPDatabaseError(f"Database operation failed{error_context}", error)

        elif "ai" in str(error).lower() or "openai" in str(error).lower():
            return MCPServiceError("AI Service", str(error), error)

        else:
            # Generic error
            return MCPTaskError(f"Operation failed{error_context}: {error}")

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any], required_fields: list[str]
    ) -> None:
        """
        Validate that required fields are present in request data.

        Args:
            data: Request data dictionary
            required_fields: List of required field names

        Raises:
            MCPValidationError: If any required field is missing
        """
        for field in required_fields:
            if field not in data:
                raise MCPValidationError(field, "Field is required")

            value = data[field]
            if value is None or (isinstance(value, str) and not value.strip()):
                raise MCPValidationError(field, "Field cannot be empty")

    @staticmethod
    def validate_field_type(
        data: Dict[str, Any], field: str, expected_type: type
    ) -> None:
        """
        Validate that a field has the expected type.

        Args:
            data: Request data dictionary
            field: Field name to validate
            expected_type: Expected Python type

        Raises:
            MCPValidationError: If field type is incorrect
        """
        if field in data and data[field] is not None:
            if not isinstance(data[field], expected_type):
                raise MCPValidationError(
                    field,
                    f"Expected {expected_type.__name__}, got {type(data[field]).__name__}",
                )

    @staticmethod
    def validate_field_choices(
        data: Dict[str, Any], field: str, choices: list[str]
    ) -> None:
        """
        Validate that a field value is one of the allowed choices.

        Args:
            data: Request data dictionary
            field: Field name to validate
            choices: List of allowed values

        Raises:
            MCPValidationError: If field value is not in choices
        """
        if field in data and data[field] is not None:
            value = data[field]
            if value not in choices:
                raise MCPValidationError(
                    field,
                    f"Invalid choice '{value}'. Must be one of: {', '.join(choices)}",
                )

    @staticmethod
    def create_success_response(
        data: Any, message: str = "Operation completed successfully"
    ) -> Dict[str, Any]:
        """
        Create a standardized success response.

        Args:
            data: Response data
            message: Success message

        Returns:
            Standardized success response dictionary
        """
        return {
            "success": True,
            "message": message,
            "data": data,
        }

    @staticmethod
    def log_tool_execution(tool_name: str, request_data: Dict[str, Any]) -> None:
        """
        Log MCP tool execution for debugging and monitoring.

        Args:
            tool_name: Name of the MCP tool being executed
            request_data: Request data (sensitive data will be masked)
        """
        # Mask sensitive data
        safe_data = {
            k: v for k, v in request_data.items() if not _is_sensitive_field(k)
        }
        logger.info(f"Executing MCP tool '{tool_name}' with data: {safe_data}")


def _is_sensitive_field(field_name: str) -> bool:
    """Check if a field contains sensitive data that should not be logged."""
    sensitive_fields = ["password", "token", "key", "secret", "auth"]
    return any(sensitive in field_name.lower() for sensitive in sensitive_fields)
