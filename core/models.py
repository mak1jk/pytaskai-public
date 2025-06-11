"""
PyTaskAI Core Domain Models

Pure domain models without infrastructure dependencies.
These models represent the core business entities of the PyTaskAI system.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from .exceptions import ValidationError


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"  
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOWEST = "lowest"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HIGHEST = "highest"


class TaskType(str, Enum):
    """Task type enumeration."""
    TASK = "task"
    BUG = "bug"
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"


class BugSeverity(str, Enum):
    """Bug severity enumeration."""
    TRIVIAL = "trivial"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"
    BLOCKER = "blocker"


class AIModelProvider(str, Enum):
    """AI model provider enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GOOGLE = "google"
    XAI = "xai"


# Value Objects

class TaskMetadata(BaseModel):
    """Task metadata value object."""
    complexity_score: Optional[int] = Field(None, ge=1, le=10)
    estimated_hours: Optional[float] = Field(None, gt=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    tags: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    
    @validator('tags', 'labels')
    def validate_string_lists(cls, v):
        if not all(isinstance(item, str) for item in v):
            raise ValidationError("All tags and labels must be strings")
        return v


class TestCoverage(BaseModel):
    """Test coverage information."""
    target_coverage: Optional[int] = Field(None, ge=0, le=100)
    achieved_coverage: Optional[int] = Field(None, ge=0, le=100)
    related_test_files: List[str] = Field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None
    
    @validator('target_coverage', 'achieved_coverage')
    def validate_percentage(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValidationError("Coverage percentage must be between 0 and 100")
        return v


class BugDetails(BaseModel):
    """Bug-specific details."""
    severity: Optional[BugSeverity] = None
    environment: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    version: Optional[str] = None
    
    class Config:
        use_enum_values = True


# Domain Entities

class SubTask(BaseModel):
    """Subtask entity."""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    test_strategy: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
    
    def set_updated_at(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    def mark_completed(self) -> None:
        """Mark subtask as completed."""
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now()
        self.set_updated_at()


class Task(BaseModel):
    """Main task entity."""
    id: int
    title: str
    description: str = ""
    type: TaskType = TaskType.TASK
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[int] = Field(default_factory=list)
    subtasks: List[SubTask] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Additional fields
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    test_strategy: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    
    # Bug-specific fields
    severity: Optional[BugSeverity] = None
    environment: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    
    # Test coverage fields
    target_test_coverage: Optional[int] = Field(None, ge=0, le=100)
    achieved_test_coverage: Optional[int] = Field(None, ge=0, le=100)
    related_test_files: List[str] = Field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None
    
    # Metadata
    metadata: TaskMetadata = Field(default_factory=TaskMetadata)
    
    class Config:
        use_enum_values = True
    
    @validator('dependencies')
    def validate_dependencies(cls, v, values):
        """Validate dependencies don't include self-reference."""
        task_id = values.get('id')
        if task_id and task_id in v:
            raise ValidationError(f"Task cannot depend on itself: {task_id}")
        return v
    
    @validator('target_test_coverage', 'achieved_test_coverage')
    def validate_coverage_percentage(cls, v):
        """Validate test coverage is a valid percentage."""
        if v is not None and not (0 <= v <= 100):
            raise ValidationError("Test coverage must be between 0 and 100")
        return v
    
    def set_updated_at(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now()
        self.set_updated_at()
    
    def add_dependency(self, task_id: int) -> None:
        """Add a dependency to this task."""
        if task_id == self.id:
            raise ValidationError(f"Task cannot depend on itself: {task_id}")
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.set_updated_at()
    
    def remove_dependency(self, task_id: int) -> bool:
        """Remove a dependency from this task."""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self.set_updated_at()
            return True
        return False
    
    def get_total_subtasks(self) -> int:
        """Get total number of subtasks."""
        return len(self.subtasks)
    
    def get_completed_subtasks(self) -> int:
        """Get number of completed subtasks."""
        return len([st for st in self.subtasks if st.status == TaskStatus.DONE])
    
    def get_completion_percentage(self) -> float:
        """Get task completion percentage based on subtasks."""
        total = self.get_total_subtasks()
        if total == 0:
            return 100.0 if self.status == TaskStatus.DONE else 0.0
        completed = self.get_completed_subtasks()
        return (completed / total) * 100.0
    
    def is_blocked_by_dependencies(self, all_tasks: List['Task']) -> bool:
        """Check if task is blocked by incomplete dependencies."""
        if not self.dependencies:
            return False
        
        task_map = {task.id: task for task in all_tasks}
        for dep_id in self.dependencies:
            dep_task = task_map.get(dep_id)
            if dep_task and dep_task.status not in [TaskStatus.DONE, TaskStatus.CANCELLED]:
                return True
        return False
    
    def get_bug_details(self) -> Optional[BugDetails]:
        """Get bug-specific details if this is a bug task."""
        if self.type != TaskType.BUG:
            return None
        
        return BugDetails(
            severity=self.severity,
            environment=self.environment,
            steps_to_reproduce=self.steps_to_reproduce,
            expected_result=self.expected_result,
            actual_result=self.actual_result
        )
    
    def get_test_coverage(self) -> TestCoverage:
        """Get test coverage information."""
        return TestCoverage(
            target_coverage=self.target_test_coverage,
            achieved_coverage=self.achieved_test_coverage,
            related_test_files=self.related_test_files,
            test_results=self.test_results
        )


# Request/Response Models

class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    type: TaskType = TaskType.TASK
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[int] = Field(default_factory=list)
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    
    # Bug-specific fields
    severity: Optional[BugSeverity] = None
    environment: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    
    # Test coverage fields
    target_test_coverage: Optional[int] = Field(None, ge=0, le=100)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    estimated_hours: Optional[float] = Field(None, gt=0)
    
    class Config:
        use_enum_values = True


class TaskUpdateRequest(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    
    # Test coverage updates
    achieved_test_coverage: Optional[int] = Field(None, ge=0, le=100)
    test_results: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class TaskResponse(BaseModel):
    """Response model for task operations."""
    task: Task
    success: bool = True
    message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class TaskListResponse(BaseModel):
    """Response model for task list operations."""
    tasks: List[Task]
    total: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False


# AI Service Models

class AIUsageRecord(BaseModel):
    """AI usage tracking record."""
    timestamp: datetime = Field(default_factory=datetime.now)
    provider: str
    model: str
    operation_type: str
    operation_context: str
    
    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    # Cost and performance
    estimated_cost: float = 0.0
    duration_ms: int = 0
    
    # Status and metadata
    status: str = "success"  # success, failed, cached
    cache_hit: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('total_tokens')
    def validate_total_tokens(cls, v, values):
        """Validate total tokens matches sum of prompt and completion tokens."""
        prompt = values.get('prompt_tokens', 0)
        completion = values.get('completion_tokens', 0)
        expected = prompt + completion
        if v != expected and v != 0:  # Allow 0 for failed calls
            v = expected
        return v


class AIModelConfig(BaseModel):
    """AI model configuration."""
    name: str
    provider: AIModelProvider
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: float = 30.0
    cost_per_1k_tokens: float = 0.001
    supports_json: bool = True
    supports_streaming: bool = True
    
    class Config:
        use_enum_values = True


# Domain Services Interfaces (will be implemented in services layer)

class TaskDomainService:
    """Domain service for task business logic."""
    
    @staticmethod
    def can_add_dependency(task: Task, dependency_task: Task, all_tasks: List[Task]) -> bool:
        """Check if a dependency can be added without creating cycles."""
        # Implementation will be in services layer
        pass
    
    @staticmethod
    def calculate_task_complexity(task: Task) -> int:
        """Calculate task complexity score based on various factors."""
        # Implementation will be in services layer
        pass
    
    @staticmethod
    def estimate_completion_time(task: Task) -> Optional[datetime]:
        """Estimate task completion time based on subtasks and dependencies."""
        # Implementation will be in services layer
        pass


# Events (for future event-driven architecture)

class DomainEvent(BaseModel):
    """Base class for domain events."""
    event_id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: str
    aggregate_id: Union[int, str]
    aggregate_type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class TaskCreatedEvent(DomainEvent):
    """Event raised when a task is created."""
    event_type: str = "task.created"
    aggregate_type: str = "task"


class TaskStatusChangedEvent(DomainEvent):
    """Event raised when a task status changes."""
    event_type: str = "task.status_changed" 
    aggregate_type: str = "task"
    
    @property
    def old_status(self) -> Optional[str]:
        return self.data.get('old_status')
    
    @property  
    def new_status(self) -> Optional[str]:
        return self.data.get('new_status')