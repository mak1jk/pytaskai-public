"""
PyTaskAI - Additional Schemas and Types

Extended schemas for advanced features like Kanban UI, analytics, and collaboration.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

from .models import TaskStatus, TaskPriority, Task


# =============================================================================
# KANBAN UI MODELS
# =============================================================================


class KanbanColumn(BaseModel):
    """Kanban board column definition"""

    id: str = Field(..., description="Unique identifier for the column")
    title: str = Field(..., description="Display title for the column")
    status: TaskStatus = Field(..., description="Task status this column represents")
    color: str = Field(default="#f0f0f0", description="Background color for the column")
    max_tasks: Optional[int] = Field(
        default=None, ge=1, description="Maximum number of tasks allowed in this column"
    )
    order: int = Field(default=0, description="Display order of the column")


class KanbanBoard(BaseModel):
    """Complete Kanban board configuration"""

    id: str = Field(..., description="Unique identifier for the board")
    name: str = Field(..., description="Display name for the board")
    description: Optional[str] = Field(default=None, description="Board description")
    columns: List[KanbanColumn] = Field(..., description="List of columns in the board")
    task_filters: Dict[str, Any] = Field(
        default_factory=dict, description="Active filters for tasks"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TaskCardData(BaseModel):
    """Data for rendering task cards in Kanban UI"""

    task: Task = Field(..., description="The task data")
    subtask_summary: Dict[str, int] = Field(
        default_factory=dict, description="Summary of subtask statuses"
    )
    dependency_status: Dict[str, str] = Field(
        default_factory=dict, description="Status of task dependencies"
    )
    urgency_score: Optional[float] = Field(
        default=None, description="Calculated urgency score"
    )
    assignee: Optional[str] = Field(default=None, description="Assigned user")
    tags: List[str] = Field(default_factory=list, description="Task tags")


# =============================================================================
# ANALYTICS MODELS
# =============================================================================


class TimeSeriesDataPoint(BaseModel):
    """Single data point for time series analytics"""

    timestamp: datetime = Field(..., description="Timestamp for this data point")
    value: float = Field(..., description="Numeric value")
    label: Optional[str] = Field(
        default=None, description="Optional label for this point"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class VelocityMetrics(BaseModel):
    """Team/project velocity metrics"""

    period_start: date = Field(..., description="Start of the measurement period")
    period_end: date = Field(..., description="End of the measurement period")
    tasks_completed: int = Field(
        ..., ge=0, description="Number of tasks completed in period"
    )
    story_points_completed: Optional[float] = Field(
        default=None, ge=0, description="Story points completed"
    )
    average_cycle_time_hours: Optional[float] = Field(
        default=None, ge=0, description="Average time from start to completion"
    )
    throughput_per_day: float = Field(
        ..., ge=0, description="Average tasks completed per day"
    )
    predicted_completion_date: Optional[date] = Field(
        default=None, description="Predicted project completion date"
    )

    class Config:
        json_encoders = {date: lambda v: v.isoformat()}


class BurndownData(BaseModel):
    """Burndown chart data"""

    project_name: str = Field(..., description="Name of the project")
    start_date: date = Field(..., description="Project start date")
    target_end_date: date = Field(..., description="Target completion date")
    total_tasks: int = Field(..., ge=0, description="Total number of tasks in project")
    daily_progress: List[TimeSeriesDataPoint] = Field(
        ..., description="Daily progress data points"
    )
    ideal_burndown: List[TimeSeriesDataPoint] = Field(
        ..., description="Ideal burndown line"
    )
    actual_burndown: List[TimeSeriesDataPoint] = Field(
        ..., description="Actual progress line"
    )

    class Config:
        json_encoders = {date: lambda v: v.isoformat()}


class ProjectInsights(BaseModel):
    """AI-generated project insights and recommendations"""

    generated_at: datetime = Field(
        default_factory=datetime.now, description="When insights were generated"
    )
    project_health_score: float = Field(
        ..., ge=0, le=100, description="Overall project health score"
    )
    velocity_trend: str = Field(
        ..., description="Velocity trend analysis (improving/declining/stable)"
    )
    bottlenecks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Identified bottlenecks"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="AI recommendations for improvement"
    )
    risk_factors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Identified risk factors"
    )
    predicted_delays: List[Dict[str, Any]] = Field(
        default_factory=list, description="Predicted task delays"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# COLLABORATION MODELS
# =============================================================================


class UserRole(str, Enum):
    """User roles for collaboration features"""

    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class User(BaseModel):
    """User model for collaboration"""

    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="Full display name")
    role: UserRole = Field(default=UserRole.DEVELOPER, description="User role")
    avatar_url: Optional[str] = Field(
        default=None, description="URL to user avatar image"
    )
    is_active: bool = Field(default=True, description="Whether the user is active")
    created_at: datetime = Field(default_factory=datetime.now)
    last_seen: Optional[datetime] = Field(
        default=None, description="Last activity timestamp"
    )

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class TaskAssignment(BaseModel):
    """Task assignment model"""

    task_id: int = Field(..., description="ID of the assigned task")
    user_id: str = Field(..., description="ID of the assigned user")
    assigned_by: str = Field(..., description="ID of the user who made the assignment")
    assigned_at: datetime = Field(default_factory=datetime.now)
    due_date: Optional[datetime] = Field(
        default=None, description="Due date for the assignment"
    )
    notes: Optional[str] = Field(default=None, description="Assignment notes")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Comment(BaseModel):
    """Comment model for tasks and subtasks"""

    id: str = Field(..., description="Unique comment identifier")
    task_id: int = Field(..., description="ID of the task this comment belongs to")
    subtask_id: Optional[int] = Field(
        default=None, description="ID of the subtask if applicable"
    )
    user_id: str = Field(..., description="ID of the user who made the comment")
    content: str = Field(..., min_length=1, description="Comment content")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(
        default=None, description="Last edit timestamp"
    )
    parent_comment_id: Optional[str] = Field(
        default=None, description="ID of parent comment for replies"
    )
    mentions: List[str] = Field(
        default_factory=list, description="List of mentioned user IDs"
    )
    attachments: List[str] = Field(
        default_factory=list, description="List of attachment URLs"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ActivityEvent(BaseModel):
    """Activity feed event"""

    id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(
        ..., description="Type of event (task_created, status_changed, etc.)"
    )
    user_id: str = Field(..., description="ID of the user who triggered the event")
    task_id: Optional[int] = Field(default=None, description="Related task ID")
    description: str = Field(..., description="Human-readable event description")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional event data"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# INTEGRATION MODELS
# =============================================================================


class GitHubIntegration(BaseModel):
    """GitHub integration configuration"""

    repository_url: str = Field(..., description="GitHub repository URL")
    access_token: str = Field(..., description="GitHub access token")
    default_branch: str = Field(default="main", description="Default branch name")
    auto_create_issues: bool = Field(
        default=False, description="Automatically create GitHub issues for tasks"
    )
    sync_commits: bool = Field(
        default=True, description="Sync commit messages with task progress"
    )
    webhook_url: Optional[str] = Field(
        default=None, description="Webhook URL for GitHub events"
    )


class SlackIntegration(BaseModel):
    """Slack integration configuration"""

    bot_token: str = Field(..., description="Slack bot token")
    channel_id: str = Field(..., description="Default Slack channel ID")
    notify_on_completion: bool = Field(
        default=True, description="Send notifications when tasks are completed"
    )
    notify_on_assignment: bool = Field(
        default=True, description="Send notifications when tasks are assigned"
    )
    daily_summary: bool = Field(default=False, description="Send daily project summary")


# =============================================================================
# EXPORT/IMPORT MODELS
# =============================================================================


class ExportFormat(str, Enum):
    """Export format options"""

    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    MARKDOWN = "markdown"


class ExportRequest(BaseModel):
    """Request for exporting task data"""

    format: ExportFormat = Field(..., description="Export format")
    task_ids: Optional[List[int]] = Field(
        default=None, description="Specific task IDs to export (all if None)"
    )
    include_subtasks: bool = Field(
        default=True, description="Include subtasks in export"
    )
    include_comments: bool = Field(
        default=False, description="Include comments in export"
    )
    include_analytics: bool = Field(default=False, description="Include analytics data")
    date_range: Optional[Dict[str, str]] = Field(
        default=None, description="Date range filter"
    )

    class Config:
        use_enum_values = True


class ImportRequest(BaseModel):
    """Request for importing task data"""

    format: ExportFormat = Field(..., description="Import format")
    data: Union[str, Dict[str, Any], List[Dict[str, Any]]] = Field(
        ..., description="Data to import"
    )
    merge_strategy: str = Field(
        default="append",
        description="How to handle existing tasks (append/replace/merge)",
    )
    validate_dependencies: bool = Field(
        default=True, description="Validate task dependencies during import"
    )

    class Config:
        use_enum_values = True


# =============================================================================
# SEARCH AND FILTERING MODELS
# =============================================================================


class TaskFilter(BaseModel):
    """Advanced task filtering options"""

    status: Optional[List[TaskStatus]] = Field(
        default=None, description="Filter by status"
    )
    priority: Optional[List[TaskPriority]] = Field(
        default=None, description="Filter by priority"
    )
    assignee: Optional[List[str]] = Field(
        default=None, description="Filter by assigned user"
    )
    created_after: Optional[datetime] = Field(
        default=None, description="Filter by creation date"
    )
    created_before: Optional[datetime] = Field(
        default=None, description="Filter by creation date"
    )
    due_after: Optional[datetime] = Field(
        default=None, description="Filter by due date"
    )
    due_before: Optional[datetime] = Field(
        default=None, description="Filter by due date"
    )
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    search_text: Optional[str] = Field(
        default=None, description="Full-text search in title/description"
    )
    has_subtasks: Optional[bool] = Field(
        default=None, description="Filter tasks with/without subtasks"
    )
    complexity_min: Optional[int] = Field(
        default=None, ge=1, le=10, description="Minimum complexity score"
    )
    complexity_max: Optional[int] = Field(
        default=None, ge=1, le=10, description="Maximum complexity score"
    )

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class SearchResult(BaseModel):
    """Search result model"""

    tasks: List[Task] = Field(..., description="Matching tasks")
    total_count: int = Field(..., description="Total number of matching tasks")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Number of results per page")
    filters_applied: TaskFilter = Field(..., description="Filters that were applied")
    search_time_ms: float = Field(
        ..., description="Search execution time in milliseconds"
    )
