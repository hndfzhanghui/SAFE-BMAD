"""
Common Dependencies

This module contains common dependency injection functions for FastAPI.
"""

from typing import Optional, Dict, Any, List
from math import ceil

from fastapi import Query, Depends, HTTPException, status
from pydantic import BaseModel, validator

from app.core.config import get_settings
from app.core.exceptions import ValidationError

settings = get_settings()


class PaginationParams(BaseModel):
    """Pagination parameters"""

    page: int = 1
    size: int = settings.default_page_size

    @validator("page")
    def validate_page(cls, v):
        if v < 1:
            raise ValueError("Page must be >= 1")
        return v

    @validator("size")
    def validate_size(cls, v):
        if v < 1:
            raise ValueError("Size must be >= 1")
        if v > settings.max_page_size:
            raise ValueError(f"Size must be <= {settings.max_page_size}")
        return v

    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get limit for database query"""
        return self.size


class OrderByParams(BaseModel):
    """Order by parameters"""

    field: str
    direction: str = "asc"

    @validator("direction")
    def validate_direction(cls, v):
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("Direction must be 'asc' or 'desc'")
        return v.lower()


class FilterParams(BaseModel):
    """Filter parameters"""

    # Common filters
    search: Optional[str] = None
    status: Optional[str] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    updated_after: Optional[str] = None
    updated_before: Optional[str] = None

    # Custom filters can be added here
    custom_filters: Dict[str, Any] = {}

    def get_filter_dict(self) -> Dict[str, Any]:
        """Convert filter params to dictionary for database queries"""
        filters = {}

        if self.search:
            filters["search"] = self.search

        if self.status:
            filters["status"] = self.status

        if self.created_after:
            filters["created_after"] = self.created_after

        if self.created_before:
            filters["created_before"] = self.created_before

        if self.updated_after:
            filters["updated_after"] = self.updated_after

        if self.updated_before:
            filters["updated_before"] = self.updated_before

        # Add custom filters
        filters.update(self.custom_filters)

        return filters


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description=f"Page size (max: {settings.max_page_size})"
    )
) -> PaginationParams:
    """
    Dependency to get pagination parameters

    Args:
        page: Page number (>= 1)
        size: Page size (1 to max_page_size)

    Returns:
        PaginationParams: Pagination parameters
    """
    return PaginationParams(page=page, size=size)


def get_order_by_params(
    order_by: Optional[str] = Query(None, description="Order by field (e.g., 'created_at:desc')"),
    allowed_fields: Optional[List[str]] = None
) -> Optional[OrderByParams]:
    """
    Dependency to get order by parameters

    Args:
        order_by: Order by string in format 'field:direction'
        allowed_fields: List of allowed fields for ordering

    Returns:
        Optional[OrderByParams]: Order by parameters or None

    Raises:
        HTTPException: If order_by format is invalid or field not allowed
    """
    if order_by is None:
        return None

    try:
        # Parse order_by string (format: "field:direction")
        parts = order_by.split(":")
        field = parts[0]
        direction = parts[1] if len(parts) > 1 else "asc"

        # Validate direction
        if direction.lower() not in ["asc", "desc"]:
            raise ValidationError(
                message="Invalid sort direction",
                field="order_by",
                value=order_by,
                details={"allowed_directions": ["asc", "desc"]}
            )

        # Validate field if allowed_fields is provided
        if allowed_fields and field not in allowed_fields:
            raise ValidationError(
                message="Invalid sort field",
                field="order_by",
                value=order_by,
                details={"allowed_fields": allowed_fields}
            )

        return OrderByParams(field=field, direction=direction.lower())

    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid order_by parameter format",
                "error_code": "INVALID_ORDER_BY",
                "details": {
                    "format": "field:direction",
                    "example": "created_at:desc",
                    "provided": order_by
                }
            }
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )


def get_filter_params(
    search: Optional[str] = Query(None, description="Search term"),
    status: Optional[str] = Query(None, description="Status filter"),
    created_after: Optional[str] = Query(None, description="Filter items created after this date (ISO format)"),
    created_before: Optional[str] = Query(None, description="Filter items created before this date (ISO format)"),
    updated_after: Optional[str] = Query(None, description="Filter items updated after this date (ISO format)"),
    updated_before: Optional[str] = Query(None, description="Filter items updated before this date (ISO format)")
) -> FilterParams:
    """
    Dependency to get filter parameters

    Args:
        search: Search term
        status: Status filter
        created_after: Created after date filter
        created_before: Created before date filter
        updated_after: Updated after date filter
        updated_before: Updated before date filter

    Returns:
        FilterParams: Filter parameters
    """
    return FilterParams(
        search=search,
        status=status,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before
    )


class PaginatedResponse(BaseModel):
    """Paginated response model"""

    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls,
        items: List[Any],
        total: int,
        pagination: PaginationParams
    ) -> "PaginatedResponse":
        """
        Create paginated response

        Args:
            items: List of items
            total: Total number of items
            pagination: Pagination parameters

        Returns:
            PaginatedResponse: Paginated response
        """
        pages = ceil(total / pagination.size) if total > 0 else 0
        has_next = pagination.page < pages
        has_prev = pagination.page > 1

        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )


def get_query_params(
    pagination: PaginationParams = Depends(get_pagination_params),
    order_by: Optional[OrderByParams] = Depends(get_order_by_params),
    filters: FilterParams = Depends(get_filter_params)
) -> Dict[str, Any]:
    """
    Dependency to get all query parameters

    Args:
        pagination: Pagination parameters
        order_by: Order by parameters
        filters: Filter parameters

    Returns:
        Dict[str, Any]: Query parameters
    """
    return {
        "pagination": pagination,
        "order_by": order_by,
        "filters": filters
    }


def validate_content_type(
    content_type: str = "application/json"
):
    """
    Dependency factory to validate content type

    Args:
        content_type: Expected content type

    Returns:
        Dependency function
    """
    async def content_type_dependency(
        content_type_header: str = None
    ):
        if content_type_header != content_type:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "error": "Unsupported content type",
                    "error_code": "UNSUPPORTED_CONTENT_TYPE",
                    "details": {
                        "expected": content_type,
                        "received": content_type_header
                    }
                }
            )
        return content_type_header

    return content_type_dependency


async def get_request_id(
    request_id: Optional[str] = None
) -> str:
    """
    Dependency to get or generate request ID

    Args:
        request_id: Optional request ID from headers

    Returns:
        str: Request ID
    """
    import uuid

    if request_id:
        return request_id

    return str(uuid.uuid4())