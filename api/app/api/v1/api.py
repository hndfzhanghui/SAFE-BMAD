"""
API v1 Router

This module aggregates all API v1 routers for the SAFE-BMAD system.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, users, scenarios, agents, auth

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Health check endpoints
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

# User management endpoints
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# Scenario management endpoints
api_router.include_router(
    scenarios.router,
    prefix="/scenarios",
    tags=["Scenarios"]
)

# Agent management endpoints
api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["Agents"]
)