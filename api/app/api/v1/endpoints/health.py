"""
Health Check Endpoints

This module contains health check endpoints for the SAFE-BMAD API.
"""

import platform
import sys
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.database import check_database_connection, get_database_stats
from shared.utils.redis_client import check_redis_health
from shared.utils.redis_client import get_redis_connection
from app.schemas.health import HealthCheckResponse, ReadinessCheckResponse, VersionResponse, MetricsResponse

router = APIRouter()
settings = get_settings()

# Track application start time
start_time = time.time()


@router.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """
    Basic health check endpoint

    Returns the health status of the API service. This endpoint provides a quick
    way to verify that the API service is running and responsive.

    Returns:
        HealthCheckResponse: Basic health information
    """
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + "Z",
        service="safe-bmad-api",
        version="1.0.0",
        environment=settings.environment
    )


@router.get("/ready", response_model=ReadinessCheckResponse, tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint

    Checks if the service is ready to accept requests by verifying dependencies
    like database and Redis connections. This endpoint is useful for Kubernetes
    readiness probes and load balancers.

    Returns:
        ReadinessCheckResponse: Detailed readiness status with dependency checks

    Raises:
        HTTPException: If service is not ready (503 Service Unavailable)
    """
    try:
        # Check database connection
        db_status = await check_database_connection()

        # Check Redis connection
        redis_status = await check_redis_health()

        # Determine overall readiness
        overall_ready = (
            db_status["status"] == "healthy" and
            redis_status["status"] == "healthy"
        )

        response = ReadinessCheckResponse(
            status="ready" if overall_ready else "not_ready",
            timestamp=datetime.utcnow().isoformat() + "Z",
            checks={
                "database": db_status,
                "redis": redis_status
            }
        )

        if not overall_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response.dict()
            )

        return response

    except Exception as e:
        # Return a proper error response
        error_response = ReadinessCheckResponse(
            status="not_ready",
            timestamp=datetime.utcnow().isoformat() + "Z",
            checks={
                "database": {"status": "unhealthy", "error": str(e)},
                "redis": {"status": "unknown", "error": "Database check failed"}
            }
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_response.dict()
        )


@router.get("/version", response_model=VersionResponse, tags=["Health"])
async def version_info():
    """
    Version information endpoint

    Returns detailed version information about the API service, including
    runtime environment details. This endpoint is useful for monitoring
    and debugging purposes.

    Returns:
        VersionResponse: Detailed version and environment information
    """
    return VersionResponse(
        version="1.0.0",
        api_version="v1",
        build_time=None,  # This could be set during build process
        git_commit=None,  # This could be set during build process
        python_version=sys.version.split()[0],
        fastapi_version="0.104.1"  # This should be dynamically obtained
    )


@router.get("/metrics", response_model=MetricsResponse, tags=["Health"])
async def metrics():
    """
    Basic metrics endpoint

    Returns system and application metrics for monitoring purposes.
    This endpoint provides insights into application performance and usage.

    Returns:
        MetricsResponse: Application and system metrics
    """
    try:
        # Calculate uptime
        uptime_seconds = int(time.time() - start_time)
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        uptime_secs = uptime_seconds % 60
        uptime_str = f"{uptime_hours}h {uptime_minutes}m {uptime_secs}s"

        # Get database statistics
        db_stats = await get_database_stats()

        # Get Redis connection info
        redis_stats = {}
        try:
            redis_client = get_redis_connection()
            redis_stats = {
                "connected": True,
                "pool_size": getattr(redis_client.connection_pool, 'max_connections', 'unknown')
            }
        except Exception:
            redis_stats = {"connected": False}

        # Memory usage (basic implementation)
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage = {
            "rss": f"{memory_info.rss / 1024 / 1024:.1f}MB",
            "vms": f"{memory_info.vms / 1024 / 1024:.1f}MB"
        }

        # CPU usage
        cpu_usage = process.cpu_percent()

        return MetricsResponse(
            timestamp=datetime.utcnow().isoformat() + "Z",
            uptime=uptime_str,
            version="1.0.0",
            environment=settings.environment,
            requests_total=0,  # This would be implemented with actual request counting
            errors_total=0,    # This would be implemented with actual error counting
            active_connections=db_stats.get("pool_checked_out", 0),
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            database_stats=db_stats,
            redis_stats=redis_stats
        )

    except Exception as e:
        # Fallback response if metrics collection fails
        return MetricsResponse(
            timestamp=datetime.utcnow().isoformat() + "Z",
            uptime="unknown",
            version="1.0.0",
            environment=settings.environment,
            requests_total=0,
            errors_total=1,  # Count this metrics error
            active_connections=0,
            memory_usage={"error": str(e)},
            cpu_usage=None
        )


@router.get("/ping", tags=["Health"])
async def ping():
    """
    Simple ping endpoint

    Returns a simple pong response for basic connectivity testing.
    This endpoint has minimal overhead and is useful for basic health checks.

    Returns:
        dict: Simple pong response
    """
    return {
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "safe-bmad-api"
    }


@router.get("/info", tags=["Health"])
async def service_info():
    """
    Service information endpoint

    Returns detailed information about the service, including configuration
    and capabilities. This endpoint is useful for service discovery and
    documentation purposes.

    Returns:
        dict: Detailed service information
    """
    return {
        "name": "S3DA2 - SAFE BMAD System API",
        "description": "Multi-Agent Emergency Response System with S-A-F-E-R Framework",
        "version": "1.0.0",
        "api_version": "v1",
        "environment": settings.environment,
        "debug": settings.debug,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "capabilities": {
            "multi_agent_coordination": True,
            "emergency_response": True,
            "real_time_analysis": True,
            "decision_support": True,
            "resource_management": True
        },
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "version": "/version",
            "metrics": "/metrics",
            "ping": "/ping",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "contact": {
            "name": "SAFE-BMAD Team",
            "email": "team@safe-bmad.com"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    }