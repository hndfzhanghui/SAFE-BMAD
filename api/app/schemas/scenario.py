"""
Scenario Schemas

This module contains Pydantic schemas for scenario-related API operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, validator


class ScenarioBase(BaseModel):
    """Base scenario schema with common fields"""

    title: str
    description: Optional[str] = None
    status: str = "active"
    priority: str = "medium"
    location: Optional[str] = None
    emergency_type: Optional[Dict[str, Any]] = None

    @validator("title")
    def validate_title(cls, v):
        """Validate scenario title"""
        if len(v) < 3:
            raise ValueError("Title must be at least 3 characters long")
        if len(v) > 200:
            raise ValueError("Title must be no more than 200 characters long")
        return v

    @validator("status")
    def validate_status(cls, v):
        """Validate scenario status"""
        allowed_statuses = ["active", "resolved", "pending", "closed"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v

    @validator("priority")
    def validate_priority(cls, v):
        """Validate scenario priority"""
        allowed_priorities = ["low", "medium", "high", "critical"]
        if v not in allowed_priorities:
            raise ValueError(f"Priority must be one of: {allowed_priorities}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "title": "Chemical Spill Response",
                "description": "Emergency response to chemical spill at industrial facility",
                "status": "active",
                "priority": "high",
                "location": "123 Industrial Ave, City, State",
                "emergency_type": {
                    "category": "hazardous_materials",
                    "severity": "moderate",
                    "affected_area": "2km radius"
                }
            }
        }


class ScenarioCreate(ScenarioBase):
    """Schema for creating a new scenario"""

    metadata: Optional[Dict[str, Any]] = None
    incident_id: Optional[str] = None
    severity_level: Optional[str] = None
    estimated_duration: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    affected_population: Optional[int] = None
    estimated_cost: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "Chemical Spill Response",
                "description": "Emergency response to chemical spill at industrial facility",
                "status": "active",
                "priority": "high",
                "location": "123 Industrial Ave, City, State",
                "emergency_type": {
                    "category": "hazardous_materials",
                    "severity": "moderate"
                },
                "incident_id": "INC-2025-001",
                "severity_level": "high",
                "estimated_duration": "4-6 hours",
                "latitude": "40.7128",
                "longitude": "-74.0060",
                "affected_population": 150
            }
        }


class ScenarioUpdate(BaseModel):
    """Schema for updating an existing scenario"""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    emergency_type: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    severity_level: Optional[str] = None
    estimated_duration: Optional[str] = None
    actual_duration: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    affected_population: Optional[int] = None
    estimated_cost: Optional[int] = None
    external_references: Optional[Dict[str, Any]] = None

    @validator("status")
    def validate_status(cls, v):
        """Validate scenario status if provided"""
        if v is not None:
            allowed_statuses = ["active", "resolved", "pending", "closed"]
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v

    @validator("priority")
    def validate_priority(cls, v):
        """Validate scenario priority if provided"""
        if v is not None:
            allowed_priorities = ["low", "medium", "high", "critical"]
            if v not in allowed_priorities:
                raise ValueError(f"Priority must be one of: {allowed_priorities}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "status": "resolved",
                "priority": "medium",
                "ended_at": "2025-10-21T18:30:00.000Z",
                "actual_duration": "4h 15m",
                "affected_population": 120,
                "estimated_cost": 50000
            }
        }


class ScenarioInDB(ScenarioBase):
    """Schema for scenario data as stored in database"""

    id: int
    created_by_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    incident_id: Optional[str] = None
    severity_level: Optional[str] = None
    estimated_duration: Optional[str] = None
    actual_duration: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    affected_population: Optional[int] = None
    estimated_cost: Optional[int] = None
    external_references: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class ScenarioResponse(ScenarioBase):
    """Schema for scenario response data"""

    id: int
    created_by_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    incident_id: Optional[str] = None
    severity_level: Optional[str] = None
    estimated_duration: Optional[str] = None
    actual_duration: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    affected_population: Optional[int] = None
    estimated_cost: Optional[int] = None
    external_references: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "title": "Chemical Spill Response",
                "description": "Emergency response to chemical spill at industrial facility",
                "status": "active",
                "priority": "high",
                "location": "123 Industrial Ave, City, State",
                "emergency_type": {
                    "category": "hazardous_materials",
                    "severity": "moderate"
                },
                "created_by_id": 1,
                "created_at": "2025-10-21T14:30:00.000Z",
                "updated_at": "2025-10-21T14:30:00.000Z",
                "started_at": "2025-10-21T14:15:00.000Z",
                "incident_id": "INC-2025-001",
                "severity_level": "high",
                "estimated_duration": "4-6 hours",
                "latitude": "40.7128",
                "longitude": "-74.0060",
                "affected_population": 150
            }
        }


class ScenarioListResponse(BaseModel):
    """Schema for paginated scenario list response"""

    items: List[ScenarioResponse]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "title": "Chemical Spill Response",
                        "status": "active",
                        "priority": "high",
                        "created_at": "2025-10-21T14:30:00.000Z",
                        "updated_at": "2025-10-21T14:30:00.000Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1,
                "has_next": False,
                "has_prev": False
            }
        }


class ScenarioSummary(BaseModel):
    """Schema for scenario summary information"""

    id: int
    title: str
    status: str
    priority: str
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    agent_count: int = 0
    analysis_count: int = 0
    decision_count: int = 0
    resource_count: int = 0

    class Config:
        orm_mode = True