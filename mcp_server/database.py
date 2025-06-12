"""
PyTaskAI - SQLite Database Module

This module provides SQLite database functionality using SQLAlchemy ORM
for task and subtask management, replacing the JSON-based storage.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from shared.models import TaskStatus, TaskPriority, TaskType, BugSeverity

logger = logging.getLogger(__name__)

Base = declarative_base()


class TaskDB(Base):
    """SQLAlchemy model for tasks table"""

    __tablename__ = "tasks"

    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = Column(
        SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False
    )
    type = Column(SQLEnum(TaskType), default=TaskType.TASK, nullable=False)

    # Content fields
    details = Column(Text, default="")
    test_strategy = Column(Text, default="")

    # Metadata fields
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    # Estimation fields
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    complexity_score = Column(Integer, nullable=True)

    # Bug-specific fields
    severity = Column(SQLEnum(BugSeverity), nullable=True)
    steps_to_reproduce = Column(Text, nullable=True)
    expected_result = Column(Text, nullable=True)
    actual_result = Column(Text, nullable=True)
    environment = Column(Text, nullable=True)

    # File attachments (JSON array of file paths)
    attachments = Column(JSON, default=list)

    # Test coverage fields
    target_test_coverage = Column(Float, nullable=True)
    achieved_test_coverage = Column(Float, nullable=True)
    test_report_url = Column(String(500), nullable=True)
    related_tests = Column(JSON, default=list)

    # AI generation metadata
    generated_by_ai = Column(Boolean, default=False)
    ai_model_used = Column(String(100), nullable=True)
    research_used = Column(Boolean, default=False)

    # Dependencies (stored as JSON array of task IDs)
    dependencies = Column(JSON, default=list)

    # Relationships
    subtasks = relationship(
        "SubTaskDB", back_populates="parent_task", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert TaskDB instance to dictionary matching Pydantic model"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if self.status else "pending",
            "priority": self.priority.value if self.priority else "medium",
            "type": self.type.value if self.type else "task",
            "details": self.details or "",
            "test_strategy": self.test_strategy or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "complexity_score": self.complexity_score,
            "severity": self.severity.value if self.severity else None,
            "steps_to_reproduce": self.steps_to_reproduce,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "environment": self.environment,
            "attachments": self.attachments or [],
            "target_test_coverage": self.target_test_coverage,
            "achieved_test_coverage": self.achieved_test_coverage,
            "test_report_url": self.test_report_url,
            "related_tests": self.related_tests or [],
            "generated_by_ai": self.generated_by_ai or False,
            "ai_model_used": self.ai_model_used,
            "research_used": self.research_used or False,
            "dependencies": self.dependencies or [],
            "subtasks": (
                [subtask.to_dict() for subtask in self.subtasks]
                if self.subtasks
                else []
            ),
        }


class SubTaskDB(Base):
    """SQLAlchemy model for subtasks table"""

    __tablename__ = "subtasks"

    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    # Content fields
    details = Column(Text, default="")
    test_strategy = Column(Text, default="")

    # Metadata fields
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Estimation fields
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)

    # Dependencies (JSON array of subtask IDs)
    dependencies = Column(JSON, default=list)

    # Relationships
    parent_task = relationship("TaskDB", back_populates="subtasks")

    def to_dict(self) -> Dict[str, Any]:
        """Convert SubTaskDB instance to dictionary matching Pydantic model"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if self.status else "pending",
            "details": self.details or "",
            "test_strategy": self.test_strategy or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "dependencies": self.dependencies or [],
        }


class DatabaseManager:
    """Database manager for PyTaskAI SQLite operations"""

    def __init__(self, project_root: str = "."):
        # Ensure we always work with an absolute, resolved project root path
        # This prevents multiple DatabaseManager instances pointing to different
        # database files when the same directory is referenced with relative vs
        # absolute paths.
        self.project_root = Path(project_root).resolve()
        self.db_path = self.project_root / ".pytaskai" / "tasks.db"
        self.engine = None
        self.SessionLocal = None
        self._setup_database()

    def _setup_database(self):
        """Setup database connection and create tables"""
        try:
            # Ensure .pytaskai directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create engine
            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                echo=False,  # Set to True for SQL debugging
                connect_args={"check_same_thread": False},
            )

            # Create sessionmaker
            self.SessionLocal = sessionmaker(bind=self.engine)

            # Create all tables
            Base.metadata.create_all(bind=self.engine)

            logger.info(f"Database initialized at: {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise

    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_all_tasks(self, include_subtasks: bool = True) -> List[Dict[str, Any]]:
        """Get all tasks from database"""
        try:
            with self.get_session() as session:
                tasks = session.query(TaskDB).all()
                return [task.to_dict() for task in tasks]
        except Exception as e:
            logger.error(f"Failed to get all tasks: {e}")
            return []

    def get_task_by_id(
        self, task_id: int, include_subtasks: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get a specific task by ID"""
        try:
            with self.get_session() as session:
                task = session.query(TaskDB).filter(TaskDB.id == task_id).first()
                return task.to_dict() if task else None
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None

    def create_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new task in database"""
        try:
            with self.get_session() as session:
                # Remove subtasks from task_data, we'll handle them separately
                subtasks_data = task_data.pop("subtasks", [])

                # Convert enum strings to enum objects
                if "status" in task_data and isinstance(task_data["status"], str):
                    task_data["status"] = TaskStatus(task_data["status"])
                if "priority" in task_data and isinstance(task_data["priority"], str):
                    task_data["priority"] = TaskPriority(task_data["priority"])
                if "type" in task_data and isinstance(task_data["type"], str):
                    task_data["type"] = TaskType(task_data["type"])
                if "severity" in task_data and isinstance(task_data["severity"], str):
                    task_data["severity"] = BugSeverity(task_data["severity"])

                # Convert datetime strings to datetime objects
                for field in ["created_at", "updated_at", "completed_at"]:
                    if field in task_data and isinstance(task_data[field], str):
                        task_data[field] = datetime.fromisoformat(task_data[field])

                # Create task
                task = TaskDB(**task_data)
                session.add(task)
                session.flush()  # Get the ID

                # Create subtasks
                for subtask_data in subtasks_data:
                    subtask_data["parent_task_id"] = task.id
                    if "status" in subtask_data and isinstance(
                        subtask_data["status"], str
                    ):
                        subtask_data["status"] = TaskStatus(subtask_data["status"])

                    # Convert datetime strings
                    for field in ["created_at", "updated_at"]:
                        if field in subtask_data and isinstance(
                            subtask_data[field], str
                        ):
                            subtask_data[field] = datetime.fromisoformat(
                                subtask_data[field]
                            )

                    subtask = SubTaskDB(**subtask_data)
                    session.add(subtask)

                session.commit()

                # Return the created task with subtasks
                return self.get_task_by_id(task.id)

        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return None

    def update_task(
        self, task_id: int, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing task"""
        try:
            with self.get_session() as session:
                task = session.query(TaskDB).filter(TaskDB.id == task_id).first()
                if not task:
                    return None

                # Handle enum conversions
                if "status" in updates and isinstance(updates["status"], str):
                    updates["status"] = TaskStatus(updates["status"])
                if "priority" in updates and isinstance(updates["priority"], str):
                    updates["priority"] = TaskPriority(updates["priority"])
                if "type" in updates and isinstance(updates["type"], str):
                    updates["type"] = TaskType(updates["type"])
                if "severity" in updates and isinstance(updates["severity"], str):
                    updates["severity"] = BugSeverity(updates["severity"])

                # Update fields
                for field, value in updates.items():
                    if hasattr(task, field):
                        setattr(task, field, value)

                # Auto-update timestamp
                task.updated_at = datetime.now()

                session.commit()
                return self.get_task_by_id(task_id)

        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return None

    def delete_task(self, task_id: int) -> bool:
        """Delete a task and its subtasks"""
        try:
            with self.get_session() as session:
                task = session.query(TaskDB).filter(TaskDB.id == task_id).first()
                if not task:
                    return False

                session.delete(task)  # Cascade will delete subtasks
                session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False

    def update_subtask(
        self, task_id: int, subtask_id: int, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a subtask"""
        try:
            with self.get_session() as session:
                subtask = (
                    session.query(SubTaskDB)
                    .filter(
                        SubTaskDB.id == subtask_id, SubTaskDB.parent_task_id == task_id
                    )
                    .first()
                )

                if not subtask:
                    return None

                # Handle status enum conversion
                if "status" in updates and isinstance(updates["status"], str):
                    updates["status"] = TaskStatus(updates["status"])

                # Update fields
                for field, value in updates.items():
                    if hasattr(subtask, field):
                        setattr(subtask, field, value)

                # Auto-update timestamp
                subtask.updated_at = datetime.now()

                session.commit()
                return self.get_task_by_id(task_id)

        except Exception as e:
            logger.error(f"Failed to update subtask {subtask_id}: {e}")
            return None

    def get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get tasks filtered by status"""
        try:
            with self.get_session() as session:
                status_enum = TaskStatus(status)
                tasks = session.query(TaskDB).filter(TaskDB.status == status_enum).all()
                return [task.to_dict() for task in tasks]
        except Exception as e:
            logger.error(f"Failed to get tasks by status {status}: {e}")
            return []

    def get_tasks_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """Get tasks filtered by priority"""
        try:
            with self.get_session() as session:
                priority_enum = TaskPriority(priority)
                tasks = (
                    session.query(TaskDB).filter(TaskDB.priority == priority_enum).all()
                )
                return [task.to_dict() for task in tasks]
        except Exception as e:
            logger.error(f"Failed to get tasks by priority {priority}: {e}")
            return []

    def get_tasks_by_type(self, task_type: str) -> List[Dict[str, Any]]:
        """Get tasks filtered by type"""
        try:
            with self.get_session() as session:
                type_enum = TaskType(task_type)
                tasks = session.query(TaskDB).filter(TaskDB.type == type_enum).all()
                return [task.to_dict() for task in tasks]
        except Exception as e:
            logger.error(f"Failed to get tasks by type {task_type}: {e}")
            return []

    def get_next_task_id(self) -> int:
        """Get the next available task ID"""
        try:
            with self.get_session() as session:
                max_id = session.query(TaskDB.id).order_by(TaskDB.id.desc()).first()
                return (max_id[0] + 1) if max_id else 1
        except Exception as e:
            logger.error(f"Failed to get next task ID: {e}")
            return 1

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of the database"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"tasks_backup_{timestamp}.db"

        try:
            import shutil

            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            raise


# Global database manager instance
_db_manager = None


def get_db_manager(project_root: str = ".") -> DatabaseManager:
    """Get or create the global database manager instance"""
    # Always resolve the project_root to an absolute path to maintain a single
    # consistent DatabaseManager instance regardless of how the path was
    # supplied (e.g., ".", "./", or an absolute path).
    normalized_root = Path(project_root).resolve()

    global _db_manager
    if _db_manager is None or _db_manager.project_root != normalized_root:
        _db_manager = DatabaseManager(normalized_root)
    return _db_manager


def migrate_json_to_sqlite(project_root: str = ".") -> bool:
    """Migrate existing JSON tasks to SQLite database"""
    try:
        from .utils import get_tasks_file_path
        import json

        # Get existing JSON data
        tasks_file = get_tasks_file_path(project_root)
        if not tasks_file.exists():
            logger.info("No existing tasks.json file to migrate")
            return True

        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different JSON formats
        if isinstance(data, dict) and "tasks" in data:
            tasks_data = data["tasks"]
        elif isinstance(data, list):
            tasks_data = data
        else:
            logger.error("Invalid JSON format for migration")
            return False

        # Migrate to SQLite
        db_manager = get_db_manager(project_root)
        migrated_count = 0

        for task_data in tasks_data:
            if db_manager.create_task(task_data):
                migrated_count += 1
            else:
                logger.warning(
                    f"Failed to migrate task: {task_data.get('id', 'unknown')}"
                )

        logger.info(f"Successfully migrated {migrated_count} tasks to SQLite")

        # Backup the original JSON file
        backup_path = tasks_file.with_suffix(".json.backup")
        tasks_file.rename(backup_path)
        logger.info(f"Original JSON file backed up to: {backup_path}")

        return True

    except Exception as e:
        logger.error(f"Failed to migrate JSON to SQLite: {e}")
        return False
