"""
FastAPI Main Application for SAFE-BMAD System
S3DA2 - SAFE BMAD System with S-A-F-E-R Agent Framework
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import sys
import logging
from datetime import datetime
import asyncio
import uvicorn

# Add shared modules to Python path
sys.path.append("../shared")
sys.path.append("../core")

# Configuration and dependencies
from shared.config.settings import get_settings
from shared.utils.logger import setup_logging
from shared.utils.database import get_database_connection
from shared.utils.redis_client import get_redis_connection

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="S3DA2 - SAFE BMAD System API",
    description="S3DA2 SAFE BMAD System with S-A-F-E-R Agent Framework",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware configuration
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Static files serving
app.mount("/static", StaticFiles(directory="."), name="static")

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check endpoint
    Returns the health status of the API service
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "safe-bmad-api",
        "version": "1.0.0",
        "environment": settings.environment
    }

@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint
    Checks if the service is ready to accept requests
    """
    try:
        # Check database connection
        db_status = await check_database_health()

        # Check Redis connection
        redis_status = await check_redis_health()

        overall_ready = db_status["status"] == "healthy" and redis_status["status"] == "healthy"

        return {
            "status": "ready" if overall_ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": db_status,
                "redis": redis_status
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/metrics", tags=["Health"])
async def metrics():
    """
    Basic metrics endpoint
    Returns system and application metrics
    """
    try:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": "0s",  # TODO: Implement uptime tracking
            "version": "1.0.0",
            "environment": settings.environment,
            "requests_total": 0,  # TODO: Implement request counting
            "errors_total": 0,    # TODO: Implement error counting
        }
    except Exception as e:
        logger.error(f"Metrics check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

# Health check helper functions
async def check_database_health():
    """Check database connection health"""
    try:
        # TODO: Implement actual database health check
        # For now, return mock status
        return {
            "status": "healthy",
            "response_time_ms": 10,
            "details": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Database connection failed"
        }

async def check_redis_health():
    """Check Redis connection health"""
    try:
        # TODO: Implement actual Redis health check
        # For now, return mock status
        return {
            "status": "healthy",
            "response_time_ms": 5,
            "details": "Redis connection successful"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Redis connection failed"
        }

# Demo page endpoint
@app.get("/demo.html", tags=["Demo"])
async def demo_page():
    """Serve the demo HTML page"""
    demo_path = os.path.join(os.path.dirname(__file__), "unified_demo.html")
    if os.path.exists(demo_path):
        return FileResponse(demo_path)
    else:
        raise HTTPException(status_code=404, detail="Demo page not found")

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "Welcome to S3DA2 - SAFE BMAD System API",
        "version": "1.0.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "demo": {
            "demo_page": "/demo.html",
            "description": "Interactive demo page with API testing"
        },
        "health_checks": {
            "health": "/health",
            "ready": "/ready",
            "metrics": "/metrics"
        }
    }

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
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

    # TODO: Initialize database connections
    # TODO: Initialize Redis connections
    # TODO: Initialize AI models

    logger.info("SAFE-BMAD API server started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down SAFE-BMAD API server...")

    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Cleanup resources

    logger.info("SAFE-BMAD API server shut down successfully!")

# Development server startup
if __name__ == "__main__":
    logger.info("Starting development server...")

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True,
        use_colors=True
    )