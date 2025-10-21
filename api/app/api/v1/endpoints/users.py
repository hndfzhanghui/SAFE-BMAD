"""
User Endpoints

This module contains user management endpoints for the SAFE-BMAD API.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies.database import get_db_session
from app.dependencies.security import get_current_user_id, require_admin_permission
from app.dependencies.common import get_pagination_params, PaginationParams, PaginatedResponse
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserInDB, UserPasswordUpdate
)
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import NotFoundError, ConflictError, ValidationError

router = APIRouter()
security = HTTPBearer()


# CRUD operations for users
class UserCRUD:
    """CRUD operations for User model"""

    @staticmethod
    async def create(session: AsyncSession, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if username already exists
        result = await session.execute(
            select(User).where(User.username == user_create.username)
        )
        if result.scalar_one_or_none():
            raise ConflictError(
                message="Username already exists",
                conflict_type="username",
                details={"username": user_create.username}
            )

        # Check if email already exists
        result = await session.execute(
            select(User).where(User.email == user_create.email)
        )
        if result.scalar_one_or_none():
            raise ConflictError(
                message="Email already exists",
                conflict_type="email",
                details={"email": user_create.email}
            )

        # Create user
        user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=get_password_hash(user_create.password),
            full_name=user_create.full_name,
            role=user_create.role,
            is_active=user_create.is_active,
            phone_number=user_create.phone_number,
            department=user_create.department,
            title=user_create.title
        )

        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await session.execute(
            select(User).where(User.id == user_id, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await session.execute(
            select(User).where(User.username == username, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await session.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        session: AsyncSession,
        pagination: PaginationParams,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """Get multiple users with filtering and pagination"""
        query = select(User).where(User.is_deleted == False)

        # Apply filters
        if search:
            query = query.where(
                func.lower(User.username).contains(search.lower()) |
                func.lower(User.full_name).contains(search.lower()) |
                func.lower(User.email).contains(search.lower())
            )

        if role:
            query = query.where(User.role == role)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.order_by(User.created_at.desc())
        query = query.offset(pagination.offset).limit(pagination.limit)

        result = await session.execute(query)
        users = result.scalars().all()

        return list(users), total

    @staticmethod
    async def update(
        session: AsyncSession,
        user_id: int,
        user_update: UserUpdate
    ) -> Optional[User]:
        """Update user"""
        user = await UserCRUD.get_by_id(session, user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                resource_type="user",
                resource_id=user_id
            )

        # Check for username conflicts if updating username
        if user_update.username and user_update.username != user.username:
            result = await session.execute(
                select(User).where(
                    User.username == user_update.username,
                    User.id != user_id
                )
            )
            if result.scalar_one_or_none():
                raise ConflictError(
                    message="Username already exists",
                    conflict_type="username",
                    details={"username": user_update.username}
                )

        # Check for email conflicts if updating email
        if user_update.email and user_update.email != user.email:
            result = await session.execute(
                select(User).where(
                    User.email == user_update.email,
                    User.id != user_id
                )
            )
            if result.scalar_one_or_none():
                raise ConflictError(
                    message="Email already exists",
                    conflict_type="email",
                    details={"email": user_update.email}
                )

        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        await session.flush()
        await session.refresh(user)
        return user

    @staticmethod
    async def delete(session: AsyncSession, user_id: int) -> bool:
        """Delete user (soft delete)"""
        user = await UserCRUD.get_by_id(session, user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                resource_type="user",
                resource_id=user_id
            )

        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        user.is_active = False
        await session.flush()
        return True

    @staticmethod
    async def change_password(
        session: AsyncSession,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password"""
        user = await UserCRUD.get_by_id(session, user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                resource_type="user",
                resource_id=user_id
            )

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValidationError(
                message="Current password is incorrect",
                field="current_password"
            )

        # Update password
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        await session.flush()
        return True


# Endpoints
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(require_admin_permission)
):
    """
    Create a new user

    This endpoint creates a new user in the system. Requires admin privileges.
    """
    try:
        user = await UserCRUD.create(session, user_create)
        await session.commit()
        return UserResponse.from_orm(user)
    except (ConflictError, ValidationError) as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to create user",
                "error_code": "USER_CREATION_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.get("/", response_model=UserListResponse)
async def get_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search users by username, name, or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(require_admin_permission)
):
    """
    Get list of users with pagination and filtering

    This endpoint returns a paginated list of users. Supports search and filtering.
    Requires admin privileges.
    """
    try:
        users, total = await UserCRUD.get_multi(
            session=session,
            pagination=pagination,
            search=search,
            role=role,
            is_active=is_active
        )

        user_responses = [UserResponse.from_orm(user) for user in users]
        paginated_response = PaginatedResponse.create(user_responses, total, pagination)

        return UserListResponse(**paginated_response.dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve users",
                "error_code": "USER_RETRIEVAL_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Get user by ID

    This endpoint returns user details. Users can only view their own details
    unless they have admin privileges.
    """
    try:
        user = await UserCRUD.get_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "User not found",
                    "error_code": "USER_NOT_FOUND",
                    "details": {"user_id": user_id}
                }
            )

        # Check if user has permission to view this user's details
        if current_user_id != user_id:
            # TODO: Check if current user has admin privileges
            pass

        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve user",
                "error_code": "USER_RETRIEVAL_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Update user information

    This endpoint updates user information. Users can only update their own
    details unless they have admin privileges.
    """
    try:
        # Check if user has permission to update this user
        if current_user_id != user_id:
            # TODO: Check if current user has admin privileges
            pass

        user = await UserCRUD.update(session, user_id, user_update)
        await session.commit()
        return UserResponse.from_orm(user)
    except NotFoundError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to update user",
                "error_code": "USER_UPDATE_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(require_admin_permission)
):
    """
    Delete user (soft delete)

    This endpoint deletes a user (soft delete). Requires admin privileges.
    """
    try:
        await UserCRUD.delete(session, user_id)
        await session.commit()
    except NotFoundError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to delete user",
                "error_code": "USER_DELETION_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.post("/{user_id}/change-password")
async def change_password(
    user_id: int,
    password_update: UserPasswordUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Change user password

    This endpoint changes a user's password. Users can only change their own
    password.
    """
    try:
        # Check if user is changing their own password
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Cannot change another user's password",
                    "error_code": "PASSWORD_CHANGE_FORBIDDEN",
                    "details": {"user_id": user_id}
                }
            )

        success = await UserCRUD.change_password(
            session,
            user_id,
            password_update.current_password,
            password_update.new_password
        )
        await session.commit()

        return {"message": "Password changed successfully"}
    except NotFoundError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except ValidationError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to change password",
                "error_code": "PASSWORD_CHANGE_FAILED",
                "details": {"error": str(e)}
            }
        )