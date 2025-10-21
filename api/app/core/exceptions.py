"""
Custom Exception Classes

This module contains custom exception classes for the SAFE-BMAD API application.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseCustomException(Exception):
    """Base class for custom exceptions"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(BaseCustomException):
    """Validation error exception"""

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details, error_code="VALIDATION_ERROR")


class AuthenticationError(BaseCustomException):
    """Authentication error exception"""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(BaseCustomException):
    """Authorization error exception"""

    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message, details, error_code="AUTHORIZATION_ERROR")


class NotFoundError(BaseCustomException):
    """Resource not found error exception"""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id is not None:
            details["resource_id"] = resource_id
        super().__init__(message, details, error_code="NOT_FOUND_ERROR")


class ConflictError(BaseCustomException):
    """Resource conflict error exception"""

    def __init__(
        self,
        message: str = "Resource conflict",
        conflict_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if conflict_type:
            details["conflict_type"] = conflict_type
        super().__init__(message, details, error_code="CONFLICT_ERROR")


class BusinessLogicError(BaseCustomException):
    """Business logic error exception"""

    def __init__(
        self,
        message: str = "Business logic error",
        business_rule: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if business_rule:
            details["business_rule"] = business_rule
        super().__init__(message, details, error_code="BUSINESS_LOGIC_ERROR")


class ExternalServiceError(BaseCustomException):
    """External service error exception"""

    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        service_status: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if service_name:
            details["service_name"] = service_name
        if service_status:
            details["service_status"] = service_status
        super().__init__(message, details, error_code="EXTERNAL_SERVICE_ERROR")


class DatabaseError(BaseCustomException):
    """Database error exception"""

    def __init__(
        self,
        message: str = "Database error",
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        super().__init__(message, details, error_code="DATABASE_ERROR")


class RateLimitError(BaseCustomException):
    """Rate limit exceeded error exception"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if limit is not None:
            details["limit"] = limit
        if window is not None:
            details["window"] = window
        super().__init__(message, details, error_code="RATE_LIMIT_ERROR")


class FileUploadError(BaseCustomException):
    """File upload error exception"""

    def __init__(
        self,
        message: str = "File upload error",
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        allowed_types: Optional[list] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if file_name:
            details["file_name"] = file_name
        if file_size is not None:
            details["file_size"] = file_size
        if allowed_types:
            details["allowed_types"] = allowed_types
        super().__init__(message, details, error_code="FILE_UPLOAD_ERROR")


class ConfigurationError(BaseCustomException):
    """Configuration error exception"""

    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details, error_code="CONFIGURATION_ERROR")


class HTTPExceptionExtensions:
    """Extensions for FastAPI HTTPException"""

    @staticmethod
    def create_http_exception(
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """
        Create a standardized HTTPException

        Args:
            status_code: HTTP status code
            message: Error message
            error_code: Application-specific error code
            details: Additional error details

        Returns:
            HTTPException instance
        """
        content = {
            "error": message,
            "status_code": status_code,
        }

        if error_code:
            content["error_code"] = error_code

        if details:
            content["details"] = details

        return HTTPException(
            status_code=status_code,
            detail=content
        )

    @staticmethod
    def from_custom_exception(exc: BaseCustomException, status_code: int) -> HTTPException:
        """
        Convert custom exception to HTTPException

        Args:
            exc: Custom exception instance
            status_code: HTTP status code

        Returns:
            HTTPException instance
        """
        content = {
            "error": exc.message,
            "status_code": status_code,
        }

        if exc.error_code:
            content["error_code"] = exc.error_code

        if exc.details:
            content["details"] = exc.details

        return HTTPException(
            status_code=status_code,
            detail=content
        )


# HTTP status code mappings for custom exceptions
EXCEPTION_STATUS_MAPPINGS = {
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    BusinessLogicError: status.HTTP_400_BAD_REQUEST,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    FileUploadError: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def get_http_status_code(exception: BaseCustomException) -> int:
    """
    Get appropriate HTTP status code for custom exception

    Args:
        exception: Custom exception instance

    Returns:
        HTTP status code
    """
    return EXCEPTION_STATUS_MAPPINGS.get(
        type(exception),
        status.HTTP_500_INTERNAL_SERVER_ERROR
    )