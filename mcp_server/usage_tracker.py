"""
PyTaskAI - Usage Tracker

Comprehensive tracking system for AI token usage, costs, and analytics.
Provides detailed insights into API usage patterns, costs, and efficiency metrics.
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from .utils import get_usage_directory
from enum import Enum
import hashlib
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of AI operations for categorization."""

    LTS_RESEARCH = "lts_research"
    BEST_PRACTICES = "best_practices"
    TASK_GENERATION = "task_generation"
    TASK_EXPANSION = "task_expansion"
    PRD_PARSING = "prd_parsing"
    CUSTOM_GENERATION = "custom_generation"
    GENERAL = "general"


class CallStatus(Enum):
    """Status of AI calls."""

    SUCCESS = "success"
    FAILED = "failed"
    CACHED = "cached"
    RATE_LIMITED = "rate_limited"


@dataclass
class UsageRecord:
    """Single usage record for an AI call."""

    timestamp: str
    provider: str
    model: str
    operation_type: OperationType
    operation_context: str
    tool_name: Optional[str]
    status: CallStatus

    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Cost tracking
    estimated_cost: float = 0.0
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

    # Performance metrics
    duration_ms: int = 0
    cache_hit: bool = False

    # Error tracking
    error_message: Optional[str] = None

    # Project context
    project_root: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert enums to strings
        data["operation_type"] = self.operation_type.value
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageRecord":
        """Create from dictionary."""
        # Convert string enums back
        data["operation_type"] = OperationType(data["operation_type"])
        data["status"] = CallStatus(data["status"])
        return cls(**data)


@dataclass
class UsageStats:
    """Aggregated usage statistics."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    cached_calls: int = 0
    rate_limited_calls: int = 0

    total_tokens: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    total_cost: float = 0.0
    estimated_monthly_cost: float = 0.0

    avg_duration_ms: float = 0.0
    cache_hit_rate: float = 0.0

    most_used_model: str = ""
    most_expensive_operation: str = ""

    # Breakdown by provider
    provider_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Breakdown by operation type
    operation_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Daily stats for trends
    daily_costs: List[Tuple[str, float]] = field(default_factory=list)
    daily_tokens: List[Tuple[str, int]] = field(default_factory=list)


class UsageTracker:
    """
    Advanced usage tracking system for AI operations.
    """

    def __init__(self, project_root: Optional[str] = None):
        """Initialize usage tracker."""
        self.project_root = project_root or os.getcwd()
        self.usage_dir = get_usage_directory(self.project_root)
        self.usage_file = os.path.join(self.usage_dir, "usage.json")

        # Ensure directory structure
        os.makedirs(self.usage_dir, exist_ok=True)

        # Load existing data
        self.records: List[UsageRecord] = []
        self._load_usage_data()

        # Configuration
        self.max_records = int(os.getenv("PYTASKAI_MAX_USAGE_RECORDS", "10000"))
        self.auto_save = bool(
            os.getenv("PYTASKAI_AUTO_SAVE_USAGE", "true").lower() == "true"
        )

        # Budget settings
        self.daily_budget = float(os.getenv("PYTASKAI_DAILY_BUDGET", "10.0"))
        self.monthly_budget = float(os.getenv("PYTASKAI_MONTHLY_BUDGET", "100.0"))

        logger.info(f"UsageTracker initialized: {len(self.records)} existing records")

    def _load_usage_data(self) -> None:
        """Load usage data from JSON file."""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, "r") as f:
                    data = json.load(f)

                self.records = [
                    UsageRecord.from_dict(record_data)
                    for record_data in data.get("records", [])
                ]

                logger.info(f"Loaded {len(self.records)} usage records")

            except Exception as e:
                logger.error(f"Failed to load usage data: {e}")
                self.records = []
        else:
            logger.info("No existing usage data found, starting fresh")

    def _save_usage_data(self) -> None:
        """Save usage data to JSON file."""
        try:
            # Limit records to max_records (keep most recent)
            if len(self.records) > self.max_records:
                self.records = self.records[-self.max_records :]

            data = {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "project_root": self.project_root,
                "total_records": len(self.records),
                "records": [record.to_dict() for record in self.records],
            }

            # Write to temp file first, then rename (atomic operation)
            temp_file = self.usage_file + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            os.rename(temp_file, self.usage_file)
            logger.debug(f"Saved {len(self.records)} usage records")

        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")

    def record_usage(
        self,
        provider: str,
        model: str,
        operation_type: OperationType,
        operation_context: str,
        status: CallStatus,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        estimated_cost: float = 0.0,
        duration_ms: int = 0,
        cache_hit: bool = False,
        tool_name: Optional[str] = None,
        error_message: Optional[str] = None,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0,
    ) -> None:
        """
        Record a usage event.

        Args:
            provider: AI provider name
            model: Model name
            operation_type: Type of operation
            operation_context: Context description
            status: Call status
            prompt_tokens: Input tokens used
            completion_tokens: Output tokens generated
            estimated_cost: Estimated cost for this call
            duration_ms: Call duration in milliseconds
            cache_hit: Whether result came from cache
            tool_name: MCP tool name if applicable
            error_message: Error message if failed
            cost_per_1k_input: Cost per 1k input tokens
            cost_per_1k_output: Cost per 1k output tokens
        """
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            provider=provider,
            model=model,
            operation_type=operation_type,
            operation_context=operation_context,
            tool_name=tool_name,
            status=status,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost=estimated_cost,
            cost_per_1k_input=cost_per_1k_input,
            cost_per_1k_output=cost_per_1k_output,
            duration_ms=duration_ms,
            cache_hit=cache_hit,
            error_message=error_message,
            project_root=self.project_root,
        )

        self.records.append(record)

        if self.auto_save:
            self._save_usage_data()

        logger.debug(
            f"Recorded usage: {provider}/{model} - {status.value} - {estimated_cost:.4f}"
        )

    def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
        operation_type: Optional[OperationType] = None,
    ) -> UsageStats:
        """
        Get aggregated usage statistics.

        Args:
            start_date: Filter from this date
            end_date: Filter to this date
            provider: Filter by provider
            operation_type: Filter by operation type

        Returns:
            Aggregated usage statistics
        """
        # Filter records
        filtered_records = self.records.copy()

        if start_date:
            filtered_records = [
                r
                for r in filtered_records
                if datetime.fromisoformat(r.timestamp) >= start_date
            ]

        if end_date:
            filtered_records = [
                r
                for r in filtered_records
                if datetime.fromisoformat(r.timestamp) <= end_date
            ]

        if provider:
            filtered_records = [r for r in filtered_records if r.provider == provider]

        if operation_type:
            filtered_records = [
                r for r in filtered_records if r.operation_type == operation_type
            ]

        if not filtered_records:
            return UsageStats()

        # Calculate basic stats
        stats = UsageStats()
        stats.total_calls = len(filtered_records)
        stats.successful_calls = len(
            [r for r in filtered_records if r.status == CallStatus.SUCCESS]
        )
        stats.failed_calls = len(
            [r for r in filtered_records if r.status == CallStatus.FAILED]
        )
        stats.cached_calls = len([r for r in filtered_records if r.cache_hit])
        stats.rate_limited_calls = len(
            [r for r in filtered_records if r.status == CallStatus.RATE_LIMITED]
        )

        # Token stats
        stats.total_tokens = sum(r.total_tokens for r in filtered_records)
        stats.total_prompt_tokens = sum(r.prompt_tokens for r in filtered_records)
        stats.total_completion_tokens = sum(
            r.completion_tokens for r in filtered_records
        )

        # Cost stats
        stats.total_cost = sum(r.estimated_cost for r in filtered_records)

        # Estimate monthly cost based on daily average
        if filtered_records:
            days_span = self._get_days_span(filtered_records)
            if days_span > 0:
                daily_avg = stats.total_cost / days_span
                stats.estimated_monthly_cost = daily_avg * 30

        # Performance stats
        durations = [r.duration_ms for r in filtered_records if r.duration_ms > 0]
        if durations:
            stats.avg_duration_ms = sum(durations) / len(durations)

        if stats.total_calls > 0:
            stats.cache_hit_rate = (stats.cached_calls / stats.total_calls) * 100

        # Find most used model
        model_usage = {}
        for record in filtered_records:
            key = f"{record.provider}/{record.model}"
            model_usage[key] = model_usage.get(key, 0) + 1

        if model_usage:
            stats.most_used_model = max(model_usage, key=model_usage.get)

        # Find most expensive operation
        operation_costs = {}
        for record in filtered_records:
            op = record.operation_type.value
            operation_costs[op] = operation_costs.get(op, 0) + record.estimated_cost

        if operation_costs:
            stats.most_expensive_operation = max(
                operation_costs, key=operation_costs.get
            )

        # Provider breakdown
        stats.provider_breakdown = self._get_provider_breakdown(filtered_records)

        # Operation breakdown
        stats.operation_breakdown = self._get_operation_breakdown(filtered_records)

        # Daily trends
        stats.daily_costs, stats.daily_tokens = self._get_daily_trends(filtered_records)

        return stats

    def _get_days_span(self, records: List[UsageRecord]) -> int:
        """Get number of days spanned by records."""
        if not records:
            return 0

        timestamps = [datetime.fromisoformat(r.timestamp) for r in records]
        min_date = min(timestamps).date()
        max_date = max(timestamps).date()

        return (max_date - min_date).days + 1

    def _get_provider_breakdown(
        self, records: List[UsageRecord]
    ) -> Dict[str, Dict[str, Any]]:
        """Get breakdown by provider."""
        breakdown = {}

        for record in records:
            provider = record.provider
            if provider not in breakdown:
                breakdown[provider] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "models": set(),
                }

            breakdown[provider]["calls"] += 1
            breakdown[provider]["tokens"] += record.total_tokens
            breakdown[provider]["cost"] += record.estimated_cost
            breakdown[provider]["models"].add(record.model)

        # Convert sets to lists for JSON serialization
        for provider_data in breakdown.values():
            provider_data["models"] = list(provider_data["models"])

        return breakdown

    def _get_operation_breakdown(
        self, records: List[UsageRecord]
    ) -> Dict[str, Dict[str, Any]]:
        """Get breakdown by operation type."""
        breakdown = {}

        for record in records:
            op_type = record.operation_type.value
            if op_type not in breakdown:
                breakdown[op_type] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "avg_duration_ms": 0.0,
                    "success_rate": 0.0,
                }

            breakdown[op_type]["calls"] += 1
            breakdown[op_type]["tokens"] += record.total_tokens
            breakdown[op_type]["cost"] += record.estimated_cost

        # Calculate averages and rates
        for op_type, data in breakdown.items():
            op_records = [r for r in records if r.operation_type.value == op_type]

            # Average duration
            durations = [r.duration_ms for r in op_records if r.duration_ms > 0]
            if durations:
                data["avg_duration_ms"] = sum(durations) / len(durations)

            # Success rate
            successful = len([r for r in op_records if r.status == CallStatus.SUCCESS])
            data["success_rate"] = (
                (successful / len(op_records)) * 100 if op_records else 0
            )

        return breakdown

    def _get_daily_trends(
        self, records: List[UsageRecord]
    ) -> Tuple[List[Tuple[str, float]], List[Tuple[str, int]]]:
        """Get daily cost and token trends."""
        daily_costs = {}
        daily_tokens = {}

        for record in records:
            date = datetime.fromisoformat(record.timestamp).date().isoformat()

            daily_costs[date] = daily_costs.get(date, 0) + record.estimated_cost
            daily_tokens[date] = daily_tokens.get(date, 0) + record.total_tokens

        # Sort by date and convert to list of tuples
        cost_trends = sorted(daily_costs.items())
        token_trends = sorted(daily_tokens.items())

        return cost_trends, token_trends

    def check_budget_status(self) -> Dict[str, Any]:
        """Check current budget usage against limits."""
        now = datetime.now()

        # Daily budget check
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_stats = self.get_stats(start_date=today_start)

        # Monthly budget check
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_stats = self.get_stats(start_date=month_start)

        # Calculate percentages
        daily_usage_pct = (
            (daily_stats.total_cost / self.daily_budget) * 100
            if self.daily_budget > 0
            else 0
        )
        monthly_usage_pct = (
            (monthly_stats.total_cost / self.monthly_budget) * 100
            if self.monthly_budget > 0
            else 0
        )

        # Determine status
        daily_status = "ok"
        monthly_status = "ok"

        if daily_usage_pct >= 100:
            daily_status = "exceeded"
        elif daily_usage_pct >= 80:
            daily_status = "warning"

        if monthly_usage_pct >= 100:
            monthly_status = "exceeded"
        elif monthly_usage_pct >= 80:
            monthly_status = "warning"

        return {
            "daily": {
                "budget": self.daily_budget,
                "spent": daily_stats.total_cost,
                "remaining": max(0, self.daily_budget - daily_stats.total_cost),
                "usage_percentage": daily_usage_pct,
                "status": daily_status,
                "calls_made": daily_stats.total_calls,
            },
            "monthly": {
                "budget": self.monthly_budget,
                "spent": monthly_stats.total_cost,
                "remaining": max(0, self.monthly_budget - monthly_stats.total_cost),
                "usage_percentage": monthly_usage_pct,
                "status": monthly_status,
                "calls_made": monthly_stats.total_calls,
            },
            "recommendations": self._get_budget_recommendations(
                daily_status, monthly_status, daily_stats, monthly_stats
            ),
        }

    def _get_budget_recommendations(
        self,
        daily_status: str,
        monthly_status: str,
        daily_stats: UsageStats,
        monthly_stats: UsageStats,
    ) -> List[str]:
        """Get budget recommendations based on current usage."""
        recommendations = []

        if daily_status == "exceeded":
            recommendations.append(
                "🚨 Daily budget exceeded! Consider pausing AI operations or increasing budget."
            )
        elif daily_status == "warning":
            recommendations.append(
                "⚠️ Approaching daily budget limit. Monitor usage carefully."
            )

        if monthly_status == "exceeded":
            recommendations.append(
                "🚨 Monthly budget exceeded! Review usage patterns and adjust limits."
            )
        elif monthly_status == "warning":
            recommendations.append(
                "⚠️ Approaching monthly budget limit. Consider optimizing usage."
            )

        # Efficiency recommendations
        if daily_stats.cache_hit_rate < 30:
            recommendations.append(
                "💡 Low cache hit rate. Enable caching to reduce costs."
            )

        if (
            daily_stats.total_cost > 0
            and daily_stats.successful_calls / daily_stats.total_calls < 0.8
        ):
            recommendations.append(
                "💡 High failure rate. Check API configuration to avoid wasted calls."
            )

        # Model recommendations
        if monthly_stats.most_expensive_operation:
            recommendations.append(
                f"💡 Most expensive operation: {monthly_stats.most_expensive_operation}. Consider optimizing this workflow."
            )

        return recommendations

    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """Export usage data to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.usage_dir, f"usage_export_{timestamp}.csv")

        try:
            import csv

            with open(filename, "w", newline="") as csvfile:
                fieldnames = [
                    "timestamp",
                    "provider",
                    "model",
                    "operation_type",
                    "operation_context",
                    "tool_name",
                    "status",
                    "prompt_tokens",
                    "completion_tokens",
                    "total_tokens",
                    "estimated_cost",
                    "duration_ms",
                    "cache_hit",
                    "error_message",
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for record in self.records:
                    row = record.to_dict()
                    # Convert enums to strings for CSV
                    row["operation_type"] = row["operation_type"]
                    row["status"] = row["status"]
                    writer.writerow(row)

            logger.info(f"Exported {len(self.records)} records to {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            raise

    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """Remove records older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        original_count = len(self.records)
        self.records = [
            record
            for record in self.records
            if datetime.fromisoformat(record.timestamp) >= cutoff_date
        ]

        removed_count = original_count - len(self.records)

        if removed_count > 0:
            self._save_usage_data()
            logger.info(f"Cleaned up {removed_count} old usage records")

        return removed_count

    def get_top_models_by_cost(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Get top models by total cost."""
        model_costs = {}

        for record in self.records:
            model_key = f"{record.provider}/{record.model}"
            model_costs[model_key] = (
                model_costs.get(model_key, 0) + record.estimated_cost
            )

        # Sort by cost and return top N
        sorted_models = sorted(model_costs.items(), key=lambda x: x[1], reverse=True)
        return sorted_models[:limit]

    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """Get efficiency metrics for optimization insights."""
        if not self.records:
            return {}

        total_calls = len(self.records)
        cached_calls = len([r for r in self.records if r.cache_hit])
        successful_calls = len(
            [r for r in self.records if r.status == CallStatus.SUCCESS]
        )

        # Cost efficiency
        total_cost = sum(r.estimated_cost for r in self.records)
        total_tokens = sum(r.total_tokens for r in self.records)

        cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
        cost_per_successful_call = (
            total_cost / successful_calls if successful_calls > 0 else 0
        )

        # Time efficiency
        durations = [r.duration_ms for r in self.records if r.duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "cache_hit_rate": (cached_calls / total_calls) * 100,
            "success_rate": (successful_calls / total_calls) * 100,
            "cost_per_token": cost_per_token,
            "cost_per_successful_call": cost_per_successful_call,
            "avg_call_duration_ms": avg_duration,
            "total_cost_savings_from_cache": self._calculate_cache_savings(),
            "most_efficient_model": self._get_most_efficient_model(),
            "least_efficient_model": self._get_least_efficient_model(),
        }

    def _calculate_cache_savings(self) -> float:
        """Calculate estimated cost savings from cache hits."""
        cache_hits = [r for r in self.records if r.cache_hit]

        # Estimate cost that would have been incurred without cache
        estimated_savings = 0.0
        for record in cache_hits:
            # Use the model's cost rate to estimate what it would have cost
            if record.cost_per_1k_input > 0:
                estimated_cost = (
                    record.prompt_tokens / 1000
                ) * record.cost_per_1k_input
                estimated_cost += (
                    record.completion_tokens / 1000
                ) * record.cost_per_1k_output
                estimated_savings += estimated_cost

        return estimated_savings

    def _get_most_efficient_model(self) -> str:
        """Get the most cost-efficient model (lowest cost per token)."""
        model_efficiency = {}

        for record in self.records:
            if record.status == CallStatus.SUCCESS and record.total_tokens > 0:
                model_key = f"{record.provider}/{record.model}"
                if model_key not in model_efficiency:
                    model_efficiency[model_key] = {"cost": 0, "tokens": 0}

                model_efficiency[model_key]["cost"] += record.estimated_cost
                model_efficiency[model_key]["tokens"] += record.total_tokens

        # Calculate cost per token for each model
        efficiency_ratios = {}
        for model, data in model_efficiency.items():
            if data["tokens"] > 0:
                efficiency_ratios[model] = data["cost"] / data["tokens"]

        if efficiency_ratios:
            return min(efficiency_ratios, key=efficiency_ratios.get)

        return "Unknown"

    def _get_least_efficient_model(self) -> str:
        """Get the least cost-efficient model (highest cost per token)."""
        model_efficiency = {}

        for record in self.records:
            if record.status == CallStatus.SUCCESS and record.total_tokens > 0:
                model_key = f"{record.provider}/{record.model}"
                if model_key not in model_efficiency:
                    model_efficiency[model_key] = {"cost": 0, "tokens": 0}

                model_efficiency[model_key]["cost"] += record.estimated_cost
                model_efficiency[model_key]["tokens"] += record.total_tokens

        # Calculate cost per token for each model
        efficiency_ratios = {}
        for model, data in model_efficiency.items():
            if data["tokens"] > 0:
                efficiency_ratios[model] = data["cost"] / data["tokens"]

        if efficiency_ratios:
            return max(efficiency_ratios, key=efficiency_ratios.get)

        return "Unknown"


# Global usage tracker instances, one per project root
_usage_trackers: Dict[str, UsageTracker] = {}


def get_usage_tracker(project_root: Optional[str] = None) -> UsageTracker:
    """Get a usage tracker instance for a specific project root."""
    global _usage_trackers

    key = project_root or "_global_"

    if key not in _usage_trackers:
        _usage_trackers[key] = UsageTracker(project_root)

    return _usage_trackers[key]


def record_ai_usage(
    provider: str,
    model: str,
    operation_type: OperationType,
    operation_context: str,
    status: CallStatus,
    project_root: Optional[str] = None,
    **kwargs,
) -> None:
    """Convenience function to record AI usage."""
    tracker = get_usage_tracker(project_root)
    tracker.record_usage(
        provider=provider,
        model=model,
        operation_type=operation_type,
        operation_context=operation_context,
        status=status,
        **kwargs,
    )


# Export main classes and functions
__all__ = [
    "UsageTracker",
    "UsageRecord",
    "UsageStats",
    "OperationType",
    "CallStatus",
    "get_usage_tracker",
    "record_ai_usage",
]
