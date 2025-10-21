"""
Database Dependencies

This module contains database-related dependency injection functions for FastAPI.
"""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session, DatabaseError
from app.core.exceptions import NotFoundError


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session

    Yields:
        AsyncSession: Database session

    Raises:
        HTTPException: If database connection fails
    """
    try:
        async for session in get_async_session():
            yield session
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Database connection failed",
                "error_code": "DATABASE_ERROR",
                "details": e.details
            }
        )


def get_transaction_session(
    session: AsyncSession = Depends(get_db_session)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with transaction support

    Args:
        session: Database session

    Yields:
        AsyncSession: Database session with transaction
    """
    async with DatabaseTransaction(session):
        yield session


async def get_db_with_health_check(
    session: AsyncSession = Depends(get_db_session)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with health check

    Args:
        session: Database session

    Yields:
        AsyncSession: Database session

    Raises:
        HTTPException: If database health check fails
    """
    try:
        # Perform a simple health check query
        await session.execute("SELECT 1")
        yield session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Database health check failed",
                "error_code": "DATABASE_HEALTH_CHECK_FAILED",
                "details": {"health_check_error": str(e)}
            }
        )