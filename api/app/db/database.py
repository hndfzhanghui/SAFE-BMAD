"""
Database Configuration and Connection Management

This module contains database configuration and connection management
for the SAFE-BMAD system using SQLAlchemy async support.
"""

import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.exceptions import DatabaseError

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""
    pass


# Database engines
async_engine = None
sync_engine = None

# Session makers
AsyncSessionLocal = None
SessionLocal = None


def create_database_engines():
    """
    Create database engines for both async and sync operations
    """
    global async_engine, sync_engine, AsyncSessionLocal, SessionLocal

    if async_engine is None:
        # Create async engine
        async_database_url = settings.get_database_async_url()
        async_engine = create_async_engine(
            async_database_url,
            echo=settings.db_echo or settings.debug,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            # Enable connection pool pre-ping
            pool_pre_ping=True,
        )

        # Create async session maker
        AsyncSessionLocal = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    if sync_engine is None:
        # Create sync engine for migrations and admin operations
        sync_engine = create_engine(
            settings.database_url,
            echo=settings.db_echo or settings.debug,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=True,
        )

        # Create sync session maker
        SessionLocal = sessionmaker(
            bind=sync_engine,
            autocommit=False,
            autoflush=False,
        )

    # Register event listeners
    register_event_listeners()


def register_event_listeners():
    """Register SQLAlchemy event listeners"""

    @event.listens_for(async_engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set SQLite pragmas if using SQLite (for testing)"""
        if "sqlite" in settings.database_url:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    @event.listens_for(async_engine.sync_engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log slow queries"""
        if not settings.debug:
            return

        context._query_start_time = asyncio.get_event_loop().time()

    @event.listens_for(async_engine.sync_engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log slow queries after execution"""
        if not settings.debug:
            return

        total = asyncio.get_event_loop().time() - context._query_start_time
        if total > 1.0:  # Log queries taking more than 1 second
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Slow query ({total:.2f}s): {statement}")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session

    Yields:
        AsyncSession: Database session
    """
    if AsyncSessionLocal is None:
        create_database_engines()

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise DatabaseError(
                message="Database session error",
                operation="session_management",
                details={"error": str(e)}
            )
        finally:
            await session.close()


def get_sync_session():
    """
    Get sync database session (for migrations and admin operations)

    Yields:
        Session: Database session
    """
    if SessionLocal is None:
        create_database_engines()

    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise DatabaseError(
            message="Database session error",
            operation="session_management",
            details={"error": str(e)}
        )
    finally:
        session.close()


async def create_tables():
    """Create all database tables"""
    if async_engine is None:
        create_database_engines()

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables (use with caution!)"""
    if async_engine is None:
        create_database_engines()

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_database_connection() -> dict:
    """
    Check database connection health

    Returns:
        dict: Connection health status
    """
    try:
        if async_engine is None:
            create_database_engines()

        async with async_engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            await result.fetchone()

        return {
            "status": "healthy",
            "message": "Database connection successful",
            "database_url": settings.database_url.replace(
                settings.db_password, "***"
            ) if settings.db_password else settings.database_url
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Database connection failed",
            "error": str(e)
        }


async def close_database_connections():
    """Close all database connections"""
    global async_engine, sync_engine, AsyncSessionLocal, SessionLocal

    try:
        if async_engine:
            await async_engine.dispose()
            async_engine = None
            AsyncSessionLocal = None

        if sync_engine:
            sync_engine.dispose()
            sync_engine = None
            SessionLocal = None

    except Exception as e:
        raise DatabaseError(
            message="Error closing database connections",
            operation="connection_cleanup",
            details={"error": str(e)}
        )


# Test database support
def create_test_database():
    """
    Create in-memory SQLite database for testing

    Returns:
        tuple: (engine, session_maker)
    """
    test_engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
        echo=True
    )

    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    # Create tables
    Base.metadata.create_all(bind=test_engine)

    return test_engine, TestSessionLocal


# Dependency injection for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session

    Yields:
        AsyncSession: Database session
    """
    async for session in get_async_session():
        yield session


# Database transaction helper
class DatabaseTransaction:
    """Database transaction context manager"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction = None

    async def __aenter__(self):
        self.transaction = await self.session.begin()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.transaction.rollback()
        else:
            await self.transaction.commit()


# Database health check endpoint support
async def get_database_stats() -> dict:
    """
    Get database statistics for monitoring

    Returns:
        dict: Database statistics
    """
    try:
        if async_engine is None:
            create_database_engines()

        pool = async_engine.pool
        return {
            "pool_size": pool.size(),
            "pool_checked_in": pool.checkedin(),
            "pool_checked_out": pool.checkedout(),
            "pool_overflow": pool.overflow(),
            "pool_invalid": pool.invalid(),
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "unavailable"
        }