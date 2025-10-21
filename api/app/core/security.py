"""
Security Configuration and Utilities

This module contains security-related functionality for authentication,
authorization, and password handling.
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from passlib.hash import bcrypt
from pydantic import ValidationError

from app.core.config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Token expiration time

    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Token expiration time

    Returns:
        JWT refresh token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string
        token_type: Type of token ("access" or "refresh")

    Returns:
        Token subject if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        # Check token type for refresh tokens
        if token_type == "refresh" and payload.get("type") != "refresh":
            return None

        subject: str = payload.get("sub")
        if subject is None:
            return None

        return subject
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    """
    Generate password reset token

    Args:
        email: User email address

    Returns:
        Password reset token
    """
    delta = timedelta(hours=settings.email_reset_token_expire_hours)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token

    Args:
        token: Password reset token

    Returns:
        Email address if valid, None otherwise
    """
    try:
        decoded_token = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return decoded_token["sub"]
    except JWTError:
        return None


def generate_api_key() -> str:
    """
    Generate a secure API key

    Returns:
        API key string
    """
    return secrets.token_urlsafe(32)


def generate_verification_token(email: str) -> str:
    """
    Generate email verification token

    Args:
        email: User email address

    Returns:
        Email verification token
    """
    delta = timedelta(hours=settings.email_verification_token_expire_hours)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_verification_token(token: str) -> Optional[str]:
    """
    Verify email verification token

    Args:
        token: Email verification token

    Returns:
        Email address if valid, None otherwise
    """
    try:
        decoded_token = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return decoded_token["sub"]
    except JWTError:
        return None


class PasswordValidator:
    """Password validation utility class"""

    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """
        Validate password strength

        Args:
            password: Password to validate

        Returns:
            Dictionary with validation results
        """
        result = {
            "is_valid": True,
            "errors": [],
            "score": 0
        }

        # Length check
        if len(password) < 8:
            result["errors"].append("Password must be at least 8 characters long")
            result["is_valid"] = False
        else:
            result["score"] += 1

        # Uppercase letter check
        if not any(c.isupper() for c in password):
            result["errors"].append("Password must contain at least one uppercase letter")
            result["is_valid"] = False
        else:
            result["score"] += 1

        # Lowercase letter check
        if not any(c.islower() for c in password):
            result["errors"].append("Password must contain at least one lowercase letter")
            result["is_valid"] = False
        else:
            result["score"] += 1

        # Number check
        if not any(c.isdigit() for c in password):
            result["errors"].append("Password must contain at least one number")
            result["is_valid"] = False
        else:
            result["score"] += 1

        # Special character check
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            result["errors"].append("Password must contain at least one special character")
            result["is_valid"] = False
        else:
            result["score"] += 1

        # Common password check
        common_passwords = [
            "password", "123456", "123456789", "12345678", "12345",
            "1234567", "1234567890", "1234", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey"
        ]

        if password.lower() in common_passwords:
            result["errors"].append("Password is too common, please choose a stronger password")
            result["is_valid"] = False
            result["score"] = max(0, result["score"] - 2)

        return result


class SecurityHeaders:
    """Security headers utility class"""

    @staticmethod
    def get_security_headers() -> dict:
        """
        Get security headers for HTTP responses

        Returns:
            Dictionary of security headers
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
        }


class RateLimiter:
    """Simple rate limiter for API endpoints"""

    def __init__(self):
        self.requests = {}

    def is_allowed(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed based on rate limit

        Args:
            key: Rate limit key (e.g., IP address, user ID)
            limit: Number of requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = datetime.utcnow().timestamp()

        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < window
        ]

        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True, {
                "allowed": True,
                "limit": limit,
                "remaining": limit - len(self.requests[key]),
                "reset_time": int(now + window)
            }
        else:
            return False, {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset_time": int(self.requests[key][0] + window)
            }


# Global rate limiter instance
rate_limiter = RateLimiter()