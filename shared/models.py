"""
PyTaskAI - Shared Pydantic Models

This module contains all Pydantic models used across the PyTaskAI system,
including core data models and MCP tool request/response schemas.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================


class TaskStatus(str, Enum):
    """Task status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration"""

    HIGHEST = "highest"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    LOWEST = "lowest"


class TaskType(str, Enum):
    """Task type enumeration"""

    TASK = "task"
    BUG = "bug"
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"


class BugSeverity(str, Enum):
    """Bug severity enumeration"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AIModelProvider(str, Enum):
    """AI model provider enumeration"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GOOGLE = "google"
    MISTRAL = "mistral"
    XAI = "xai"
    OPENROUTER = "openrouter"
    AZURE = "azure"
    OLLAMA = "ollama"


# =============================================================================
# CORE DATA MODELS
# =============================================================================


class SubTask(BaseModel):
    """SubTask model for task breakdown"""

    id: int = Field(..., description="Unique identifier for subtask within parent task")
    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Brief descriptive title for the subtask",
    )
    description: str = Field(
        ..., min_length=10, description="Detailed description of what needs to be done"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current status of the subtask"
    )
    details: str = Field(default="", description="Implementation details and notes")
    test_strategy: str = Field(
        default="", description="How to verify the subtask is completed correctly"
    )
    dependencies: List[Union[int, str]] = Field(
        default_factory=list,
        description="IDs of tasks/subtasks this depends on (e.g., [1, '2.1'])",
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the subtask was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="When the subtask was last modified"
    )
    estimated_hours: Optional[float] = Field(
        default=None, ge=0, description="Estimated hours to complete"
    )
    actual_hours: Optional[float] = Field(
        default=None, ge=0, description="Actual hours spent"
    )

    @field_validator("updated_at", mode="before")
    @classmethod
    def set_updated_at(cls, v):
        return v or datetime.now()

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class Task(BaseModel):
    """Main Task model"""

    id: int = Field(..., description="Unique identifier for the task")
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Brief descriptive title for the task",
    )
    description: str = Field(
        ...,
        min_length=10,
        description="Detailed description of what needs to be accomplished",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current status of the task"
    )
    dependencies: List[int] = Field(
        default_factory=list,
        description="List of task IDs that must be completed first",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="Priority level of the task"
    )
    details: str = Field(
        default="", description="Implementation details, notes, and specifications"
    )
    test_strategy: str = Field(
        default="", description="How to verify the task is completed correctly"
    )
    subtasks: List[SubTask] = Field(
        default_factory=list, description="List of subtasks for detailed breakdown"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the task was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="When the task was last modified"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When the task was completed"
    )

    # Estimation and tracking
    estimated_hours: Optional[float] = Field(
        default=None, ge=0, description="Estimated hours to complete"
    )
    actual_hours: Optional[float] = Field(
        default=None, ge=0, description="Actual hours spent"
    )
    complexity_score: Optional[int] = Field(
        default=None, ge=1, le=10, description="AI-assessed complexity score (1-10)"
    )

    # Task type and bug-specific fields
    type: TaskType = Field(
        default=TaskType.TASK, description="Type of task (task, bug, feature, etc.)"
    )

    # Bug-specific fields (only relevant when type=BUG)
    severity: Optional[BugSeverity] = Field(
        default=None, description="Bug severity level (only for bugs)"
    )
    steps_to_reproduce: Optional[str] = Field(
        default=None, description="Steps to reproduce the bug (only for bugs)"
    )
    expected_result: Optional[str] = Field(
        default=None, description="Expected behavior (only for bugs)"
    )
    actual_result: Optional[str] = Field(
        default=None, description="Actual behavior observed (only for bugs)"
    )
    environment: Optional[str] = Field(
        default=None, description="Environment where bug occurs (only for bugs)"
    )
    attachments: List[str] = Field(
        default_factory=list, description="List of attachment URLs or file paths"
    )

    # Test coverage fields
    target_test_coverage: Optional[float] = Field(
        default=None, ge=0, le=100, description="Target test coverage percentage"
    )
    achieved_test_coverage: Optional[float] = Field(
        default=None, ge=0, le=100, description="Achieved test coverage percentage"
    )
    test_report_url: Optional[str] = Field(
        default=None, description="URL to test coverage report"
    )
    related_tests: List[str] = Field(
        default_factory=list, description="List of related test files or test names"
    )

    # AI generation metadata
    generated_by_ai: bool = Field(
        default=False, description="Whether this task was generated by AI"
    )
    ai_model_used: Optional[str] = Field(
        default=None, description="Which AI model was used for generation"
    )
    research_used: bool = Field(
        default=False, description="Whether research mode was used during generation"
    )

    @field_validator("created_at", "updated_at", "completed_at", mode="before")
    @classmethod
    def parse_datetime_fields(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now()
        if isinstance(v, datetime):
            return v
        return datetime.now()

    @field_validator("updated_at", mode="before")
    @classmethod
    def set_updated_at(cls, v):
        if v is None:
            return datetime.now()
        return v

    @field_validator("completed_at", mode="before")
    @classmethod
    def validate_completed_at(cls, v):
        # Note: Cross-field validation moved to model_validator if needed
        return v

    def get_total_subtasks(self) -> int:
        """Get total number of subtasks"""
        return len(self.subtasks)

    def get_completed_subtasks(self) -> int:
        """Get number of completed subtasks"""
        return len([st for st in self.subtasks if st.status == TaskStatus.DONE])

    def get_completion_percentage(self) -> float:
        """Calculate completion percentage based on subtasks"""
        if not self.subtasks:
            return 100.0 if self.status == TaskStatus.DONE else 0.0
        return (self.get_completed_subtasks() / self.get_total_subtasks()) * 100

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# MCP TOOL REQUEST MODELS
# =============================================================================


class AddTaskRequest(BaseModel):
    """Request model for add_task MCP tool"""

    prompt: str = Field(
        ..., min_length=10, description="Description of the task to create"
    )
    dependencies: List[int] = Field(
        default_factory=list, description="List of task IDs this task depends on"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="Priority level for the new task"
    )
    type: TaskType = Field(
        default=TaskType.TASK, description="Type of task (task, bug, feature, etc.)"
    )
    use_research: bool = Field(
        default=False,
        description="Enable AI research mode for enhanced task generation",
    )
    use_lts_deps: bool = Field(
        default=True,
        description="Prefer LTS versions for dependencies (True) or latest versions (False)",
    )
    estimated_hours: Optional[float] = Field(
        default=None, ge=0, description="Estimated hours to complete"
    )

    # Bug-specific fields (only used when type=BUG)
    severity: Optional[BugSeverity] = Field(
        default=None, description="Bug severity level (only for bugs)"
    )
    steps_to_reproduce: Optional[str] = Field(
        default=None, description="Steps to reproduce the bug (only for bugs)"
    )
    expected_result: Optional[str] = Field(
        default=None, description="Expected behavior (only for bugs)"
    )
    actual_result: Optional[str] = Field(
        default=None, description="Actual behavior observed (only for bugs)"
    )
    environment: Optional[str] = Field(
        default=None, description="Environment where bug occurs (only for bugs)"
    )

    # Test coverage fields
    target_test_coverage: Optional[float] = Field(
        default=None, ge=0, le=100, description="Target test coverage percentage"
    )
    related_tests: List[str] = Field(
        default_factory=list, description="List of related test files or test names"
    )

    class Config:
        use_enum_values = True


class ExpandTaskRequest(BaseModel):
    """Request model for expand_task MCP tool"""

    task_id: int = Field(..., description="ID of the task to expand into subtasks")
    num_subtasks: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Target number of subtasks (uses complexity analysis if not specified)",
    )
    use_research: bool = Field(
        default=False,
        description="Enable AI research mode for enhanced subtask generation",
    )
    use_lts_deps: bool = Field(
        default=True, description="Prefer LTS versions for dependencies"
    )
    additional_context: Optional[str] = Field(
        default=None,
        description="Additional context or requirements for subtask generation",
    )
    force: bool = Field(
        default=False,
        description="Force regeneration of subtasks even if they already exist",
    )

    class Config:
        use_enum_values = True


class UpdateSubtaskRequest(BaseModel):
    """Request model for update_subtask MCP tool"""

    parent_task_id: int = Field(..., description="ID of the parent task")
    subtask_id: int = Field(
        ..., description="ID of the subtask to update (relative to parent)"
    )
    update_prompt: str = Field(
        ..., min_length=5, description="Description of changes or additions to make"
    )
    use_research: bool = Field(
        default=False, description="Enable AI research mode for enhanced updates"
    )
    use_lts_deps: bool = Field(
        default=True, description="Prefer LTS versions for any new dependencies"
    )

    class Config:
        use_enum_values = True


class SetTaskStatusRequest(BaseModel):
    """Request model for set_task_status MCP tool"""

    task_ids: Union[int, List[int]] = Field(
        ..., description="Task ID or list of task IDs to update"
    )
    subtask_ids: Optional[List[str]] = Field(
        default=None, description="Subtask IDs in format 'parent_id.subtask_id'"
    )
    status: TaskStatus = Field(..., description="New status to set")
    completion_notes: Optional[str] = Field(
        default=None, description="Notes about the completion or status change"
    )

    @field_validator("task_ids", mode="before")
    @classmethod
    def normalize_task_ids(cls, v):
        if isinstance(v, int):
            return [v]
        return v

    class Config:
        use_enum_values = True


class NextTaskRequest(BaseModel):
    """Request model for next_task MCP tool"""

    current_task_id: Optional[int] = Field(
        default=None, description="Current task ID to find next from"
    )
    priority_filter: Optional[List[TaskPriority]] = Field(
        default=None, description="Filter by priority levels"
    )
    status_filter: Optional[List[TaskStatus]] = Field(
        default=None, description="Filter by status"
    )
    exclude_blocked: bool = Field(
        default=True, description="Exclude tasks with incomplete dependencies"
    )

    class Config:
        use_enum_values = True


class AnalyzeComplexityRequest(BaseModel):
    """Request model for analyze_complexity MCP tool"""

    task_id: Optional[int] = Field(
        default=None, description="Specific task ID to analyze (analyzes all if None)"
    )
    task_ids: Optional[List[int]] = Field(
        default=None, description="List of specific task IDs to analyze"
    )
    use_research: bool = Field(
        default=False,
        description="Enable AI research mode for more accurate complexity analysis",
    )
    threshold: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Complexity threshold for expansion recommendations",
    )

    class Config:
        use_enum_values = True


# =============================================================================
# DEPENDENCY MANAGEMENT MODELS
# =============================================================================


class DependencyRequest(BaseModel):
    """Request model for dependency management tools"""

    task_id: int = Field(
        ..., description="ID of the task that will have the dependency"
    )
    depends_on_task_id: int = Field(
        ..., description="ID of the task that must be completed first"
    )

    @field_validator("depends_on_task_id", mode="before")
    @classmethod
    def validate_no_self_dependency(cls, v):
        # Note: Cross-field validation moved to model_validator if needed
        return v


class ValidationReport(BaseModel):
    """Report model for dependency validation"""

    is_valid: bool = Field(..., description="Whether the dependency structure is valid")
    issues_found: List[str] = Field(
        default_factory=list, description="List of validation issues found"
    )
    circular_dependencies: List[List[int]] = Field(
        default_factory=list,
        description="Lists of task IDs forming circular dependencies",
    )
    missing_dependencies: List[Dict[str, int]] = Field(
        default_factory=list, description="Dependencies pointing to non-existent tasks"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations to fix issues"
    )


# =============================================================================
# COMPLEXITY ANALYSIS MODELS
# =============================================================================


class ComplexityReport(BaseModel):
    """Report model for task complexity analysis"""

    task_id: int = Field(..., description="ID of the analyzed task")
    complexity_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Complexity score from 1 (simple) to 10 (very complex)",
    )
    reasoning: str = Field(
        ...,
        min_length=20,
        description="Detailed explanation of the complexity assessment",
    )
    recommended_subtasks: int = Field(
        ...,
        ge=1,
        le=20,
        description="Recommended number of subtasks for this complexity level",
    )
    key_complexity_factors: List[str] = Field(
        default_factory=list, description="Main factors contributing to complexity"
    )
    estimated_hours: Optional[float] = Field(
        default=None, ge=0, description="Estimated hours based on complexity"
    )
    risk_factors: List[str] = Field(
        default_factory=list, description="Potential risks or challenges identified"
    )
    similar_tasks: List[int] = Field(
        default_factory=list, description="IDs of similar tasks for reference"
    )

    # AI analysis metadata
    analyzed_by_model: Optional[str] = Field(
        default=None, description="AI model used for analysis"
    )
    research_used: bool = Field(
        default=False, description="Whether research mode was used"
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="When the analysis was performed"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ProjectComplexityReport(BaseModel):
    """Overall project complexity analysis"""

    total_tasks: int = Field(..., description="Total number of tasks analyzed")
    average_complexity: float = Field(
        ..., ge=1, le=10, description="Average complexity score across all tasks"
    )
    complexity_distribution: Dict[int, int] = Field(
        default_factory=dict, description="Distribution of complexity scores"
    )
    high_complexity_tasks: List[int] = Field(
        default_factory=list, description="Task IDs with complexity >= threshold"
    )
    expansion_recommendations: List[int] = Field(
        default_factory=list, description="Task IDs recommended for expansion"
    )
    total_estimated_hours: Optional[float] = Field(
        default=None, ge=0, description="Total estimated project hours"
    )
    critical_path_tasks: List[int] = Field(
        default_factory=list, description="Task IDs on the critical path"
    )

    # Metadata
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="When the analysis was performed"
    )
    threshold_used: int = Field(
        default=5, description="Complexity threshold used for recommendations"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# USAGE TRACKING MODELS
# =============================================================================


class AIUsageRecord(BaseModel):
    """Record of AI API usage for cost tracking"""

    id: Optional[str] = Field(
        default=None, description="Unique identifier for this usage record"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the API call was made"
    )
    model: str = Field(
        ..., description="AI model used (e.g., 'gpt-4o-mini', 'claude-3-haiku')"
    )
    provider: AIModelProvider = Field(..., description="AI provider")
    operation_type: str = Field(
        ...,
        description="Type of operation (e.g., 'task_generation', 'lts_search', 'best_practices')",
    )

    # Token usage
    input_tokens: int = Field(..., ge=0, description="Number of input tokens used")
    output_tokens: int = Field(
        ..., ge=0, description="Number of output tokens generated"
    )
    total_tokens: int = Field(..., ge=0, description="Total tokens used")

    # Cost tracking
    cost_usd: float = Field(..., ge=0, description="Cost in USD for this API call")

    # Performance metrics
    duration_ms: float = Field(
        ..., ge=0, description="Duration of the API call in milliseconds"
    )
    success: bool = Field(
        default=True, description="Whether the API call was successful"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if the call failed"
    )

    # Context
    task_id: Optional[int] = Field(
        default=None, description="Task ID associated with this usage"
    )
    user_id: Optional[str] = Field(
        default=None, description="User ID who initiated the operation"
    )
    cache_hit: bool = Field(
        default=False, description="Whether this was served from cache"
    )

    @field_validator("total_tokens", mode="before")
    @classmethod
    def validate_total_tokens(cls, v):
        # Note: Cross-field validation moved to model_validator if needed
        return v

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UsageSummary(BaseModel):
    """Summary of AI usage and costs"""

    period_start: datetime = Field(..., description="Start of the summary period")
    period_end: datetime = Field(..., description="End of the summary period")
    total_calls: int = Field(..., ge=0, description="Total number of API calls")
    total_tokens: int = Field(..., ge=0, description="Total tokens used")
    total_cost_usd: float = Field(..., ge=0, description="Total cost in USD")

    # Breakdown by model
    by_model: Dict[str, Dict[str, Union[int, float]]] = Field(
        default_factory=dict, description="Usage breakdown by model"
    )
    by_operation: Dict[str, Dict[str, Union[int, float]]] = Field(
        default_factory=dict, description="Usage breakdown by operation type"
    )

    # Performance metrics
    average_duration_ms: float = Field(
        ..., ge=0, description="Average API call duration"
    )
    success_rate: float = Field(
        ..., ge=0, le=100, description="Success rate percentage"
    )
    cache_hit_rate: float = Field(
        ..., ge=0, le=100, description="Cache hit rate percentage"
    )

    # Budget tracking
    daily_budget_usd: Optional[float] = Field(
        default=None, ge=0, description="Daily budget limit"
    )
    monthly_budget_usd: Optional[float] = Field(
        default=None, ge=0, description="Monthly budget limit"
    )
    budget_utilization_percent: Optional[float] = Field(
        default=None, ge=0, description="Percentage of budget used"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class TaskResponse(BaseModel):
    """Standard response model for task operations"""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message about the operation")
    task: Optional[Task] = Field(
        default=None, description="The task data if applicable"
    )
    tasks: Optional[List[Task]] = Field(
        default=None, description="List of tasks if applicable"
    )
    error_code: Optional[str] = Field(
        default=None, description="Error code if the operation failed"
    )


class MCPToolResponse(BaseModel):
    """Generic response model for MCP tools"""

    success: bool = Field(..., description="Whether the tool execution was successful")
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool-specific response data"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if the tool failed"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata about the operation"
    )
