"""
Mappers between domain entities and database models for PyTaskAI.

These mappers implement the Data Mapper pattern, keeping domain entities
separate from database concerns while providing clean conversion.
"""

from typing import List, Optional

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
from pytaskai.infrastructure.persistence.models import (
    ConfigAssigneeModel,
    ConfigPriorityModel,
    ConfigProjectModel,
    ConfigSizeModel,
    ConfigStatusModel,
    ConfigTagModel,
    DocumentModel,
    TaskConfigModel,
    TaskModel,
    TaskTagModel,
)


class TaskMapper:
    """Mapper for Task domain entity and TaskModel database model."""

    @staticmethod
    def to_domain(model: TaskModel) -> Task:
        """Convert database model to domain entity."""
        tags = [TagName(tag_model.tag_name) for tag_model in model.tags]

        priority = None
        if model.priority:
            priority = TaskPriority(model.priority)

        size = None
        if model.size:
            size = TaskSize(model.size)

        parent_id = None
        if model.parent_id:
            parent_id = TaskId(model.parent_id)

        return Task(
            id=TaskId(model.id),
            title=model.title,
            external_url=model.external_url,
            project=ProjectName(model.project),
            task_type=TaskType(model.task_type),
            status=TaskStatus(model.status),
            assignee=model.assignee,
            parent_id=parent_id,
            tags=tags,
            priority=priority,
            start_at=model.start_at,
            due_at=model.due_at,
            size=size,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Task, existing_model: Optional[TaskModel] = None) -> TaskModel:
        """Convert domain entity to database model."""
        if existing_model:
            # Update existing model
            model = existing_model
            model.title = entity.title
            model.external_url = entity.external_url
            model.project = str(entity.project)
            model.task_type = str(entity.task_type)
            model.status = str(entity.status)
            model.assignee = entity.assignee
            model.parent_id = str(entity.parent_id) if entity.parent_id else None
            model.priority = str(entity.priority) if entity.priority else None
            model.start_at = entity.start_at
            model.due_at = entity.due_at
            model.size = str(entity.size) if entity.size else None
            model.description = entity.description
            model.updated_at = entity.updated_at

            # Update tags (clear existing and add new ones)
            model.tags.clear()
            for tag in entity.tags:
                tag_model = TaskTagModel(task_id=str(entity.id), tag_name=str(tag))
                model.tags.append(tag_model)
        else:
            # Create new model
            model = TaskModel(
                id=str(entity.id),
                title=entity.title,
                external_url=entity.external_url,
                project=str(entity.project),
                task_type=str(entity.task_type),
                status=str(entity.status),
                assignee=entity.assignee,
                parent_id=str(entity.parent_id) if entity.parent_id else None,
                priority=str(entity.priority) if entity.priority else None,
                start_at=entity.start_at,
                due_at=entity.due_at,
                size=str(entity.size) if entity.size else None,
                description=entity.description,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )

            # Add tags
            for tag in entity.tags:
                tag_model = TaskTagModel(task_id=str(entity.id), tag_name=str(tag))
                model.tags.append(tag_model)

        return model

    @staticmethod
    def update_model_from_entity(model: TaskModel, entity: Task) -> None:
        """Update existing model with entity data."""
        TaskMapper.to_model(entity, model)


class DocumentMapper:
    """Mapper for Document domain entity and DocumentModel database model."""

    @staticmethod
    def to_domain(model: DocumentModel) -> Document:
        """Convert database model to domain entity."""
        return Document(
            id=model.id,
            title=model.title,
            text=model.text,
            folder=model.folder,
            is_draft=model.is_draft,
            in_trash=model.in_trash,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: Document, existing_model: Optional[DocumentModel] = None
    ) -> DocumentModel:
        """Convert domain entity to database model."""
        if existing_model:
            # Update existing model
            model = existing_model
            model.title = entity.title
            model.text = entity.text
            model.folder = entity.folder
            model.is_draft = entity.is_draft
            model.in_trash = entity.in_trash
            model.updated_at = entity.updated_at
        else:
            # Create new model
            model = DocumentModel(
                id=entity.id,
                title=entity.title,
                text=entity.text,
                folder=entity.folder,
                is_draft=entity.is_draft,
                in_trash=entity.in_trash,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )

        return model

    @staticmethod
    def update_model_from_entity(model: DocumentModel, entity: Document) -> None:
        """Update existing model with entity data."""
        DocumentMapper.to_model(entity, model)


class TaskConfigMapper:
    """Mapper for TaskConfig domain value object and TaskConfigModel database model."""

    @staticmethod
    def to_domain(model: TaskConfigModel) -> TaskConfig:
        """Convert database model to domain value object."""
        assignees = [assignee_model.assignee for assignee_model in model.assignees]
        statuses = [status_model.status for status_model in model.statuses]
        priorities = [priority_model.priority for priority_model in model.priorities]
        sizes = [size_model.size for size_model in model.sizes]
        projects = [project_model.project for project_model in model.projects]
        tags = [tag_model.tag for tag_model in model.tags]

        return TaskConfig(
            assignees=assignees,
            statuses=statuses,
            priorities=priorities,
            sizes=sizes,
            projects=projects,
            tags=tags,
        )

    @staticmethod
    def to_model(
        config: TaskConfig, existing_model: Optional[TaskConfigModel] = None
    ) -> TaskConfigModel:
        """Convert domain value object to database model."""
        if existing_model:
            model = existing_model

            # Clear existing configuration items
            model.assignees.clear()
            model.statuses.clear()
            model.priorities.clear()
            model.sizes.clear()
            model.projects.clear()
            model.tags.clear()
        else:
            model = TaskConfigModel(config_type="default")

        # Add configuration items with order preservation
        for i, assignee in enumerate(config.assignees):
            model.assignees.append(ConfigAssigneeModel(assignee=assignee))

        for i, status in enumerate(config.statuses):
            model.statuses.append(ConfigStatusModel(status=status))

        for i, priority in enumerate(config.priorities):
            model.priorities.append(ConfigPriorityModel(priority=priority))

        for i, size in enumerate(config.sizes):
            model.sizes.append(ConfigSizeModel(size=size))

        for i, project in enumerate(config.projects):
            model.projects.append(ConfigProjectModel(project=project))

        for i, tag in enumerate(config.tags):
            model.tags.append(ConfigTagModel(tag=tag))

        return model

    @staticmethod
    def update_model_from_config(model: TaskConfigModel, config: TaskConfig) -> None:
        """Update existing model with config data."""
        TaskConfigMapper.to_model(config, model)
