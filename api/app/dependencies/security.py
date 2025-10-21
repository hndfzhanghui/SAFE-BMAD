"""
Security Dependencies

This module contains security-related dependency injection functions for FastAPI.
"""

from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.dependencies.database import get_db_session

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Dependency to get current user token from Authorization header

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        str: User token (subject)

    Raises:
        HTTPException: If authentication fails
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Not authenticated",
                "error_code": "AUTHENTICATION_REQUIRED",
                "details": {"message": "Authorization header is required"}
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        user_id = verify_token(token)
        if user_id is None:
            raise AuthenticationError("Invalid authentication token")
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid authentication token",
                "error_code": "INVALID_TOKEN",
                "details": {"message": "Token is invalid or expired"}
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Dependency to get optional current user token

    Args:
        credentials: HTTP Bearer credentials (optional)

    Returns:
        Optional[str]: User token if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        user_id = verify_token(token)
        return user_id
    except JWTError:
        return None


async def get_current_user_id(
    user_token: str = Depends(get_current_user_token)
) -> int:
    """
    Dependency to get current user ID

    Args:
        user_token: User token

    Returns:
        int: User ID

    Raises:
        HTTPException: If user ID is invalid
    """
    try:
        return int(user_token)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid user ID in token",
                "error_code": "INVALID_USER_ID",
                "details": {"user_id": user_token}
            }
        )


async def require_permission(permission: str):
    """
    Dependency factory to require specific permission

    Args:
        permission: Required permission

    Returns:
        Dependency function
    """
    async def permission_dependency(
        user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_db_session)
    ):
        # TODO: Implement user permission checking
        # This would typically involve querying the database for user permissions
        # For now, we'll assume all authenticated users have basic permissions

        # Example implementation (to be completed when user model is defined):
        # from app.crud.user import user_crud
        # user = await user_crud.get(session, user_id)
        # if not user or not user.has_permission(permission):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail={
        #             "error": "Insufficient permissions",
        #             "error_code": "INSUFFICIENT_PERMISSIONS",
        #             "details": {
        #                 "required_permission": permission,
        #                 "user_id": user_id
        #             }
        #         }
        #     )

        return user_id

    return permission_dependency


# Common permission dependencies
require_admin_permission = require_permission("admin")
require_operator_permission = require_permission("operator")
require_analyst_permission = require_permission("analyst")
require_viewer_permission = require_permission("viewer")


async def require_same_user_or_permission(
    target_user_id: int,
    permission: str = "admin"
):
    """
    Dependency factory to require user to be the same as target user or have specific permission

    Args:
        target_user_id: Target user ID
        permission: Required permission to access other users' data

    Returns:
        Dependency function
    """
    async def same_user_or_permission_dependency(
        current_user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_db_session)
    ):
        # User can access their own data
        if current_user_id == target_user_id:
            return current_user_id

        # Otherwise, they need the required permission
        # TODO: Implement permission checking
        # For now, we'll allow self-access only
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Cannot access another user's data",
                "error_code": "ACCESS_DENIED",
                "details": {
                    "target_user_id": target_user_id,
                    "current_user_id": current_user_id,
                    "required_permission": permission
                }
            }
        )

    return same_user_or_permission_dependency


async def get_refresh_token_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Dependency to get user from refresh token

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        str: User token

    Raises:
        HTTPException: If refresh token is invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Refresh token required",
                "error_code": "REFRESH_TOKEN_REQUIRED",
                "details": {"message": "Authorization header with refresh token is required"}
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        user_id = verify_token(token, token_type="refresh")
        if user_id is None:
            raise AuthenticationError("Invalid refresh token")
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid refresh token",
                "error_code": "INVALID_REFRESH_TOKEN",
                "details": {"message": "Refresh token is invalid or expired"}
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            },
            headers={"WWW-Authenticate": "Bearer"},
        )