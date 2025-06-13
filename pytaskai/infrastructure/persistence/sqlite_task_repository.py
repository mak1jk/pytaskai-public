"""
SQLite implementation of the task repository interface.
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from pytaskai.domain.entities.task import Document, Task
from pytaskai.domain.repositories.task_repository import (
    DocumentRepository,
    TaskManagementRepository,
    TaskRepository,
)
from pytaskai.domain.value_objects.task_types import TaskConfig, TaskId
from pytaskai.infrastructure.persistence.database import Database
from pytaskai.infrastructure.persistence.mappers import (
    DocumentMapper,
    TaskConfigMapper,
    TaskMapper,
)
from pytaskai.infrastructure.persistence.models import (
    DocumentModel,
    TaskConfigModel,
    TaskModel,
)

# ---------------------------------------------------------------------------
# NOTE: Compatibility shim
# ---------------------------------------------------------------------------
# ``SQLiteTaskRepository`` historically implemented ONLY the ``TaskRepository``
# interface.  However, several higher-level components (services, use-cases and
# tests) are written against the *combined* ``TaskManagementRepository``
# abstraction and access nested repositories via the ``tasks`` / ``docs``
# attributes.  Integration tests sometimes pass a plain
# ``SQLiteTaskRepository`` instance where a combined repository is expected. To
# avoid having to update all those call-sites we expose *compatibility
# properties* so that a standalone ``SQLiteTaskRepository`` can masquerade as a
# full ``TaskManagementRepository``:
#
#   - ``tasks`` returns *self* (task operations are implemented directly).
#   - ``docs`` returns an internal ``SQLiteDocumentRepository`` instance that
#     handles document operations.
#
# This change is purely additive and does not affect existing behaviour when
# the proper ``SQLiteTaskManagementRepository`` is used.


class SQLiteTaskRepository(TaskRepository):
    """SQLite implementation of TaskRepository interface."""

    def __init__(self, database: Database) -> None:
        self._database = database
        # Provide document repository for compatibility with callers expecting
        # a ``docs`` attribute.
        from pytaskai.infrastructure.persistence.sqlite_task_repository import (
            SQLiteDocumentRepository,
        )

        self._docs = SQLiteDocumentRepository(database)

    # ---------------------------------------------------------------------
    # Compatibility helpers (nested repository facade)
    # ---------------------------------------------------------------------

    @property
    def tasks(self) -> "SQLiteTaskRepository":  # type: ignore[override]
        """Return self to satisfy ``repository.tasks`` access."""

        return self

    @property
    def docs(self) -> "SQLiteDocumentRepository":  # type: ignore[override]
        """Return underlying document repository for ``repository.docs``."""

        return self._docs

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        size: Optional[str] = None,
        project: Optional[str] = None,
        task_type: str = "Task",
        status: str = "Todo",
        assignee: Optional[str] = None,
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        start_at: Optional[datetime] = None,
        due_at: Optional[datetime] = None,
    ) -> Task:
        """Create a new task."""
        # Generate unique ID
        task_id = str(uuid4())[:12]  # 12-character ID

        # Create domain entity first to validate data
        from pytaskai.domain.value_objects.task_types import (
            ProjectName,
            TagName,
            TaskPriority,
            TaskSize,
            TaskStatus,
            TaskType,
        )

        entity_tags = [TagName(tag) for tag in (tags or [])]
        entity_priority = TaskPriority(priority) if priority else None
        entity_size = TaskSize(size) if size else None
        entity_parent_id = TaskId(parent_id) if parent_id else None

        task_entity = Task(
            id=TaskId(task_id),
            title=title,
            project=ProjectName(project or "Default"),
            task_type=TaskType(task_type),
            status=TaskStatus(status),
            description=description,
            assignee=assignee,
            parent_id=entity_parent_id,
            tags=entity_tags,
            priority=entity_priority,
            start_at=start_at,
            due_at=due_at,
            size=entity_size,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Convert to database model and save
        async with self._database.transaction() as session:
            task_model = TaskMapper.to_model(task_entity)
            session.add(task_model)
            session.flush()  # Get the ID back

            return TaskMapper.to_domain(task_model)

    async def get_task(self, task_id: TaskId) -> Optional[Task]:
        """Get a task by ID."""
        async with self._database.transaction() as session:
            task_model = (
                session.query(TaskModel).filter(TaskModel.id == str(task_id)).first()
            )

            if task_model:
                return TaskMapper.to_domain(task_model)
            return None

    async def update_task(
        self,
        task_id: TaskId,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        size: Optional[str] = None,
        assignee: Optional[str] = None,
        tags: Optional[List[str]] = None,
        start_at: Optional[datetime] = None,
        due_at: Optional[datetime] = None,
    ) -> Task:
        """Update an existing task."""
        async with self._database.transaction() as session:
            task_model = (
                session.query(TaskModel).filter(TaskModel.id == str(task_id)).first()
            )

            if not task_model:
                raise ValueError(f"Task {task_id} not found")

            # Get current entity
            current_entity = TaskMapper.to_domain(task_model)

            # Apply updates
            update_kwargs = {}
            if title is not None:
                update_kwargs["title"] = title
            if description is not None:
                update_kwargs["description"] = description
            if status is not None:
                from pytaskai.domain.value_objects.task_types import TaskStatus

                update_kwargs["status"] = TaskStatus(status)
            if priority is not None:
                from pytaskai.domain.value_objects.task_types import TaskPriority

                update_kwargs["priority"] = TaskPriority(priority)
            if size is not None:
                from pytaskai.domain.value_objects.task_types import TaskSize

                update_kwargs["size"] = TaskSize(size)
            if assignee is not None:
                update_kwargs["assignee"] = assignee
            if tags is not None:
                from pytaskai.domain.value_objects.task_types import TagName

                update_kwargs["tags"] = [TagName(tag) for tag in tags]
            if start_at is not None:
                update_kwargs["start_at"] = start_at
            if due_at is not None:
                update_kwargs["due_at"] = due_at

            update_kwargs["updated_at"] = datetime.utcnow()

            # Create updated entity
            updated_entity = current_entity._replace(**update_kwargs)

            # Update model
            TaskMapper.update_model_from_entity(task_model, updated_entity)
            session.flush()

            return TaskMapper.to_domain(task_model)

    async def delete_task(self, task_id: TaskId) -> bool:
        """Delete a task."""
        async with self._database.transaction() as session:
            task_model = (
                session.query(TaskModel).filter(TaskModel.id == str(task_id)).first()
            )

            if task_model:
                session.delete(task_model)
                return True
            return False

    async def list_tasks(
        self,
        assignee: Optional[str] = None,
        project: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_type: Optional[str] = None,
        tag: Optional[str] = None,
        due_at_before: Optional[datetime] = None,
        due_at_after: Optional[datetime] = None,
        parent_id: Optional[str] = None,
    ) -> List[Task]:
        """List tasks with optional filters."""
        async with self._database.transaction() as session:
            query = session.query(TaskModel)

            # Apply filters
            if assignee:
                query = query.filter(TaskModel.assignee == assignee)
            if project:
                query = query.filter(TaskModel.project == project)
            if status:
                query = query.filter(TaskModel.status == status)
            if priority:
                query = query.filter(TaskModel.priority == priority)
            if task_type:
                query = query.filter(TaskModel.task_type == task_type)
            if tag:
                query = query.join(TaskModel.tags).filter(
                    TaskModel.tags.any(tag_name=tag)
                )
            if due_at_before:
                query = query.filter(TaskModel.due_at <= due_at_before)
            if due_at_after:
                query = query.filter(TaskModel.due_at >= due_at_after)
            if parent_id:
                query = query.filter(TaskModel.parent_id == parent_id)

            # Order by creation date (newest first)
            query = query.order_by(TaskModel.created_at.desc())

            task_models = query.all()
            return [TaskMapper.to_domain(model) for model in task_models]

    async def add_task_comment(self, task_id: TaskId, text: str) -> bool:
        """Add a comment to a task (placeholder implementation)."""
        # For now, we'll add this as a simple note to the task description
        async with self._database.transaction() as session:
            task_model = (
                session.query(TaskModel).filter(TaskModel.id == str(task_id)).first()
            )

            if task_model:
                # Append comment to description with timestamp
                comment_with_timestamp = f"\n\n**Comment ({datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})**: {text}"
                if task_model.description:
                    task_model.description += comment_with_timestamp
                else:
                    task_model.description = f"**Comment ({datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})**: {text}"
                task_model.updated_at = datetime.utcnow()
                return True
            return False

    async def get_config(self) -> TaskConfig:
        """Get workspace configuration."""
        async with self._database.transaction() as session:
            config_model = (
                session.query(TaskConfigModel)
                .filter(TaskConfigModel.config_type == "default")
                .first()
            )

            if config_model:
                return TaskConfigMapper.to_domain(config_model)

            # Return default configuration if none exists
            return TaskConfig(
                assignees=[],
                statuses=["Todo", "In Progress", "Done"],
                priorities=["Low", "Medium", "High", "Critical"],
                sizes=["Small", "Medium", "Large"],
                projects=["Default"],
                tags=[],
            )

    async def update_config(self, config: TaskConfig) -> TaskConfig:
        """Update workspace configuration."""
        async with self._database.transaction() as session:
            config_model = (
                session.query(TaskConfigModel)
                .filter(TaskConfigModel.config_type == "default")
                .first()
            )

            if config_model:
                TaskConfigMapper.update_model_from_config(config_model, config)
            else:
                config_model = TaskConfigMapper.to_model(config)
                session.add(config_model)

            session.flush()
            return TaskConfigMapper.to_domain(config_model)


class SQLiteDocumentRepository(DocumentRepository):
    """SQLite implementation of DocumentRepository interface."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def create_doc(
        self,
        title: str,
        text: Optional[str] = None,
        folder: Optional[str] = None,
        is_draft: bool = False,
    ) -> Document:
        """Create a new document."""
        # Generate unique ID
        doc_id = str(uuid4())[:12]  # 12-character ID

        document_entity = Document(
            id=doc_id,
            title=title,
            text=text,
            folder=folder,
            is_draft=is_draft,
            in_trash=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        async with self._database.transaction() as session:
            doc_model = DocumentMapper.to_model(document_entity)
            session.add(doc_model)
            session.flush()

            return DocumentMapper.to_domain(doc_model)

    async def get_doc(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        async with self._database.transaction() as session:
            doc_model = (
                session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            )

            if doc_model:
                return DocumentMapper.to_domain(doc_model)
            return None

    async def update_doc(
        self,
        doc_id: str,
        title: Optional[str] = None,
        text: Optional[str] = None,
        folder: Optional[str] = None,
        is_draft: Optional[bool] = None,
    ) -> Document:
        """Update an existing document."""
        async with self._database.transaction() as session:
            doc_model = (
                session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            )

            if not doc_model:
                raise ValueError(f"Document {doc_id} not found")

            # Get current entity
            current_entity = DocumentMapper.to_domain(doc_model)

            # Apply updates
            update_kwargs = {}
            if title is not None:
                update_kwargs["title"] = title
            if text is not None:
                update_kwargs["text"] = text
            if folder is not None:
                update_kwargs["folder"] = folder
            if is_draft is not None:
                update_kwargs["is_draft"] = is_draft

            update_kwargs["updated_at"] = datetime.utcnow()

            # Create updated entity
            updated_entity = current_entity._replace(**update_kwargs)

            # Update model
            DocumentMapper.update_model_from_entity(doc_model, updated_entity)
            session.flush()

            return DocumentMapper.to_domain(doc_model)

    async def delete_doc(self, doc_id: str) -> bool:
        """Delete a document (move to trash)."""
        async with self._database.transaction() as session:
            doc_model = (
                session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            )

            if doc_model:
                doc_model.in_trash = True
                doc_model.updated_at = datetime.utcnow()
                return True
            return False

    async def list_docs(
        self,
        folder: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Document]:
        """List documents with optional filters."""
        async with self._database.transaction() as session:
            query = session.query(DocumentModel).filter(DocumentModel.in_trash == False)

            # Apply filters
            if folder:
                query = query.filter(DocumentModel.folder == folder)
            if search:
                query = query.filter(
                    or_(
                        DocumentModel.title.contains(search),
                        DocumentModel.text.contains(search),
                    )
                )

            # Order by creation date (newest first)
            query = query.order_by(DocumentModel.created_at.desc())

            doc_models = query.all()
            return [DocumentMapper.to_domain(model) for model in doc_models]


class SQLiteTaskManagementRepository(TaskManagementRepository):
    """SQLite implementation of TaskManagementRepository interface."""

    def __init__(self, database: Database) -> None:
        self._database = database
        self._tasks = SQLiteTaskRepository(database)
        self._docs = SQLiteDocumentRepository(database)

    @property
    def tasks(self) -> TaskRepository:
        """Get task repository."""
        return self._tasks

    @property
    def docs(self) -> DocumentRepository:
        """Get document repository."""
        return self._docs
