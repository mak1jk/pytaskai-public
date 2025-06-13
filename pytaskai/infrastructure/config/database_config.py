"""
Database configuration for PyTaskAI infrastructure layer.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration for database connections."""

    url: str
    echo: bool = False
    pool_pre_ping: bool = True
    pool_recycle: int = 3600
    connect_args: Optional[dict] = None

    @classmethod
    def from_environment(cls) -> "DatabaseConfig":
        """Create database configuration from environment variables."""
        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            # Default to SQLite for development
            database_path = os.getenv("DATABASE_PATH", "pytaskai.db")
            database_url = f"sqlite:///{database_path}"

        # SQLite-specific connection args
        connect_args = {}
        if database_url.startswith("sqlite"):
            connect_args = {
                "check_same_thread": False,  # Allow SQLite to be used across threads
                "timeout": 30,  # 30 second timeout for SQLite operations
            }

        return cls(
            url=database_url,
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            pool_pre_ping=os.getenv("DATABASE_POOL_PRE_PING", "true").lower() == "true",
            pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
            connect_args=connect_args if connect_args else None,
        )

    @classmethod
    def for_testing(cls, database_path: str = ":memory:") -> "DatabaseConfig":
        """Create database configuration for testing."""
        return cls(
            url=f"sqlite:///{database_path}",
            echo=False,
            pool_pre_ping=False,
            connect_args={"check_same_thread": False},
        )

    @property
    def is_sqlite(self) -> bool:
        """Check if the database is SQLite."""
        return self.url.startswith("sqlite")

    @property
    def is_in_memory(self) -> bool:
        """Check if the database is in-memory SQLite."""
        return self.url == "sqlite:///:memory:"
