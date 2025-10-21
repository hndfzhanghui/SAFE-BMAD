"""
Database Connection Utilities for SAFE-BMAD System
"""

import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)

# Global database instances
async_engine = None
sync_engine = None
async_session_factory = None
sync_session_factory = None


def get_database_connection():
    """
    Get database connection instance
    Returns both async and sync engines
    """
    global async_engine, sync_engine, async_session_factory, sync_session_factory

    if async_engine is None:
        settings = get_settings()

        # Parse database URL for async version
        database_url = settings.database_url
        if database_url.startswith("postgresql://"):
            async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            raise ValueError("Unsupported database URL format")

        # Create async engine
        async_engine = create_async_engine(
            async_database_url,
            echo=settings.debug,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
        )

        # Create sync engine
        sync_engine = create_engine(
            database_url,
            echo=settings.debug,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
        )

        # Create session factories
        async_session_factory = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        sync_session_factory = sessionmaker(
            bind=sync_engine,
            autocommit=False,
            autoflush=False
        )

        logger.info("Database connections initialized")

    return {
        "async_engine": async_engine,
        "sync_engine": sync_engine,
        "async_session_factory": async_session_factory,
        "sync_session_factory": sync_session_factory
    }


@asynccontextmanager
async def get_async_session():
    """
    Get async database session context manager
    """
    connections = get_database_connection()
    session_factory = connections["async_session_factory"]

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
def get_sync_session():
    """
    Get sync database session context manager
    """
    connections = get_database_connection()
    session_factory = connections["sync_session_factory"]

    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def check_database_health():
    """
    Check database connection health
    Returns health status information
    """
    try:
        connections = get_database_connection()
        engine = connections["async_engine"]

        start_time = asyncio.get_event_loop().time()

        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()

        response_time = (asyncio.get_event_loop().time() - start_time) * 1000

        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "details": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Database connection failed"
        }


async def execute_query(query: str, params: dict = None):
    """
    Execute a database query
    Returns query results
    """
    try:
        connections = get_database_connection()
        engine = connections["async_engine"]

        async with engine.begin() as conn:
            result = await conn.execute(text(query), params or {})
            return result.fetchall()
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        raise


async def initialize_database():
    """
    Initialize database with schema and data
    """
    try:
        # TODO: Add database initialization logic
        # This could include running migrations, creating tables, etc.
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


async def close_database_connections():
    """
    Close all database connections
    """
    global async_engine, sync_engine

    try:
        if async_engine:
            await async_engine.dispose()
            async_engine = None

        if sync_engine:
            sync_engine.dispose()
            sync_engine = None

        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")


# Development in-memory database for testing
def create_test_database():
    """
    Create an in-memory SQLite database for testing
    """
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
        echo=True
    )

    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    return engine, session_factory