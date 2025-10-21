"""
User Schemas

This module contains Pydantic schemas for user-related API operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    """Base user schema with common fields"""

    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "viewer"
    is_active: bool = True
    phone_number: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None

    @validator("role")
    def validate_role(cls, v):
        """Validate user role"""
        allowed_roles = ["admin", "operator", "analyst", "viewer"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v

    @validator("username")
    def validate_username(cls, v):
        """Validate username"""
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("Username must be no more than 50 characters long")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, hyphens, and underscores")
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "analyst",
                "is_active": True,
                "phone_number": "+1-555-0123",
                "department": "Emergency Management",
                "title": "Senior Analyst"
            }
        }


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str

    @validator("password")
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "password": "SecurePassword123",
                "full_name": "John Doe",
                "role": "analyst",
                "is_active": True
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating an existing user"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

    @validator("role")
    def validate_role(cls, v):
        """Validate user role if provided"""
        if v is not None:
            allowed_roles = ["admin", "operator", "analyst", "viewer"]
            if v not in allowed_roles:
                raise ValueError(f"Role must be one of: {allowed_roles}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "full_name": "John Smith",
                "role": "operator",
                "is_active": True,
                "department": "Operations",
                "title": "Emergency Coordinator"
            }
        }


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password"""

    current_password: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123",
                "new_password": "NewPassword456"
            }
        }


class UserInDB(UserBase):
    """Schema for user data as stored in database"""

    id: int
    password_hash: str
    created_at: datetime
    updated_at: datetime
    is_email_verified: bool = False
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None

    class Config:
        orm_mode = True


class UserResponse(UserBase):
    """Schema for user response data"""

    id: int
    created_at: datetime
    updated_at: datetime
    is_email_verified: bool
    last_login_at: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "analyst",
                "is_active": True,
                "is_email_verified": True,
                "created_at": "2025-10-21T14:30:00.000Z",
                "updated_at": "2025-10-21T14:30:00.000Z",
                "last_login_at": "2025-10-21T15:00:00.000Z",
                "preferences": {
                    "theme": "dark",
                    "notifications": "enabled"
                }
            }
        }


class UserListResponse(BaseModel):
    """Schema for paginated user list response"""

    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john.doe@example.com",
                        "full_name": "John Doe",
                        "role": "analyst",
                        "is_active": True,
                        "created_at": "2025-10-21T14:30:00.000Z",
                        "updated_at": "2025-10-21T14:30:00.000Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1,
                "has_next": False,
                "has_prev": False
            }
        }


class UserLogin(BaseModel):
    """Schema for user login"""

    username: str
    password: str

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePassword123"
            }
        }


class UserLoginResponse(BaseModel):
    """Schema for user login response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john.doe@example.com",
                    "full_name": "John Doe",
                    "role": "analyst",
                    "is_active": True,
                    "created_at": "2025-10-21T14:30:00.000Z",
                    "updated_at": "2025-10-21T14:30:00.000Z"
                }
            }
        }


class UserRefreshToken(BaseModel):
    """Schema for refresh token request"""

    refresh_token: str

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }