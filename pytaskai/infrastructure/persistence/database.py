"""
SQLAlchemy database setup and session management for PyTaskAI.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from pytaskai.infrastructure.config.database_config import DatabaseConfig
from pytaskai.infrastructure.persistence.models import Base


class Database:
    """
    Database connection and session management.

    Supports both synchronous and asynchronous operations.
    Uses SQLite with proper configuration for PyTaskAI.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize database with configuration."""
        self._config = config
        self._engine: Optional[object] = None
        self._async_engine: Optional[object] = None
        self._session_factory: Optional[sessionmaker] = None
        self._async_session_factory: Optional[async_sessionmaker] = None

    def initialize(self) -> None:
        """Initialize the database engine and session factory."""
        if self._config.is_sqlite:
            # Use synchronous engine for SQLite
            self._engine = create_engine(
                self._config.url,
                echo=self._config.echo,
                pool_pre_ping=self._config.pool_pre_ping,
                pool_recycle=self._config.pool_recycle,
                connect_args=self._config.connect_args or {},
            )

            # Enable foreign key constraints for SQLite
            @event.listens_for(self._engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
            )

            # Automatically create all tables for SQLite databases. This is
            # especially useful in unit / integration tests where the caller
            # may forget to invoke `create_tables()` explicitly, leading to
            # `OperationalError: no such table` failures.
            self.create_tables()
        else:
            # For future support of async databases like PostgreSQL
            async_url = self._config.url.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
            self._async_engine = create_async_engine(
                async_url,
                echo=self._config.echo,
                pool_pre_ping=self._config.pool_pre_ping,
                pool_recycle=self._config.pool_recycle,
            )

            self._async_session_factory = async_sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
            )

    def create_tables(self) -> None:
        """Create all database tables."""
        if not self._engine:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        Base.metadata.create_all(self._engine)

    def drop_tables(self) -> None:
        """Drop all database tables (for testing)."""
        if not self._engine:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        Base.metadata.drop_all(self._engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        return self._session_factory()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session (for future async support)."""
        if not self._async_session_factory:
            raise RuntimeError("Async database not configured.")

        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Session, None]:
        """
        Context manager for database transactions.

        Automatically commits on success, rolls back on exception.
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close database connections."""
        if self._engine:
            self._engine.dispose()


# Global database instance
_database: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _database
    if _database is None:
        config = DatabaseConfig.from_environment()
        _database = Database(config)
        _database.initialize()
    return _database


def initialize_database(config: Optional[DatabaseConfig] = None) -> Database:
    """Initialize the global database instance with optional config."""
    global _database

    if config is None:
        config = DatabaseConfig.from_environment()

    _database = Database(config)
    _database.initialize()
    return _database


def create_tables() -> None:
    """Create all database tables using the global database instance."""
    database = get_database()
    database.create_tables()


def reset_database() -> None:
    """Reset the global database instance (for testing)."""
    global _database
    if _database:
        _database.close()
    _database = None
