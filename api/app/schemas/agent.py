"""
Agent Schemas

This module contains Pydantic schemas for agent-related API operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, validator


class AgentBase(BaseModel):
    """Base agent schema with common fields"""

    name: str
    type: str
    status: str = "idle"
    configuration: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None

    @validator("name")
    def validate_name(cls, v):
        """Validate agent name"""
        if len(v) < 3:
            raise ValueError("Name must be at least 3 characters long")
        if len(v) > 100:
            raise ValueError("Name must be no more than 100 characters long")
        return v

    @validator("type")
    def validate_type(cls, v):
        """Validate agent type"""
        allowed_types = ["S", "A", "F", "E", "R"]  # S-A-F-E-R framework
        if v not in allowed_types:
            raise ValueError(f"Agent type must be one of: {allowed_types}")
        return v

    @validator("status")
    def validate_status(cls, v):
        """Validate agent status"""
        allowed_statuses = ["idle", "running", "paused", "error", "completed"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "SAR-001",
                "type": "S",
                "status": "running",
                "configuration": {
                    "search_radius": "5km",
                    "response_time": "2min"
                },
                "capabilities": {
                    "search": True,
                    "reconnaissance": True,
                    "reporting": True
                }
            }
        }


class AgentCreate(AgentBase):
    """Schema for creating a new agent"""

    scenario_id: int
    model_name: Optional[str] = None
    description: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    communication_channel: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "SAR-001",
                "type": "S",
                "scenario_id": 1,
                "model_name": "gpt-4",
                "description": "Search and rescue agent specialized in locating missing persons",
                "configuration": {
                    "search_radius": "5km",
                    "response_time": "2min"
                },
                "capabilities": {
                    "search": True,
                    "reconnaissance": True,
                    "reporting": True
                },
                "communication_channel": "radio-channel-1"
            }
        }


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent"""

    name: Optional[str] = None
    status: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = None
    description: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    current_task: Optional[Dict[str, Any]] = None
    task_queue: Optional[Dict[str, Any]] = None
    communication_channel: Optional[str] = None
    health_score: Optional[float] = None
    version: Optional[str] = None
    update_available: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        """Validate agent status if provided"""
        if v is not None:
            allowed_statuses = ["idle", "running", "paused", "error", "completed"]
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v

    @validator("health_score")
    def validate_health_score(cls, v):
        """Validate health score if provided"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Health score must be between 0 and 100")
        return v

    class Config:
        schema_extra = {
            "example": {
                "status": "paused",
                "health_score": 85.5,
                "current_task": {
                    "task_id": "TASK-001",
                    "description": "Searching sector A-3",
                    "progress": "75%"
                }
            }
        }


class AgentInDB(AgentBase):
    """Schema for agent data as stored in database"""

    id: int
    scenario_id: Optional[int] = None
    last_activity: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    current_task: Optional[Dict[str, Any]] = None
    task_queue: Optional[Dict[str, Any]] = None
    communication_channel: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    error_count: Optional[float] = None
    last_error: Optional[Dict[str, Any]] = None
    health_score: Optional[float] = None
    last_heartbeat: Optional[str] = None
    version: Optional[str] = None
    update_available: Optional[str] = None

    class Config:
        orm_mode = True


class AgentResponse(AgentBase):
    """Schema for agent response data"""

    id: int
    scenario_id: Optional[int] = None
    last_activity: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    current_task: Optional[Dict[str, Any]] = None
    task_queue: Optional[Dict[str, Any]] = None
    communication_channel: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    error_count: Optional[float] = None
    health_score: Optional[float] = None
    last_heartbeat: Optional[str] = None
    version: Optional[str] = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "SAR-001",
                "type": "S",
                "status": "running",
                "scenario_id": 1,
                "model_name": "gpt-4",
                "created_at": "2025-10-21T14:30:00.000Z",
                "updated_at": "2025-10-21T14:35:00.000Z",
                "health_score": 95.0,
                "last_heartbeat": "2025-10-21T14:35:30.000Z",
                "current_task": {
                    "task_id": "TASK-001",
                    "description": "Searching sector A-3",
                    "progress": "75%"
                }
            }
        }


class AgentListResponse(BaseModel):
    """Schema for paginated agent list response"""

    items: List[AgentResponse]
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
                        "name": "SAR-001",
                        "type": "S",
                        "status": "running",
                        "scenario_id": 1,
                        "created_at": "2025-10-21T14:30:00.000Z",
                        "updated_at": "2025-10-21T14:35:00.000Z"
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


class AgentStatus(BaseModel):
    """Schema for agent status update"""

    status: str
    activity_type: Optional[str] = None
    activity_details: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None

    @validator("status")
    def validate_status(cls, v):
        """Validate agent status"""
        allowed_statuses = ["idle", "running", "paused", "error", "completed"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "status": "running",
                "activity_type": "search_operation",
                "activity_details": {
                    "sector": "A-3",
                    "progress": "75%",
                    "findings": ["potential shelter", "water source"]
                }
            }
        }


class AgentTask(BaseModel):
    """Schema for agent task assignment"""

    task: Dict[str, Any]
    priority: Optional[str] = "medium"

    @validator("priority")
    def validate_priority(cls, v):
        """Validate task priority"""
        allowed_priorities = ["low", "medium", "high", "critical"]
        if v not in allowed_priorities:
            raise ValueError(f"Priority must be one of: {allowed_priorities}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "task": {
                    "type": "search",
                    "description": "Search for missing persons in sector A-3",
                    "parameters": {
                        "sector": "A-3",
                        "search_type": "grid",
                        "time_limit": "2h"
                    }
                },
                "priority": "high"
            }
        }


class AgentPerformance(BaseModel):
    """Schema for agent performance metrics"""

    health_score: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    tasks_completed: Optional[int] = None
    tasks_pending: Optional[int] = None
    last_activity: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "health_score": 92.5,
                "cpu_usage": 45.2,
                "memory_usage": 128.5,
                "tasks_completed": 5,
                "tasks_pending": 2,
                "last_activity": {
                    "type": "search_completed",
                    "timestamp": "2025-10-21T14:35:00.000Z",
                    "details": "Searched sector A-3, found 2 potential locations"
                }
            }
        }