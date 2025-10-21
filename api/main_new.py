"""
FastAPI Main Application for SAFE-BMAD System
S3DA2 - SAFE BMAD System with S-A-F-E-R Agent Framework
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
import sys
import logging
from datetime import datetime
import asyncio
import uvicorn
import time

# Add shared modules to Python path
sys.path.append("../shared")
sys.path.append("../core")

# Configuration and dependencies
from shared.config.settings import get_settings
from shared.utils.logger import setup_logging
from shared.utils.database import get_database_connection
from shared.utils.redis_client import get_redis_connection

# App modules
from app.core.config import get_settings as app_get_settings
from app.core.exceptions import BaseCustomException, HTTPExceptionExtensions, get_http_status_code
from app.api.v1.api import api_router
from app.db.database import create_database_engines, close_database_connections
from shared.utils.redis_client import check_redis_health
from app.db.database import check_database_connection

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get application settings
settings = app_get_settings()

# Create FastAPI application
app = FastAPI(
    title="S3DA2 - SAFE BMAD System API",
    description="S3DA2 SAFE BMAD System with S-A-F-E-R Agent Framework - Multi-Agent Emergency Response System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "SAFE-BMAD Team",
        "email": "team@safe-bmad.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Trusted host middleware (for production)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with actual allowed hosts
    )

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header to all responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include API v1 router
app.include_router(api_router, prefix=settings.api_prefix)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "Welcome to S3DA2 - SAFE BMAD System API",
        "version": "1.0.0",
        "description": "Multi-Agent Emergency Response System with S-A-F-E-R Framework",
        "api_version": "v1",
        "api_prefix": settings.api_prefix,
        "documentation": {
            "swagger": f"{settings.api_prefix}/docs",
            "redoc": f"{settings.api_prefix}/redoc",
            "openapi": f"{settings.api_prefix}/openapi.json"
        },
        "health_checks": {
            "health": f"{settings.api_prefix}/health/health",
            "ready": f"{settings.api_prefix}/health/ready",
            "version": f"{settings.api_prefix}/health/version"
        },
        "endpoints": {
            "users": f"{settings.api_prefix}/users",
            "scenarios": f"{settings.api_prefix}/scenarios",
            "agents": f"{settings.api_prefix}/agents"
        }
    }

# Exception handlers
@app.exception_handler(BaseCustomException)
async def custom_exception_handler(request: Request, exc: BaseCustomException):
    """Handle custom application exceptions"""
    status_code = get_http_status_code(exc)

    logger.error(
        f"Custom exception: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": str(request.url),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method
        }
    )

    # Extract detail content if it's a dict
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {
            "error": exc.detail,
            "status_code": exc.status_code
        }

    content.update({
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url)
    })

    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": str(request.url),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_SERVER_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
            "details": {"debug_info": str(exc)} if settings.debug else None
        }
    )

# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting SAFE-BMAD API server...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API host: {settings.api_host}")
    logger.info(f"API port: {settings.api_port}")
    logger.info(f"API prefix: {settings.api_prefix}")

    try:
        # Initialize database connections
        logger.info("Initializing database connections...")
        create_database_engines()

        # Test database connection
        db_health = await check_database_connection()
        if db_health["status"] == "healthy":
            logger.info("Database connection successful")
        else:
            logger.warning(f"Database connection issue: {db_health.get('message', 'Unknown error')}")

        # Initialize Redis connection
        logger.info("Initializing Redis connection...")
        redis_client = get_redis_connection()

        # Test Redis connection
        redis_health = await check_redis_health()
        if redis_health["status"] == "healthy":
            logger.info("Redis connection successful")
        else:
            logger.warning(f"Redis connection issue: {redis_health.get('message', 'Unknown error')}")

        # Log startup success
        logger.info("SAFE-BMAD API server started successfully!")
        logger.info(f"API documentation available at: http://{settings.api_host}:{settings.api_port}{settings.api_prefix}/docs")

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down SAFE-BMAD API server...")

    try:
        # Close database connections
        logger.info("Closing database connections...")
        await close_database_connections()

        # Close Redis connections
        logger.info("Closing Redis connections...")
        from shared.utils.redis_client import close_redis_connections
        await close_redis_connections()

        logger.info("SAFE-BMAD API server shut down successfully!")

    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Development server startup
if __name__ == "__main__":
    logger.info("Starting development server...")

    uvicorn.run(
        "main_new:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True,
        use_colors=True
    )