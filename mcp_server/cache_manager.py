"""
PyTaskAI - Cache Manager

Intelligent caching and rate limiting system for LLM operations.
Optimizes AI calls with in-memory caching, TTL management, and rate limiting.
"""

import asyncio
import hashlib
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import os

# Configure logging
logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Types of cache entries for different TTL settings."""

    LTS_RESEARCH = "lts_research"
    BEST_PRACTICES = "best_practices"
    TASK_GENERATION = "task_generation"
    AI_RESPONSE = "ai_response"
    GENERAL = "general"


class RateLimitStatus(Enum):
    """Rate limiting status."""

    OK = "ok"
    APPROACHING_LIMIT = "approaching_limit"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata."""

    key: str
    value: Any
    cache_type: CacheType
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


@dataclass
class RateLimitInfo:
    """Rate limiting information for a provider/model."""

    provider: str
    model: str
    calls_count: int = 0
    first_call_time: Optional[datetime] = None
    last_call_time: Optional[datetime] = None
    reset_time: Optional[datetime] = None
    daily_limit: int = 1000
    minute_limit: int = 60
    status: RateLimitStatus = RateLimitStatus.OK


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_size: int = 0
    total_saved_calls: int = 0
    total_saved_cost: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100


class CacheManager:
    """
    Intelligent cache manager with TTL, rate limiting, and metrics.
    """

    def __init__(self, project_root: Optional[str] = None):
        """Initialize cache manager with configuration."""
        self.cache: Dict[str, CacheEntry] = {}
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.metrics = CacheMetrics()

        # Configuration from environment
        self.ttl_config = self._load_ttl_config()
        self.rate_limit_config = self._load_rate_limit_config()
        self.project_root = project_root or os.getcwd()
        self.cache_dir = os.path.join(self.project_root, ".pytaskai", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.max_cache_size = int(os.getenv("PYTASKAI_MAX_CACHE_SIZE", "1000"))
        self.cleanup_interval = int(
            os.getenv("PYTASKAI_CACHE_CLEANUP_INTERVAL", "300")
        )  # 5 minutes

        # Start background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()

        logger.info(f"CacheManager initialized with max_size={self.max_cache_size}")

    def _load_ttl_config(self) -> Dict[CacheType, int]:
        """Load TTL configuration from environment variables."""
        return {
            CacheType.LTS_RESEARCH: int(
                os.getenv("PYTASKAI_LTS_CACHE_TTL", "86400")
            ),  # 24 hours
            CacheType.BEST_PRACTICES: int(
                os.getenv("PYTASKAI_BP_CACHE_TTL", "43200")
            ),  # 12 hours
            CacheType.TASK_GENERATION: int(
                os.getenv("PYTASKAI_TASK_CACHE_TTL", "3600")
            ),  # 1 hour
            CacheType.AI_RESPONSE: int(
                os.getenv("PYTASKAI_AI_RESPONSE_CACHE_TTL", "1800")
            ),  # 30 minutes
            CacheType.GENERAL: int(
                os.getenv("PYTASKAI_GENERAL_CACHE_TTL", "7200")
            ),  # 2 hours
        }

    def _load_rate_limit_config(self) -> Dict[str, Dict[str, int]]:
        """Load rate limiting configuration from environment variables."""
        return {
            "openai": {
                "daily_limit": int(os.getenv("PYTASKAI_OPENAI_DAILY_LIMIT", "1000")),
                "minute_limit": int(os.getenv("PYTASKAI_OPENAI_MINUTE_LIMIT", "60")),
            },
            "anthropic": {
                "daily_limit": int(os.getenv("PYTASKAI_ANTHROPIC_DAILY_LIMIT", "1000")),
                "minute_limit": int(os.getenv("PYTASKAI_ANTHROPIC_MINUTE_LIMIT", "50")),
            },
            "perplexity": {
                "daily_limit": int(os.getenv("PYTASKAI_PERPLEXITY_DAILY_LIMIT", "500")),
                "minute_limit": int(
                    os.getenv("PYTASKAI_PERPLEXITY_MINUTE_LIMIT", "20")
                ),
            },
            "google": {
                "daily_limit": int(os.getenv("PYTASKAI_GOOGLE_DAILY_LIMIT", "1000")),
                "minute_limit": int(os.getenv("PYTASKAI_GOOGLE_MINUTE_LIMIT", "60")),
            },
            "xai": {
                "daily_limit": int(os.getenv("PYTASKAI_XAI_DAILY_LIMIT", "1000")),
                "minute_limit": int(os.getenv("PYTASKAI_XAI_MINUTE_LIMIT", "30")),
            },
        }

    def _start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            try:
                loop = asyncio.get_event_loop()
                self._cleanup_task = loop.create_task(self._periodic_cleanup())
            except RuntimeError:
                # No event loop running, cleanup will be manual
                logger.info(
                    "No event loop for background cleanup, using manual cleanup"
                )

    async def _periodic_cleanup(self):
        """Periodic cleanup of expired cache entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    def _generate_cache_key(
        self, prompt: str, model: str, cache_type: CacheType, **params
    ) -> str:
        """Generate cache key from prompt, model, and parameters."""
        # Create deterministic key from inputs
        key_data = {
            "prompt": prompt,
            "model": model,
            "cache_type": cache_type.value,
            "params": sorted(params.items()) if params else [],
        }

        key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def get(
        self, prompt: str, model: str, cache_type: CacheType, **params
    ) -> Optional[Any]:
        """
        Get cached result if available and not expired.

        Args:
            prompt: AI prompt
            model: Model name
            cache_type: Type of cache entry
            **params: Additional parameters for cache key

        Returns:
            Cached result or None if not found/expired
        """
        self.metrics.total_requests += 1

        cache_key = self._generate_cache_key(prompt, model, cache_type, **params)

        entry = self.cache.get(cache_key)
        if entry is None:
            self.metrics.cache_misses += 1
            logger.debug(f"Cache miss for key: {cache_key[:8]}...")
            return None

        # Check if expired
        if datetime.now() > entry.expires_at:
            del self.cache[cache_key]
            self.metrics.cache_misses += 1
            logger.debug(f"Cache expired for key: {cache_key[:8]}...")
            return None

        # Update access info
        entry.hit_count += 1
        entry.last_accessed = datetime.now()

        self.metrics.cache_hits += 1
        self.metrics.total_saved_calls += 1

        logger.debug(f"Cache hit for key: {cache_key[:8]}... (hits: {entry.hit_count})")
        return entry.value

    def set(
        self,
        prompt: str,
        model: str,
        cache_type: CacheType,
        value: Any,
        cost_saved: float = 0.0,
        **params,
    ) -> None:
        """
        Store result in cache with TTL.

        Args:
            prompt: AI prompt
            model: Model name
            cache_type: Type of cache entry
            value: Result to cache
            cost_saved: Estimated cost saved by caching
            **params: Additional parameters for cache key
        """
        cache_key = self._generate_cache_key(prompt, model, cache_type, **params)

        # Check cache size limit
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest_entries()

        # Calculate expiry time
        ttl_seconds = self.ttl_config.get(cache_type, 3600)
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            value=value,
            cache_type=cache_type,
            created_at=datetime.now(),
            expires_at=expires_at,
        )

        self.cache[cache_key] = entry
        self.metrics.cache_size = len(self.cache)
        self.metrics.total_saved_cost += cost_saved

        logger.debug(f"Cached result for key: {cache_key[:8]}... (TTL: {ttl_seconds}s)")

    def _evict_oldest_entries(self, evict_count: int = None):
        """Evict oldest cache entries to make space."""
        if evict_count is None:
            evict_count = max(1, len(self.cache) // 10)  # Evict 10% of cache

        # Sort by last_accessed time
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].last_accessed)

        # Remove oldest entries
        for i in range(min(evict_count, len(sorted_entries))):
            key, _ = sorted_entries[i]
            del self.cache[key]
            logger.debug(f"Evicted cache entry: {key[:8]}...")

        self.metrics.cache_size = len(self.cache)

    def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items() if now > entry.expires_at
        ]

        for key in expired_keys:
            del self.cache[key]

        self.metrics.cache_size = len(self.cache)

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def clear_cache(self, cache_type: Optional[CacheType] = None) -> int:
        """
        Clear cache entries.

        Args:
            cache_type: If specified, only clear entries of this type

        Returns:
            Number of entries cleared
        """
        if cache_type is None:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared all cache ({count} entries)")
        else:
            keys_to_remove = [
                key
                for key, entry in self.cache.items()
                if entry.cache_type == cache_type
            ]
            count = len(keys_to_remove)
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(f"Cleared {count} {cache_type.value} cache entries")

        self.metrics.cache_size = len(self.cache)
        return count

    def check_rate_limit(self, provider: str, model: str) -> RateLimitStatus:
        """
        Check rate limiting status for provider/model.

        Args:
            provider: AI provider name
            model: Model name

        Returns:
            Rate limit status
        """
        rate_key = f"{provider}:{model}"

        # Get or create rate limit info
        if rate_key not in self.rate_limits:
            config = self.rate_limit_config.get(provider, {})
            self.rate_limits[rate_key] = RateLimitInfo(
                provider=provider,
                model=model,
                daily_limit=config.get("daily_limit", 1000),
                minute_limit=config.get("minute_limit", 60),
            )

        rate_info = self.rate_limits[rate_key]
        now = datetime.now()

        # Reset counters if it's a new day
        if rate_info.first_call_time and now.date() > rate_info.first_call_time.date():
            rate_info.calls_count = 0
            rate_info.first_call_time = None
            rate_info.reset_time = None

        # Check daily limit
        if rate_info.calls_count >= rate_info.daily_limit:
            rate_info.status = RateLimitStatus.RATE_LIMITED
            env_var = f"PYTASKAI_{provider.upper()}_DAILY_LIMIT"
            logger.warning(
                f"Daily rate limit reached for {rate_key} ({rate_info.calls_count}/{rate_info.daily_limit}). "
                f"To increase limit, set environment variable: {env_var}=<new_limit>"
            )
            return RateLimitStatus.RATE_LIMITED

        # Check minute limit (simple implementation)
        if rate_info.last_call_time:
            time_since_last = (now - rate_info.last_call_time).total_seconds()
            if (
                time_since_last < 60
                and rate_info.calls_count % rate_info.minute_limit == 0
            ):
                rate_info.status = RateLimitStatus.APPROACHING_LIMIT
                env_var = f"PYTASKAI_{provider.upper()}_MINUTE_LIMIT"
                logger.warning(
                    f"Approaching minute rate limit for {rate_key} ({rate_info.minute_limit}/min). "
                    f"To increase limit, set environment variable: {env_var}=<new_limit>"
                )
                return RateLimitStatus.APPROACHING_LIMIT

        # Check if approaching daily limit (90%)
        if rate_info.calls_count >= rate_info.daily_limit * 0.9:
            rate_info.status = RateLimitStatus.APPROACHING_LIMIT
            env_var = f"PYTASKAI_{provider.upper()}_DAILY_LIMIT"
            logger.info(
                f"Approaching daily limit for {rate_key} ({rate_info.calls_count}/{rate_info.daily_limit} = "
                f"{rate_info.calls_count/rate_info.daily_limit*100:.0f}%). "
                f"To increase limit, set: {env_var}=<new_limit>"
            )
            return RateLimitStatus.APPROACHING_LIMIT

        rate_info.status = RateLimitStatus.OK
        return RateLimitStatus.OK

    def record_api_call(self, provider: str, model: str) -> None:
        """
        Record an API call for rate limiting.

        Args:
            provider: AI provider name
            model: Model name
        """
        rate_key = f"{provider}:{model}"

        if rate_key not in self.rate_limits:
            self.check_rate_limit(provider, model)  # Initialize

        rate_info = self.rate_limits[rate_key]
        now = datetime.now()

        if rate_info.first_call_time is None:
            rate_info.first_call_time = now

        rate_info.calls_count += 1
        rate_info.last_call_time = now

        logger.debug(
            f"Recorded API call for {rate_key} (count: {rate_info.calls_count})"
        )

    async def wait_for_rate_limit(self, provider: str, model: str) -> float:
        """
        Wait if necessary due to rate limiting.

        Args:
            provider: AI provider name
            model: Model name

        Returns:
            Seconds waited
        """
        status = self.check_rate_limit(provider, model)

        if status == RateLimitStatus.RATE_LIMITED:
            # Wait until next minute
            wait_time = 60
            logger.info(
                f"Rate limited, waiting {wait_time} seconds for {provider}:{model}"
            )
            await asyncio.sleep(wait_time)
            return wait_time

        elif status == RateLimitStatus.APPROACHING_LIMIT:
            # Small delay to prevent hitting limits
            wait_time = 2.0
            logger.debug(f"Approaching rate limit, waiting {wait_time} seconds")
            await asyncio.sleep(wait_time)
            return wait_time

        return 0.0

    def get_rate_limit_message(self, provider: str, model: str) -> Optional[str]:
        """
        Get user-friendly message for rate limit status with configuration instructions.

        Args:
            provider: AI provider name
            model: Model name

        Returns:
            User-friendly message or None if no rate limiting
        """
        status = self.check_rate_limit(provider, model)
        rate_key = f"{provider}:{model}"

        if rate_key not in self.rate_limits:
            return None

        rate_info = self.rate_limits[rate_key]
        daily_env_var = f"PYTASKAI_{provider.upper()}_DAILY_LIMIT"
        minute_env_var = f"PYTASKAI_{provider.upper()}_MINUTE_LIMIT"

        if status == RateLimitStatus.RATE_LIMITED:
            return (
                f"🚫 Rate limit reached for {provider} ({model})\n"
                f"Daily limit: {rate_info.calls_count}/{rate_info.daily_limit} calls\n"
                f"To increase limit, set environment variable:\n"
                f"export {daily_env_var}=<new_limit>  # e.g., {daily_env_var}=2000\n"
                f"export {minute_env_var}=<new_limit>  # e.g., {minute_env_var}=120\n"
                f"Then restart the application."
            )

        elif status == RateLimitStatus.APPROACHING_LIMIT:
            usage_percent = (rate_info.calls_count / rate_info.daily_limit) * 100
            return (
                f"⚠️  Approaching rate limit for {provider} ({model})\n"
                f"Usage: {rate_info.calls_count}/{rate_info.daily_limit} calls ({usage_percent:.0f}%)\n"
                f"To avoid interruptions, consider increasing limits:\n"
                f"export {daily_env_var}={rate_info.daily_limit * 2}  # Double current limit\n"
                f"export {minute_env_var}={rate_info.minute_limit * 2}  # Double minute limit"
            )

        return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache and rate limiting metrics."""
        return {
            "cache": {
                "total_requests": self.metrics.total_requests,
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "hit_rate": round(self.metrics.hit_rate, 2),
                "cache_size": self.metrics.cache_size,
                "max_cache_size": self.max_cache_size,
                "total_saved_calls": self.metrics.total_saved_calls,
                "total_saved_cost": round(self.metrics.total_saved_cost, 4),
            },
            "rate_limits": {
                rate_key: {
                    "provider": info.provider,
                    "model": info.model,
                    "calls_count": info.calls_count,
                    "daily_limit": info.daily_limit,
                    "minute_limit": info.minute_limit,
                    "status": info.status.value,
                    "usage_percentage": round(
                        (info.calls_count / info.daily_limit) * 100, 2
                    ),
                }
                for rate_key, info in self.rate_limits.items()
            },
            "config": {
                "ttl_config": {ct.value: ttl for ct, ttl in self.ttl_config.items()},
                "cleanup_interval": self.cleanup_interval,
            },
        }

    def get_cache_stats_by_type(self) -> Dict[str, Dict[str, Any]]:
        """Get cache statistics grouped by cache type."""
        stats_by_type = {}

        for cache_type in CacheType:
            entries = [
                entry for entry in self.cache.values() if entry.cache_type == cache_type
            ]

            if entries:
                total_hits = sum(entry.hit_count for entry in entries)
                avg_age = sum(
                    (datetime.now() - entry.created_at).total_seconds()
                    for entry in entries
                ) / len(entries)

                stats_by_type[cache_type.value] = {
                    "entry_count": len(entries),
                    "total_hits": total_hits,
                    "avg_hits_per_entry": round(total_hits / len(entries), 2),
                    "avg_age_seconds": round(avg_age, 2),
                    "ttl_seconds": self.ttl_config[cache_type],
                }
            else:
                stats_by_type[cache_type.value] = {
                    "entry_count": 0,
                    "total_hits": 0,
                    "avg_hits_per_entry": 0,
                    "avg_age_seconds": 0,
                    "ttl_seconds": self.ttl_config[cache_type],
                }

        return stats_by_type

    def shutdown(self):
        """Cleanup and shutdown cache manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()

        self.cache.clear()
        self.rate_limits.clear()
        logger.info("CacheManager shutdown complete")


# Global cache manager instances, one per project root
_cache_managers: Dict[str, CacheManager] = {}


def get_cache_manager(project_root: Optional[str] = None) -> CacheManager:
    """Get a cache manager instance for a specific project root."""
    global _cache_managers

    # Use a default key for global/non-project-specific usage
    key = project_root or "_global_"

    if key not in _cache_managers:
        _cache_managers[key] = CacheManager(project_root)

    return _cache_managers[key]


def shutdown_cache_manager():
    """Shutdown global cache manager."""
    global _cache_manager
    if _cache_manager:
        _cache_manager.shutdown()
        _cache_manager = None
