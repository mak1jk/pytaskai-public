"""
Abstract interfaces for notification services in PyTaskAI application layer.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional


class NotificationChannel(Enum):
    """Available notification channels."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationPriority(Enum):
    """Notification priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationService(ABC):
    """
    Abstract interface for notification services.

    This interface defines the contract for services that can send
    notifications about task events, deadlines, and other updates.
    """

    @abstractmethod
    async def send_task_created_notification(
        self,
        task_id: str,
        task_title: str,
        assignee: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.IN_APP,
    ) -> bool:
        """
        Send notification when a new task is created.

        Args:
            task_id: ID of the created task
            task_title: Title of the created task
            assignee: Optional assignee to notify
            channel: Notification channel to use

        Returns:
            True if notification was sent successfully

        Raises:
            NotificationError: If notification fails to send
        """

    @abstractmethod
    async def send_task_assigned_notification(
        self,
        task_id: str,
        task_title: str,
        assignee: str,
        assigned_by: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.EMAIL,
    ) -> bool:
        """
        Send notification when a task is assigned.

        Args:
            task_id: ID of the assigned task
            task_title: Title of the assigned task
            assignee: Person the task is assigned to
            assigned_by: Optional person who assigned the task
            channel: Notification channel to use

        Returns:
            True if notification was sent successfully

        Raises:
            NotificationError: If notification fails to send
        """

    @abstractmethod
    async def send_task_due_notification(
        self,
        task_id: str,
        task_title: str,
        assignee: str,
        hours_until_due: int,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
    ) -> bool:
        """
        Send notification when a task is approaching its due date.

        Args:
            task_id: ID of the task
            task_title: Title of the task
            assignee: Person assigned to the task
            hours_until_due: Hours remaining until due date
            priority: Priority of the notification

        Returns:
            True if notification was sent successfully

        Raises:
            NotificationError: If notification fails to send
        """

    @abstractmethod
    async def send_task_overdue_notification(
        self,
        task_id: str,
        task_title: str,
        assignee: str,
        hours_overdue: int,
        priority: NotificationPriority = NotificationPriority.HIGH,
    ) -> bool:
        """
        Send notification when a task is overdue.

        Args:
            task_id: ID of the overdue task
            task_title: Title of the overdue task
            assignee: Person assigned to the task
            hours_overdue: Hours past the due date
            priority: Priority of the notification

        Returns:
            True if notification was sent successfully

        Raises:
            NotificationError: If notification fails to send
        """

    @abstractmethod
    async def send_task_completed_notification(
        self,
        task_id: str,
        task_title: str,
        completed_by: str,
        project: str,
        channel: NotificationChannel = NotificationChannel.SLACK,
    ) -> bool:
        """
        Send notification when a task is completed.

        Args:
            task_id: ID of the completed task
            task_title: Title of the completed task
            completed_by: Person who completed the task
            project: Project the task belongs to
            channel: Notification channel to use

        Returns:
            True if notification was sent successfully

        Raises:
            NotificationError: If notification fails to send
        """

    @abstractmethod
    async def send_bulk_notification(
        self,
        message: str,
        recipients: List[str],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channel: NotificationChannel = NotificationChannel.EMAIL,
    ) -> int:
        """
        Send bulk notification to multiple recipients.

        Args:
            message: Notification message
            recipients: List of recipient identifiers
            priority: Priority of the notification
            channel: Notification channel to use

        Returns:
            Number of notifications sent successfully

        Raises:
            NotificationError: If bulk notification fails
        """


class NotificationError(Exception):
    """Exception raised when notification operations fail."""

    def __init__(
        self, message: str, channel: Optional[NotificationChannel] = None
    ) -> None:
        self.message = message
        self.channel = channel
        channel_info = f" via {channel.value}" if channel else ""
        super().__init__(f"Notification error{channel_info}: {message}")
