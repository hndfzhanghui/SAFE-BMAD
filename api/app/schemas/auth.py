"""
Authentication Schemas
Pydantic models for authentication related operations
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class UserLogin(BaseModel):
    """用户登录请求模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")

    @validator('username')
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        if not v:
            raise ValueError('密码不能为空')
        return v


class UserRegister(BaseModel):
    """用户注册请求模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: str = Field(..., min_length=1, max_length=100, description="全名")
    password: str = Field(..., min_length=8, max_length=100, description="密码")
    confirm_password: str = Field(..., min_length=8, max_length=100, description="确认密码")

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v.strip()

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密码和确认密码不匹配')
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!"
            }
        }


class Token(BaseModel):
    """Token响应模式"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="访问令牌过期时间(秒)")
    refresh_expires_in: int = Field(..., description="刷新令牌过期时间(秒)")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "refresh_expires_in": 86400
            }
        }


class TokenRefresh(BaseModel):
    """Token刷新请求模式"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordChange(BaseModel):
    """密码修改请求模式"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=100, description="新密码")
    confirm_password: str = Field(..., min_length=8, max_length=100, description="确认新密码")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码和确认密码不匹配')
        return v

    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            }
        }


class PasswordReset(BaseModel):
    """密码重置请求模式"""
    email: EmailStr = Field(..., description="邮箱地址")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """密码重置确认模式"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=100, description="新密码")
    confirm_password: str = Field(..., min_length=8, max_length=100, description="确认新密码")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码和确认密码不匹配')
        return v


class EmailVerification(BaseModel):
    """邮箱验证模式"""
    token: str = Field(..., description="验证令牌")


class UserResponse(BaseModel):
    """用户响应模式"""
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """认证响应模式"""
    user: UserResponse
    tokens: Token
    message: str = Field(default="认证成功", description="响应消息")

    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "username": "testuser",
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "is_active": True,
                    "is_superuser": False,
                    "is_verified": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "last_login": "2024-01-01T12:00:00Z"
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "refresh_expires_in": 86400
                },
                "message": "登录成功"
            }
        }


class MessageResponse(BaseModel):
    """通用消息响应模式"""
    message: str = Field(..., description="响应消息")
    success: bool = Field(default=True, description="操作是否成功")
    data: Optional[Dict[str, Any]] = Field(default=None, description="附加数据")

    class Config:
        schema_extra = {
            "example": {
                "message": "操作成功",
                "success": true,
                "data": {}
            }
        }


class UserProfile(BaseModel):
    """用户档案模式"""
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = Field(default=0, description="登录次数")

    class Config:
        from_attributes = True


class PermissionCheck(BaseModel):
    """权限检查模式"""
    has_permission: bool = Field(..., description="是否有权限")
    permission: str = Field(..., description="检查的权限")
    user_id: int = Field(..., description="用户ID")


class ApiKeyCreate(BaseModel):
    """API Key创建模式"""
    name: str = Field(..., min_length=1, max_length=100, description="API Key名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

    class Config:
        schema_extra = {
            "example": {
                "name": "My API Key",
                "description": "用于外部系统集成的API Key",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }


class ApiKeyResponse(BaseModel):
    """API Key响应模式"""
    id: int
    name: str
    api_key: str
    description: Optional[str]
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    last_used: Optional[datetime]
    usage_count: int = Field(default=0, description="使用次数")

    class Config:
        from_attributes = True