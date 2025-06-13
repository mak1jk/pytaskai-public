"""
SQLAlchemy database models for PyTaskAI persistence layer.

These models are separate from domain entities to maintain clean architecture.
They represent the database schema and should not contain business logic.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TaskModel(Base):
    """SQLAlchemy model for tasks."""

    __tablename__ = "tasks"

    # Primary key
    id = Column(String(50), primary_key=True)

    # Core task fields
    title = Column(String(255), nullable=False)
    external_url = Column(String(500), nullable=True)
    project = Column(String(100), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, default="Task")
    status = Column(String(50), nullable=False, default="Todo", index=True)
    description = Column(Text, nullable=True)

    # Assignment and hierarchy
    assignee = Column(String(100), nullable=True, index=True)
    parent_id = Column(String(50), ForeignKey("tasks.id"), nullable=True)

    # Metadata
    priority = Column(String(20), nullable=True, index=True)
    size = Column(String(20), nullable=True)

    # Dates
    start_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    subtasks = relationship(
        "TaskModel", back_populates="parent", cascade="all, delete-orphan"
    )
    parent = relationship("TaskModel", remote_side=[id], back_populates="subtasks")
    tags = relationship(
        "TaskTagModel", back_populates="task", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        # Index for assignee + status queries
        # Index for project + status queries
        # Index for due date queries
    )


class TaskTagModel(Base):
    """SQLAlchemy model for task tags (many-to-many relationship)."""

    __tablename__ = "task_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), ForeignKey("tasks.id"), nullable=False)
    tag_name = Column(String(50), nullable=False)

    # Relationships
    task = relationship("TaskModel", back_populates="tags")

    # Constraints
    __table_args__ = (UniqueConstraint("task_id", "tag_name", name="uq_task_tag"),)


class DocumentModel(Base):
    """SQLAlchemy model for documents."""

    __tablename__ = "documents"

    # Primary key
    id = Column(String(50), primary_key=True)

    # Core document fields
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=True)
    folder = Column(String(100), nullable=True, index=True)

    # Status flags
    is_draft = Column(Boolean, nullable=False, default=False, index=True)
    in_trash = Column(Boolean, nullable=False, default=False, index=True)

    # Dates
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TaskConfigModel(Base):
    """SQLAlchemy model for workspace configuration."""

    __tablename__ = "task_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Configuration type (singleton pattern)
    config_type = Column(String(50), nullable=False, default="default", unique=True)

    # Configuration data (JSON-like storage in separate tables for normalization)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships to configuration items
    assignees = relationship(
        "ConfigAssigneeModel", back_populates="config", cascade="all, delete-orphan"
    )
    statuses = relationship(
        "ConfigStatusModel", back_populates="config", cascade="all, delete-orphan"
    )
    priorities = relationship(
        "ConfigPriorityModel", back_populates="config", cascade="all, delete-orphan"
    )
    sizes = relationship(
        "ConfigSizeModel", back_populates="config", cascade="all, delete-orphan"
    )
    projects = relationship(
        "ConfigProjectModel", back_populates="config", cascade="all, delete-orphan"
    )
    tags = relationship(
        "ConfigTagModel", back_populates="config", cascade="all, delete-orphan"
    )


class ConfigAssigneeModel(Base):
    """SQLAlchemy model for configuration assignees."""

    __tablename__ = "config_assignees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey("task_config.id"), nullable=False)
    assignee = Column(String(100), nullable=False)

    config = relationship("TaskConfigModel", back_populates="assignees")

    __table_args__ = (
        UniqueConstraint("config_id", "assignee", name="uq_config_assignee"),
    )


class ConfigStatusModel(Base):
    """SQLAlchemy model for configuration statuses."""

    __tablename__ = "config_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey("task_config.id"), nullable=False)
    status = Column(String(50), nullable=False)

    config = relationship("TaskConfigModel", back_populates="statuses")

    __table_args__ = (UniqueConstraint("config_id", "status", name="uq_config_status"),)


class ConfigPriorityModel(Base):
    """SQLAlchemy model for configuration priorities."""

    __tablename__ = "config_priorities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey("task_config.id"), nullable=False)
    priority = Column(String(20), nullable=False)

    config = relationship("TaskConfigModel", back_populates="priorities")

    __table_args__ = (
        UniqueConstraint("config_id", "priority", name="uq_config_priority"),
    )


class ConfigSizeModel(Base):
    """SQLAlchemy model for configuration sizes."""

    __tablename__ = "config_sizes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey("task_config.id"), nullable=False)
    size = Column(String(20), nullable=False)

    config = relationship("TaskConfigModel", back_populates="sizes")

    __table_args__ = (UniqueConstraint("config_id", "size", name="uq_config_size"),)


class ConfigProjectModel(Base):
    """SQLAlchemy model for configuration projects."""

    __tablename__ = "config_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey("task_config.id"), nullable=False)
    project = Column(String(100), nullable=False)

    config = relationship("TaskConfigModel", back_populates="projects")

    __table_args__ = (
        UniqueConstraint("config_id", "project", name="uq_config_project"),
    )


class ConfigTagModel(Base):
    """SQLAlchemy model for configuration tags."""

    __tablename__ = "config_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey("task_config.id"), nullable=False)
    tag = Column(String(50), nullable=False)

    config = relationship("TaskConfigModel", back_populates="tags")

    __table_args__ = (UniqueConstraint("config_id", "tag", name="uq_config_tag"),)
