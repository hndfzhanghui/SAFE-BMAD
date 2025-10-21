"""
Health Check Schemas

This module contains Pydantic schemas for health check endpoints.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Health check response schema"""

    status: str
    timestamp: str
    service: str
    version: str
    environment: str

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-21T14:30:00.000Z",
                "service": "safe-bmad-api",
                "version": "1.0.0",
                "environment": "development"
            }
        }


class ReadinessCheckResponse(BaseModel):
    """Readiness check response schema"""

    status: str
    timestamp: str
    checks: Dict[str, Dict[str, Any]]

    class Config:
        schema_extra = {
            "example": {
                "status": "ready",
                "timestamp": "2025-10-21T14:30:00.000Z",
                "checks": {
                    "database": {
                        "status": "healthy",
                        "response_time_ms": 15.2,
                        "details": "Database connection successful"
                    },
                    "redis": {
                        "status": "healthy",
                        "response_time_ms": 8.5,
                        "details": "Redis connection successful"
                    }
                }
            }
        }


class VersionResponse(BaseModel):
    """Version information response schema"""

    version: str
    api_version: str
    build_time: Optional[str] = None
    git_commit: Optional[str] = None
    python_version: str
    fastapi_version: str

    class Config:
        schema_extra = {
            "example": {
                "version": "1.0.0",
                "api_version": "v1",
                "build_time": "2025-10-21T14:00:00.000Z",
                "git_commit": "abc123def456",
                "python_version": "3.11.5",
                "fastapi_version": "0.104.1"
            }
        }


class MetricsResponse(BaseModel):
    """Metrics response schema"""

    timestamp: str
    uptime: str
    version: str
    environment: str
    requests_total: int
    errors_total: int
    active_connections: int
    memory_usage: Dict[str, Any]
    cpu_usage: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-10-21T14:30:00.000Z",
                "uptime": "2h 30m 15s",
                "version": "1.0.0",
                "environment": "development",
                "requests_total": 1250,
                "errors_total": 3,
                "active_connections": 5,
                "memory_usage": {
                    "rss": "45.2MB",
                    "vms": "120.5MB"
                },
                "cpu_usage": 12.5
            }
        }