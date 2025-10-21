"""
Authentication Endpoints
用户认证相关的API端点
"""

from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password,
    generate_password_reset_token,
    verify_password_reset_token,
    generate_verification_token,
    verify_verification_token,
    PasswordValidator,
    SecurityHeaders,
    rate_limiter
)
from app.core.exceptions import AuthenticationError, ValidationError, NotFoundError
from app.dependencies.database import get_db_session
from app.dependencies.security import get_current_user_id, get_refresh_token_user
from app.models.user import User
from app.schemas.auth import (
    UserLogin,
    UserRegister,
    Token,
    TokenRefresh,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerification,
    AuthResponse,
    UserResponse,
    MessageResponse
)

settings = get_settings()
router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    session: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    用户注册
    """
    # 检查速率限制
    client_ip = request.client.host
    is_allowed, rate_info = rate_limiter.is_allowed(f"register:{client_ip}", limit=5, window=300)  # 5次/5分钟

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Too many registration attempts",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "details": rate_info
            }
        )

    # 检查用户名是否已存在
    result = await session.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Username already exists",
                "error_code": "USERNAME_EXISTS",
                "details": {"username": user_data.username}
            }
        )

    # 检查邮箱是否已存在
    result = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Email already registered",
                "error_code": "EMAIL_EXISTS",
                "details": {"email": user_data.email}
            }
        )

    # 验证密码强度
    password_validation = PasswordValidator.validate_password_strength(user_data.password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Password does not meet requirements",
                "error_code": "WEAK_PASSWORD",
                "details": {"errors": password_validation["errors"]}
            }
        )

    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    verification_token = generate_verification_token(user_data.email)

    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        is_verified=False,
        verification_token=verification_token
    )

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    # TODO: 发送验证邮件
    # await send_verification_email(user_data.email, verification_token)

    # 创建tokens
    access_token = create_access_token(subject=db_user.id)
    refresh_token = create_refresh_token(subject=db_user.id)

    # 更新最后登录时间
    db_user.last_login = datetime.utcnow()
    db_user.login_count = 1
    await session.commit()

    return AuthResponse(
        user=UserResponse.from_orm(db_user),
        tokens=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_expires_in=settings.refresh_token_expire_days * 24 * 60 * 60
        ),
        message="注册成功，请查看邮箱验证账户"
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    session: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    用户登录
    """
    # 检查速率限制
    client_ip = request.client.host
    is_allowed, rate_info = rate_limiter.is_allowed(f"login:{client_ip}", limit=10, window=300)  # 10次/5分钟

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Too many login attempts",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "details": rate_info
            }
        )

    # 查找用户（支持用户名或邮箱登录）
    result = await session.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid username or password",
                "error_code": "INVALID_CREDENTIALS"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Account is disabled",
                "error_code": "ACCOUNT_DISABLED"
            }
        )

    # 创建tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    # 更新最后登录时间和登录次数
    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    await session.commit()

    return AuthResponse(
        user=UserResponse.from_orm(user),
        tokens=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_expires_in=settings.refresh_token_expire_days * 24 * 60 * 60
        ),
        message="登录成功"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    session: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    刷新访问令牌
    """
    # 验证refresh token
    user_id = verify_token(token_data.refresh_token, token_type="refresh")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid refresh token",
                "error_code": "INVALID_REFRESH_TOKEN"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否存在且活跃
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "User not found or inactive",
                "error_code": "USER_INACTIVE"
            }
        )

    # 创建新的access token
    access_token = create_access_token(subject=user.id)

    return Token(
        access_token=access_token,
        refresh_token=token_data.refresh_token,  # 保持原refresh token
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_expires_in=settings.refresh_token_expire_days * 24 * 60 * 60
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    用户登出
    """
    # TODO: 实现token黑名单机制
    # 将token添加到黑名单，防止被继续使用

    return MessageResponse(
        message="登出成功",
        success=True
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    修改密码
    """
    # 获取当前用户
    result = await session.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User not found",
                "error_code": "USER_NOT_FOUND"
            }
        )

    # 验证当前密码
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Current password is incorrect",
                "error_code": "INVALID_CURRENT_PASSWORD"
            }
        )

    # 验证新密码强度
    password_validation = PasswordValidator.validate_password_strength(password_data.new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "New password does not meet requirements",
                "error_code": "WEAK_PASSWORD",
                "details": {"errors": password_validation["errors"]}
            }
        )

    # 更新密码
    user.hashed_password = get_password_hash(password_data.new_password)
    user.updated_at = datetime.utcnow()
    await session.commit()

    return MessageResponse(
        message="密码修改成功",
        success=True
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    password_data: PasswordReset,
    request: Request,
    session: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    忘记密码 - 发送重置邮件
    """
    # 检查速率限制
    client_ip = request.client.host
    is_allowed, rate_info = rate_limiter.is_allowed(f"reset_password:{client_ip}", limit=3, window=900)  # 3次/15分钟

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Too many password reset attempts",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "details": rate_info
            }
        )

    # 查找用户
    result = await session.execute(select(User).where(User.email == password_data.email))
    user = result.scalar_one_or_none()

    # 无论用户是否存在都返回成功消息，防止邮箱枚举攻击
    if user:
        reset_token = generate_password_reset_token(user.email)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=settings.email_reset_token_expire_hours)
        await session.commit()

        # TODO: 发送密码重置邮件
        # await send_password_reset_email(user.email, reset_token)

    return MessageResponse(
        message="如果邮箱存在，密码重置链接已发送",
        success=True
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    重置密码
    """
    # 验证重置令牌
    email = verify_password_reset_token(reset_data.token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid or expired reset token",
                "error_code": "INVALID_RESET_TOKEN"
            }
        )

    # 查找用户
    result = await session.execute(
        select(User).where(
            User.email == email,
            User.reset_token == reset_data.token,
            User.reset_token_expires > datetime.utcnow()
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid or expired reset token",
                "error_code": "INVALID_RESET_TOKEN"
            }
        )

    # 验证新密码强度
    password_validation = PasswordValidator.validate_password_strength(reset_data.new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "New password does not meet requirements",
                "error_code": "WEAK_PASSWORD",
                "details": {"errors": password_validation["errors"]}
            }
        )

    # 更新密码
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    user.updated_at = datetime.utcnow()
    await session.commit()

    return MessageResponse(
        message="密码重置成功",
        success=True
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerification,
    session: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    验证邮箱
    """
    # 验证验证令牌
    email = verify_verification_token(verification_data.token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid or expired verification token",
                "error_code": "INVALID_VERIFICATION_TOKEN"
            }
        )

    # 查找用户
    result = await session.execute(
        select(User).where(
            User.email == email,
            User.verification_token == verification_data.token
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid verification token",
                "error_code": "INVALID_VERIFICATION_TOKEN"
            }
        )

    # 验证邮箱
    user.is_verified = True
    user.verification_token = None
    user.updated_at = datetime.utcnow()
    await session.commit()

    return MessageResponse(
        message="邮箱验证成功",
        success=True
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    获取当前用户信息
    """
    result = await session.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User not found",
                "error_code": "USER_NOT_FOUND"
            }
        )

    return UserResponse.from_orm(user)


# 添加安全头部中间件
@router.middleware("http")
async def add_security_headers(request: Request, call_next):
    """添加安全头部"""
    response = await call_next(request)

    security_headers = SecurityHeaders.get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value

    return response