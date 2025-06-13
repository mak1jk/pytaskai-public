"""
Unit tests for PyTaskAI domain layer.
"""

from datetime import datetime, timedelta

import pytest

from pytaskai.domain.entities.task import Document, Task
from pytaskai.domain.value_objects.task_types import (
    ProjectName,
    TagName,
    TaskConfig,
    TaskId,
    TaskPriority,
    TaskSize,
    TaskStatus,
    TaskType,
)


class TestTaskId:
    """Test TaskId value object."""

    def test_valid_task_id(self) -> None:
        task_id = TaskId("abcd12345678")
        assert str(task_id) == "abcd12345678"

    def test_invalid_task_id_empty(self) -> None:
        with pytest.raises(ValueError, match="must be a non-empty string"):
            TaskId("")

    def test_invalid_task_id_short(self) -> None:
        task_id = TaskId("short")
        assert str(task_id) == "short"


class TestTaskStatus:
    """Test TaskStatus value object."""

    def test_done_status(self) -> None:
        status = TaskStatus("Done")
        assert status.is_done()
        assert not status.is_in_progress()
        assert not status.is_pending()

    def test_in_progress_status(self) -> None:
        status = TaskStatus("In Progress")
        assert not status.is_done()
        assert status.is_in_progress()
        assert not status.is_pending()

    def test_pending_status(self) -> None:
        status = TaskStatus("Todo")
        assert not status.is_done()
        assert not status.is_in_progress()
        assert status.is_pending()


class TestTaskPriority:
    """Test TaskPriority value object."""

    def test_high_priority(self) -> None:
        priority = TaskPriority("Critical")
        assert priority.is_high_priority()
        assert not priority.is_low_priority()

    def test_low_priority(self) -> None:
        priority = TaskPriority("Low")
        assert not priority.is_high_priority()
        assert priority.is_low_priority()


class TestTask:
    """Test Task entity."""

    def create_sample_task(self) -> Task:
        return Task(
            id=TaskId("abcd12345678"),
            title="Test Task",
            external_url="https://app.itsdart.com/t/abcd12345678",
            project=ProjectName("Test Project"),
            task_type=TaskType("Task"),
            status=TaskStatus("Todo"),
            assignee="test@example.com",
            tags=[TagName("test"), TagName("sample")],
            priority=TaskPriority("High"),
            due_at=datetime.now() + timedelta(days=7),
        )

    def test_create_task(self) -> None:
        task = self.create_sample_task()
        assert str(task.id) == "abcd12345678"
        assert task.title == "Test Task"
        assert not task.is_completed()
        assert not task.is_overdue()
        assert task.is_high_priority()

    def test_overdue_task(self) -> None:
        task = Task(
            id=TaskId("abcd12345678"),
            title="Overdue Task",
            external_url="https://app.itsdart.com/t/abcd12345678",
            project=ProjectName("Test Project"),
            task_type=TaskType("Task"),
            status=TaskStatus("Todo"),
            due_at=datetime.now() - timedelta(days=1),
        )
        assert task.is_overdue()

    def test_completed_task(self) -> None:
        task = Task(
            id=TaskId("abcd12345678"),
            title="Completed Task",
            external_url="https://app.itsdart.com/t/abcd12345678",
            project=ProjectName("Test Project"),
            task_type=TaskType("Task"),
            status=TaskStatus("Done"),
        )
        assert task.is_completed()

    def test_add_tag(self) -> None:
        task = self.create_sample_task()
        new_task = task.add_tag(TagName("urgent"))

        assert len(new_task.tags) == 3
        assert TagName("urgent") in new_task.tags
        assert len(task.tags) == 2  # Original unchanged

    def test_add_existing_tag(self) -> None:
        task = self.create_sample_task()
        new_task = task.add_tag(TagName("test"))

        assert len(new_task.tags) == 2
        assert new_task.tags == task.tags

    def test_remove_tag(self) -> None:
        task = self.create_sample_task()
        new_task = task.remove_tag(TagName("test"))

        assert len(new_task.tags) == 1
        assert TagName("test") not in new_task.tags
        assert len(task.tags) == 2  # Original unchanged

    def test_update_status(self) -> None:
        task = self.create_sample_task()
        new_task = task.update_status(TaskStatus("Done"))

        assert new_task.is_completed()
        assert not task.is_completed()  # Original unchanged


class TestDocument:
    """Test Document entity."""

    def test_create_doc(self) -> None:
        doc = Document(
            id="doc12345678",
            title="Test Document",
            text="This is test content",
            folder="Test Folder",
        )
        assert doc.id == "doc12345678"
        assert doc.title == "Test Document"
        assert not doc.is_empty()

    def test_empty_doc(self) -> None:
        doc = Document(
            id="doc12345678",
            title="Empty Document",
            text="   ",
        )
        assert doc.is_empty()

    def test_update_content(self) -> None:
        doc = Document(
            id="doc12345678",
            title="Test Document",
            text="Original content",
        )
        new_doc = doc.update_content("Updated content")

        assert new_doc.text == "Updated content"
        assert doc.text == "Original content"  # Original unchanged

    def test_move_to_folder(self) -> None:
        doc = Document(
            id="doc12345678",
            title="Test Document",
            folder="Old Folder",
        )
        new_doc = doc.move_to_folder("New Folder")

        assert new_doc.folder == "New Folder"
        assert doc.folder == "Old Folder"  # Original unchanged


class TestTaskSize:
    """Test TaskSize value object."""

    def test_large_size(self) -> None:
        size = TaskSize("Large")
        assert size.is_large()
        assert not size.is_small()

    def test_small_size(self) -> None:
        size = TaskSize("Small")
        assert not size.is_large()
        assert size.is_small()

    def test_medium_size(self) -> None:
        size = TaskSize("Medium")
        assert not size.is_large()
        assert not size.is_small()

    def test_invalid_size_empty(self) -> None:
        with pytest.raises(ValueError, match="must be a non-empty string"):
            TaskSize("")


class TestTaskType:
    """Test TaskType value object."""

    def test_bug_type(self) -> None:
        task_type = TaskType("Bug")
        assert task_type.is_bug()
        assert not task_type.is_feature()
        assert not task_type.is_task()

    def test_feature_type(self) -> None:
        task_type = TaskType("Feature")
        assert not task_type.is_bug()
        assert task_type.is_feature()
        assert not task_type.is_task()

    def test_task_type(self) -> None:
        task_type = TaskType("Task")
        assert not task_type.is_bug()
        assert not task_type.is_feature()
        assert task_type.is_task()

    def test_invalid_type_empty(self) -> None:
        with pytest.raises(ValueError, match="must be a non-empty string"):
            TaskType("")


class TestProjectName:
    """Test ProjectName value object."""

    def test_valid_project_name(self) -> None:
        project = ProjectName("My Project")
        assert str(project) == "My Project"

    def test_invalid_project_name_empty(self) -> None:
        with pytest.raises(ValueError, match="must be a non-empty string"):
            ProjectName("")


class TestTagName:
    """Test TagName value object."""

    def test_valid_tag_name(self) -> None:
        tag = TagName("urgent")
        assert str(tag) == "urgent"

    def test_invalid_tag_name_empty(self) -> None:
        with pytest.raises(ValueError, match="must be a non-empty string"):
            TagName("")


class TestTaskConfig:
    """Test TaskConfig value object."""

    def test_valid_config(self) -> None:
        config = TaskConfig(
            assignees=["alice@example.com", "bob@example.com"],
            statuses=["Todo", "In Progress", "Done"],
            priorities=["Low", "Medium", "High"],
            sizes=["S", "M", "L"],
            projects=["Project A", "Project B"],
            tags=["frontend", "backend", "bug"],
        )
        assert len(config.assignees) == 2
        assert len(config.statuses) == 3
        assert len(config.priorities) == 3

    def test_invalid_config_non_list_assignees(self) -> None:
        with pytest.raises(ValueError, match="assignees must be a list"):
            TaskConfig(
                assignees="not a list",  # type: ignore
                statuses=["Todo"],
                priorities=["High"],
                sizes=["M"],
                projects=["Project"],
                tags=["tag"],
            )

    def test_invalid_config_non_list_statuses(self) -> None:
        with pytest.raises(ValueError, match="statuses must be a list"):
            TaskConfig(
                assignees=["user"],
                statuses="not a list",  # type: ignore
                priorities=["High"],
                sizes=["M"],
                projects=["Project"],
                tags=["tag"],
            )

    def test_invalid_config_non_list_priorities(self) -> None:
        with pytest.raises(ValueError, match="priorities must be a list"):
            TaskConfig(
                assignees=["user"],
                statuses=["Todo"],
                priorities="not a list",  # type: ignore
                sizes=["M"],
                projects=["Project"],
                tags=["tag"],
            )
