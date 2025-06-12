"""
PyTaskAI Core Utilities

Common utility functions used across the system.
These utilities are pure functions with no external dependencies.
"""

import re
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, TypeVar, Callable
from decimal import Decimal, ROUND_HALF_UP

from .constants import PATTERNS, COMPLEXITY_WEIGHTS, PRIORITY_ORDER, SEVERITY_ORDER
from .exceptions import ValidationError

T = TypeVar('T')


# String Utilities

def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string by removing/replacing problematic characters.
    
    Args:
        text: Input string to sanitize
        max_length: Maximum length (truncate if longer)
        
    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Remove control characters and normalize whitespace
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip()
    
    return text


def slugify(text: str, max_length: int = 50) -> str:
    """
    Convert text to a URL-safe slug.
    
    Args:
        text: Input text
        max_length: Maximum slug length
        
    Returns:
        URL-safe slug
    """
    # Convert to lowercase and replace spaces/special chars
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug


def extract_email_addresses(text: str) -> List[str]:
    """Extract email addresses from text."""
    return re.findall(PATTERNS["email"], text)


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    return re.findall(PATTERNS["url"], text)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    if len(suffix) >= max_length:
        return text[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


# Validation Utilities

def validate_email(email: str) -> bool:
    """Validate email address format."""
    return bool(re.match(PATTERNS["email"], email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    return bool(re.match(PATTERNS["url"], url))


def validate_task_id(task_id: Union[str, int]) -> bool:
    """Validate task ID format."""
    return bool(re.match(PATTERNS["task_id"], str(task_id)))


def validate_version(version: str) -> bool:
    """Validate semantic version format."""
    return bool(re.match(PATTERNS["version"], version))


def validate_tag(tag: str) -> bool:
    """Validate tag format."""
    return bool(re.match(PATTERNS["tag"], tag))


def validate_percentage(value: Union[int, float]) -> bool:
    """Validate percentage value (0-100)."""
    try:
        num_value = float(value)
        return 0 <= num_value <= 100
    except (ValueError, TypeError):
        return False


# Hash and Encryption Utilities

def generate_hash(data: Union[str, bytes, Dict[str, Any]], algorithm: str = "md5") -> str:
    """
    Generate hash for data.
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
        
    Returns:
        Hex digest of hash
    """
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def generate_cache_key(*parts: str, separator: str = ":") -> str:
    """
    Generate cache key from parts.
    
    Args:
        *parts: Key parts to join
        separator: Separator character
        
    Returns:
        Cache key string
    """
    sanitized_parts = []
    for part in parts:
        # Convert to string and sanitize
        part_str = str(part).strip()
        # Replace separator and control chars
        part_str = re.sub(f'[{re.escape(separator)}\\x00-\\x1f\\x7f-\\x9f]', '_', part_str)
        sanitized_parts.append(part_str)
    
    return separator.join(sanitized_parts)


def generate_unique_id(prefix: str = "", timestamp: bool = True) -> str:
    """
    Generate unique ID.
    
    Args:
        prefix: Optional prefix
        timestamp: Include timestamp for uniqueness
        
    Returns:
        Unique ID string
    """
    parts = []
    
    if prefix:
        parts.append(prefix)
    
    if timestamp:
        parts.append(str(int(datetime.now().timestamp() * 1000000)))
    
    # Add random component
    import secrets
    parts.append(secrets.token_hex(4))
    
    return "_".join(parts)


# Date and Time Utilities

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """
    Parse datetime string with multiple format support.
    
    Args:
        dt_str: Datetime string
        
    Returns:
        Parsed datetime or None if invalid
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO with microseconds
        "%Y-%m-%dT%H:%M:%S",     # ISO without microseconds
        "%Y-%m-%d %H:%M:%S",     # Standard format
        "%Y-%m-%d",              # Date only
        "%d/%m/%Y",              # European format
        "%m/%d/%Y",              # American format
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    return None


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 0:
        return "0s"
    
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f}h"
    
    days = hours / 24
    return f"{days:.1f}d"


def time_ago(dt: datetime) -> str:
    """
    Get human-readable time ago string.
    
    Args:
        dt: Datetime to compare
        
    Returns:
        Time ago string (e.g., "2 hours ago")
    """
    now = datetime.now()
    if dt.tzinfo and not now.tzinfo:
        # Make timezone-aware if needed
        import timezone
        now = now.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    
    minutes = int(seconds / 60)
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    
    hours = int(minutes / 60)
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    
    days = int(hours / 24)
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} ago"
    
    months = int(days / 30)
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} ago"
    
    years = int(months / 12)
    return f"{years} year{'s' if years != 1 else ''} ago"


def is_business_day(dt: datetime) -> bool:
    """Check if date is a business day (Monday-Friday)."""
    return dt.weekday() < 5


def add_business_days(dt: datetime, days: int) -> datetime:
    """Add business days to a date."""
    current = dt
    days_added = 0
    
    while days_added < days:
        current += timedelta(days=1)
        if is_business_day(current):
            days_added += 1
    
    return current


# Numeric Utilities

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that handles zero division."""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def round_decimal(value: float, places: int = 2) -> float:
    """Round decimal to specified places using banker's rounding."""
    decimal_value = Decimal(str(value))
    rounded = decimal_value.quantize(
        Decimal('0.' + '0' * places), 
        rounding=ROUND_HALF_UP
    )
    return float(rounded)


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))


def percentage(part: Union[int, float], total: Union[int, float]) -> float:
    """Calculate percentage with safe division."""
    return safe_divide(part * 100, total, 0.0)


# Collection Utilities

def flatten_dict(d: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    Flatten nested dictionary.
    
    Args:
        d: Dictionary to flatten
        separator: Key separator
        
    Returns:
        Flattened dictionary
    """
    result = {}
    
    def _flatten(obj: Any, parent_key: str = ""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                _flatten(value, new_key)
        else:
            result[parent_key] = obj
    
    _flatten(d)
    return result


def unflatten_dict(d: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    Unflatten dictionary.
    
    Args:
        d: Flattened dictionary
        separator: Key separator
        
    Returns:
        Nested dictionary
    """
    result = {}
    
    for key, value in d.items():
        parts = key.split(separator)
        current = result
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    return result


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deduplicate_list(lst: List[T], key_func: Optional[Callable[[T], Any]] = None) -> List[T]:
    """
    Remove duplicates from list while preserving order.
    
    Args:
        lst: Input list
        key_func: Optional function to extract comparison key
        
    Returns:
        Deduplicated list
    """
    seen = set()
    result = []
    
    for item in lst:
        key = key_func(item) if key_func else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def sort_by_priority(items: List[Dict[str, Any]], priority_key: str = "priority") -> List[Dict[str, Any]]:
    """Sort items by priority using predefined order."""
    return sorted(
        items,
        key=lambda x: PRIORITY_ORDER.get(x.get(priority_key, "medium"), 2),
        reverse=True
    )


def sort_by_severity(items: List[Dict[str, Any]], severity_key: str = "severity") -> List[Dict[str, Any]]:
    """Sort items by bug severity using predefined order."""
    return sorted(
        items,
        key=lambda x: SEVERITY_ORDER.get(x.get(severity_key, "minor"), 1),
        reverse=True
    )


# Calculation Utilities

def calculate_task_complexity(
    description_length: int,
    subtask_count: int,
    dependency_count: int,
    estimated_hours: Optional[float] = None
) -> int:
    """
    Calculate task complexity score.
    
    Args:
        description_length: Length of task description
        subtask_count: Number of subtasks
        dependency_count: Number of dependencies
        estimated_hours: Estimated completion hours
        
    Returns:
        Complexity score (1-10)
    """
    score = 0.0
    
    # Description complexity (0-2 points)
    desc_score = min(description_length / 500, 2.0) * COMPLEXITY_WEIGHTS["description_length"]
    score += desc_score
    
    # Subtask complexity (0-3 points)
    subtask_score = min(subtask_count / 10, 3.0) * COMPLEXITY_WEIGHTS["subtask_count"]
    score += subtask_score
    
    # Dependency complexity (0-2 points)
    dep_score = min(dependency_count / 5, 2.0) * COMPLEXITY_WEIGHTS["dependency_count"]
    score += dep_score
    
    # Time estimate complexity (0-3 points)
    if estimated_hours:
        time_score = min(estimated_hours / 40, 3.0) * COMPLEXITY_WEIGHTS["estimated_hours"]
        score += time_score
    
    # Scale to 1-10 and round
    complexity = max(1, min(10, round(score * 10)))
    return complexity


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for text (rough approximation).
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    # Rough estimate: 4 characters per token
    return max(1, len(text) // 4)


def estimate_cost(input_tokens: int, output_tokens: int, cost_per_1k: float) -> float:
    """
    Estimate cost for AI operation.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost_per_1k: Cost per 1000 tokens
        
    Returns:
        Estimated cost in USD
    """
    total_tokens = input_tokens + output_tokens
    return round_decimal((total_tokens / 1000) * cost_per_1k, 4)


# Retry Utilities

def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Delay in seconds
    """
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)


# Environment and Configuration Utilities

def get_bool_env(key: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    import os
    value = os.getenv(key, "").lower()
    return value in ("true", "1", "yes", "on") if value else default


def get_int_env(key: str, default: int = 0) -> int:
    """Get integer value from environment variable."""
    import os
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_float_env(key: str, default: float = 0.0) -> float:
    """Get float value from environment variable."""
    import os
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


# Error Handling Utilities

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely serialize object to JSON."""
    try:
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    except (TypeError, ValueError):
        return default