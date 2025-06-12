"""
PyTaskAI - Jira Integration Architecture

Basic architecture for bidirectional Jira integration as outlined in the PRD.
This module provides the foundation for syncing tasks between PyTaskAI and Jira.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import logging

from .models import Task, TaskType, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class JiraIssueType(str, Enum):
    """Jira issue type mapping"""

    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    SUBTASK = "Sub-task"


class JiraPriority(str, Enum):
    """Jira priority levels"""

    BLOCKER = "Blocker"
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"


class JiraStatus(str, Enum):
    """Common Jira status values"""

    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    BLOCKED = "Blocked"
    CANCELLED = "Cancelled"


class JiraSyncStrategy(str, Enum):
    """Jira synchronization strategies"""

    COMPLETE = "complete"  # Sync all tasks
    SELECTIVE = "selective"  # Sync only tagged tasks
    UNIDIRECTIONAL = "unidirectional"  # PyTaskAI -> Jira only
    MANUAL = "manual"  # Manual sync only


class JiraConfig(BaseModel):
    """Jira integration configuration"""

    # Connection settings
    server_url: str = Field(..., description="Jira server URL")
    username: str = Field(..., description="Jira username")
    api_token: str = Field(..., description="Jira API token")
    project_key: str = Field(..., description="Jira project key")

    # Sync settings
    sync_strategy: JiraSyncStrategy = Field(
        default=JiraSyncStrategy.SELECTIVE, description="Synchronization strategy"
    )
    sync_interval_minutes: int = Field(
        default=30, description="Auto-sync interval in minutes"
    )

    # Mapping configuration
    enable_intelligent_mapping: bool = Field(
        default=True, description="Use AI-based intelligent mapping"
    )

    # Custom field mappings
    custom_field_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom field mappings {pytaskai_field: jira_field_id}",
    )

    # Sync filters
    sync_tags: List[str] = Field(
        default_factory=list, description="Tags that trigger Jira sync"
    )

    # Conflict resolution
    conflict_resolution: str = Field(
        default="timestamp",
        description="Conflict resolution strategy (timestamp, manual, jira_wins, pytaskai_wins)",
    )


class JiraTaskMapping(BaseModel):
    """Mapping between PyTaskAI and Jira"""

    pytaskai_task_id: int = Field(..., description="PyTaskAI task ID")
    jira_issue_key: str = Field(..., description="Jira issue key (e.g., PROJ-123)")
    jira_issue_id: str = Field(..., description="Jira internal issue ID")

    # Mapping metadata
    mapped_at: datetime = Field(default_factory=datetime.now)
    last_synced: Optional[datetime] = Field(default=None)
    sync_direction: str = Field(
        default="bidirectional"
    )  # bidirectional, to_jira, from_jira

    # Sync status
    sync_status: str = Field(default="synced")  # synced, conflict, error, pending
    last_sync_error: Optional[str] = Field(default=None)


class JiraIssue(BaseModel):
    """Jira issue representation"""

    key: str = Field(..., description="Jira issue key")
    id: str = Field(..., description="Jira issue ID")
    summary: str = Field(..., description="Issue summary")
    description: Optional[str] = Field(default=None)
    issue_type: JiraIssueType = Field(..., description="Issue type")
    status: str = Field(..., description="Current status")
    priority: Optional[str] = Field(default=None)

    # Timestamps
    created: datetime = Field(...)
    updated: datetime = Field(...)

    # Additional fields
    assignee: Optional[str] = Field(default=None)
    reporter: Optional[str] = Field(default=None)
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)

    # Custom fields for bug tracking
    environment: Optional[str] = Field(default=None)
    steps_to_reproduce: Optional[str] = Field(default=None)
    expected_result: Optional[str] = Field(default=None)
    actual_result: Optional[str] = Field(default=None)


class TaskToJiraMapper:
    """Maps PyTaskAI tasks to Jira issues"""

    def __init__(self, config: JiraConfig):
        self.config = config

        # Task type mapping
        self.task_type_mapping = {
            TaskType.TASK: JiraIssueType.TASK,
            TaskType.BUG: JiraIssueType.BUG,
            TaskType.FEATURE: JiraIssueType.STORY,
            TaskType.ENHANCEMENT: JiraIssueType.STORY,
            TaskType.RESEARCH: JiraIssueType.TASK,
            TaskType.DOCUMENTATION: JiraIssueType.TASK,
        }

        # Priority mapping
        self.priority_mapping = {
            TaskPriority.HIGHEST: JiraPriority.CRITICAL,
            TaskPriority.HIGH: JiraPriority.HIGH,
            TaskPriority.MEDIUM: JiraPriority.MEDIUM,
            TaskPriority.LOW: JiraPriority.LOW,
            TaskPriority.LOWEST: JiraPriority.LOWEST,
        }

        # Status mapping
        self.status_mapping = {
            TaskStatus.PENDING: JiraStatus.TO_DO,
            TaskStatus.IN_PROGRESS: JiraStatus.IN_PROGRESS,
            TaskStatus.REVIEW: JiraStatus.IN_REVIEW,
            TaskStatus.DONE: JiraStatus.DONE,
            TaskStatus.BLOCKED: JiraStatus.BLOCKED,
            TaskStatus.CANCELLED: JiraStatus.CANCELLED,
        }

    def determine_jira_issue_type(self, task: Task) -> JiraIssueType:
        """Determine appropriate Jira issue type for a task"""

        if self.config.enable_intelligent_mapping:
            # Use complexity and priority for intelligent mapping
            complexity = getattr(task, "complexity_score", 5)

            if task.type == TaskType.BUG:
                return JiraIssueType.BUG
            elif task.type == TaskType.FEATURE:
                # High complexity features become Epics
                if complexity >= 8:
                    return JiraIssueType.EPIC
                else:
                    return JiraIssueType.STORY
            elif task.type == TaskType.ENHANCEMENT:
                return JiraIssueType.STORY
            elif task.subtasks and len(task.subtasks) > 3:
                # Tasks with many subtasks become Epics
                return JiraIssueType.EPIC
            else:
                return JiraIssueType.TASK

        # Fallback to simple mapping
        return self.task_type_mapping.get(task.type, JiraIssueType.TASK)

    def map_task_to_jira_fields(self, task: Task) -> Dict[str, Any]:
        """Convert PyTaskAI task to Jira issue fields"""

        fields = {
            "summary": task.title,
            "description": self._format_description(task),
            "issuetype": {"name": self.determine_jira_issue_type(task).value},
            "priority": {
                "name": self.priority_mapping.get(
                    task.priority, JiraPriority.MEDIUM
                ).value
            },
            "labels": self._generate_labels(task),
        }

        # Add bug-specific fields
        if task.type == TaskType.BUG:
            fields.update(self._map_bug_fields(task))

        # Add custom field mappings
        for pytaskai_field, jira_field_id in self.config.custom_field_mappings.items():
            if hasattr(task, pytaskai_field):
                value = getattr(task, pytaskai_field)
                if value is not None:
                    fields[jira_field_id] = value

        return fields

    def _format_description(self, task: Task) -> str:
        """Format task description for Jira"""
        description = task.description

        # Add additional information
        if task.details:
            description += f"\n\n*Details:*\n{task.details}"

        if task.test_strategy:
            description += f"\n\n*Test Strategy:*\n{task.test_strategy}"

        # Add test coverage info
        if task.target_test_coverage:
            description += f"\n\n*Target Test Coverage:* {task.target_test_coverage}%"

        if task.achieved_test_coverage:
            description += f"\n*Achieved Test Coverage:* {task.achieved_test_coverage}%"

        # Add PyTaskAI metadata
        description += f"\n\n---\n*Synced from PyTaskAI (Task #{task.id})*"

        return description

    def _generate_labels(self, task: Task) -> List[str]:
        """Generate Jira labels for task"""
        labels = ["pytaskai"]

        # Add type label
        labels.append(f"type-{task.type}")

        # Add priority label
        labels.append(f"priority-{task.priority}")

        # Add bug severity for bugs
        if task.type == TaskType.BUG and task.severity:
            labels.append(f"severity-{task.severity}")

        # Add test coverage labels
        if task.target_test_coverage:
            labels.append("has-test-coverage")

        return labels

    def _map_bug_fields(self, task: Task) -> Dict[str, Any]:
        """Map bug-specific fields to Jira"""
        bug_fields = {}

        # These would be mapped to actual Jira custom field IDs
        if task.environment:
            bug_fields["customfield_environment"] = task.environment

        if task.steps_to_reproduce:
            bug_fields["customfield_steps_to_reproduce"] = task.steps_to_reproduce

        if task.expected_result:
            bug_fields["customfield_expected_result"] = task.expected_result

        if task.actual_result:
            bug_fields["customfield_actual_result"] = task.actual_result

        return bug_fields


class JiraIntegrationService:
    """Main service for Jira integration"""

    def __init__(self, config: JiraConfig):
        self.config = config
        self.mapper = TaskToJiraMapper(config)
        self.mappings: List[JiraTaskMapping] = []

    def should_sync_task(self, task: Task) -> bool:
        """Determine if a task should be synced with Jira"""

        if self.config.sync_strategy == JiraSyncStrategy.MANUAL:
            return False

        if self.config.sync_strategy == JiraSyncStrategy.SELECTIVE:
            # Check if task has sync tags
            return any(
                tag in self.config.sync_tags for tag in getattr(task, "tags", [])
            )

        if self.config.sync_strategy == JiraSyncStrategy.COMPLETE:
            return True

        return False

    async def sync_task_to_jira(self, task: Task) -> Optional[JiraTaskMapping]:
        """Sync a PyTaskAI task to Jira"""

        if not self.should_sync_task(task):
            logger.debug(f"Task {task.id} not eligible for Jira sync")
            return None

        try:
            # Check if already mapped
            existing_mapping = self.find_mapping_by_task_id(task.id)

            if existing_mapping:
                # Update existing Jira issue
                return await self._update_jira_issue(task, existing_mapping)
            else:
                # Create new Jira issue
                return await self._create_jira_issue(task)

        except Exception as e:
            logger.error(f"Failed to sync task {task.id} to Jira: {e}")
            return None

    async def _create_jira_issue(self, task: Task) -> JiraTaskMapping:
        """Create new Jira issue from task"""
        # This would implement actual Jira API calls
        logger.info(f"Would create Jira issue for task {task.id}")

        # Placeholder implementation
        # In real implementation, this would call Jira REST API
        # jira_fields = self.mapper.map_task_to_jira_fields(task)
        # jira_issue = jira_client.create_issue(fields=jira_fields)

        # Create mapping record
        mapping = JiraTaskMapping(
            pytaskai_task_id=task.id,
            jira_issue_key=f"PROJ-{task.id}",  # Placeholder
            jira_issue_id=f"jira_id_{task.id}",  # Placeholder
            sync_status="synced",
        )

        self.mappings.append(mapping)
        return mapping

    async def _update_jira_issue(
        self, task: Task, mapping: JiraTaskMapping
    ) -> JiraTaskMapping:
        """Update existing Jira issue"""
        logger.info(
            f"Would update Jira issue {mapping.jira_issue_key} for task {task.id}"
        )

        # Update mapping
        mapping.last_synced = datetime.now()
        mapping.sync_status = "synced"

        return mapping

    def find_mapping_by_task_id(self, task_id: int) -> Optional[JiraTaskMapping]:
        """Find Jira mapping for a task"""
        return next((m for m in self.mappings if m.pytaskai_task_id == task_id), None)

    def get_sync_status_summary(self) -> Dict[str, Any]:
        """Get summary of sync status"""
        total_mappings = len(self.mappings)
        synced = len([m for m in self.mappings if m.sync_status == "synced"])
        conflicts = len([m for m in self.mappings if m.sync_status == "conflict"])
        errors = len([m for m in self.mappings if m.sync_status == "error"])

        return {
            "total_mappings": total_mappings,
            "synced": synced,
            "conflicts": conflicts,
            "errors": errors,
            "sync_rate": synced / max(total_mappings, 1) * 100,
            "last_sync": max(
                [m.last_synced for m in self.mappings if m.last_synced], default=None
            ),
        }


# Configuration examples
DEFAULT_JIRA_CONFIG = JiraConfig(
    server_url="https://your-company.atlassian.net",
    username="your-email@company.com",
    api_token="your-api-token",
    project_key="PROJ",
    sync_strategy=JiraSyncStrategy.SELECTIVE,
    sync_tags=["jira-sync", "production"],
    custom_field_mappings={
        "environment": "customfield_10001",
        "steps_to_reproduce": "customfield_10002",
        "expected_result": "customfield_10003",
        "actual_result": "customfield_10004",
    },
)
