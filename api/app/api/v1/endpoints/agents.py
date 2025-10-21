"""
Agent Endpoints

This module contains agent management endpoints for the SAFE-BMAD API.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.dependencies.database import get_db_session
from app.dependencies.security import get_current_user_id
from app.dependencies.common import get_pagination_params, PaginationParams, PaginatedResponse
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentListResponse,
    AgentStatus, AgentTask, AgentPerformance
)
from app.models.agent import Agent
from app.models.scenario import Scenario
from app.core.exceptions import NotFoundError, ConflictError, ValidationError

router = APIRouter()


# CRUD operations for agents
class AgentCRUD:
    """CRUD operations for Agent model"""

    @staticmethod
    async def create(session: AsyncSession, agent_create: AgentCreate) -> Agent:
        """Create a new agent"""
        # Check if scenario exists
        result = await session.execute(
            select(Scenario).where(Scenario.id == agent_create.scenario_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundError(
                message="Scenario not found",
                resource_type="scenario",
                resource_id=agent_create.scenario_id
            )

        # Create agent
        agent = Agent(
            name=agent_create.name,
            type=agent_create.type,
            status=agent_create.status,
            configuration=agent_create.configuration,
            capabilities=agent_create.capabilities,
            scenario_id=agent_create.scenario_id,
            model_name=agent_create.model_name,
            description=agent_create.description,
            state=agent_create.state,
            communication_channel=agent_create.communication_channel
        )

        session.add(agent)
        await session.flush()
        await session.refresh(agent)
        return agent

    @staticmethod
    async def get_by_id(session: AsyncSession, agent_id: int) -> Optional[Agent]:
        """Get agent by ID"""
        result = await session.execute(
            select(Agent).where(Agent.id == agent_id, Agent.is_deleted == False)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        session: AsyncSession,
        pagination: PaginationParams,
        search: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        scenario_id: Optional[int] = None
    ) -> tuple[List[Agent], int]:
        """Get multiple agents with filtering and pagination"""
        query = select(Agent).where(Agent.is_deleted == False)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    func.lower(Agent.name).contains(search.lower()),
                    func.lower(Agent.description).contains(search.lower())
                )
            )

        if type:
            query = query.where(Agent.type == type)

        if status:
            query = query.where(Agent.status == status)

        if scenario_id:
            query = query.where(Agent.scenario_id == scenario_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.order_by(Agent.created_at.desc())
        query = query.offset(pagination.offset).limit(pagination.limit)

        result = await session.execute(query)
        agents = result.scalars().all()

        return list(agents), total

    @staticmethod
    async def get_by_type(session: AsyncSession, agent_type: str, scenario_id: Optional[int] = None) -> List[Agent]:
        """Get agents by type"""
        query = select(Agent).where(
            and_(
                Agent.type == agent_type,
                Agent.is_deleted == False
            )
        )

        if scenario_id:
            query = query.where(Agent.scenario_id == scenario_id)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession,
        agent_id: int,
        agent_update: AgentUpdate
    ) -> Optional[Agent]:
        """Update agent"""
        agent = await AgentCRUD.get_by_id(session, agent_id)
        if not agent:
            raise NotFoundError(
                message="Agent not found",
                resource_type="agent",
                resource_id=agent_id
            )

        # Update fields
        update_data = agent_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        agent.updated_at = datetime.utcnow()
        await session.flush()
        await session.refresh(agent)
        return agent

    @staticmethod
    async def update_status(
        session: AsyncSession,
        agent_id: int,
        status_update: AgentStatus
    ) -> Optional[Agent]:
        """Update agent status"""
        agent = await AgentCRUD.get_by_id(session, agent_id)
        if not agent:
            raise NotFoundError(
                message="Agent not found",
                resource_type="agent",
                resource_id=agent_id
            )

        agent.status = status_update.status

        # Update error information if status is error
        if status_update.status == "error" and status_update.error_details:
            agent.error_count = (agent.error_count or 0) + 1
            agent.last_error = status_update.error_details
            agent.health_score = max(0, (agent.health_score or 100) - 10)
        elif status_update.status == "running":
            agent.health_score = min(100, (agent.health_score or 100) + 5)

        # Record activity
        if status_update.activity_type:
            agent.record_activity(
                status_update.activity_type,
                status_update.activity_details or {}
            )

        agent.updated_at = datetime.utcnow()
        await session.flush()
        await session.refresh(agent)
        return agent

    @staticmethod
    async def add_task(
        session: AsyncSession,
        agent_id: int,
        agent_task: AgentTask
    ) -> Optional[Agent]:
        """Add task to agent"""
        agent = await AgentCRUD.get_by_id(session, agent_id)
        if not agent:
            raise NotFoundError(
                message="Agent not found",
                resource_type="agent",
                resource_id=agent_id
            )

        agent.add_task(agent_task.task)
        agent.updated_at = datetime.utcnow()
        await session.flush()
        await session.refresh(agent)
        return agent

    @staticmethod
    async def delete(session: AsyncSession, agent_id: int) -> bool:
        """Delete agent (soft delete)"""
        agent = await AgentCRUD.get_by_id(session, agent_id)
        if not agent:
            raise NotFoundError(
                message="Agent not found",
                resource_type="agent",
                resource_id=agent_id
            )

        agent.is_deleted = True
        agent.deleted_at = datetime.utcnow()
        await session.flush()
        return True


# Endpoints
@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_create: AgentCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Create a new agent

    This endpoint creates a new agent in the system.
    """
    try:
        agent = await AgentCRUD.create(session, agent_create)
        await session.commit()
        return AgentResponse.from_orm(agent)
    except NotFoundError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except ValidationError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to create agent",
                "error_code": "AGENT_CREATION_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.get("/", response_model=AgentListResponse)
async def get_agents(
    pagination: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search agents by name or description"),
    type: Optional[str] = Query(None, description="Filter by agent type (S, A, F, E, E)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    scenario_id: Optional[int] = Query(None, description="Filter by scenario ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Get list of agents with pagination and filtering

    This endpoint returns a paginated list of agents. Supports search and filtering.
    """
    try:
        agents, total = await AgentCRUD.get_multi(
            session=session,
            pagination=pagination,
            search=search,
            type=type,
            status=status,
            scenario_id=scenario_id
        )

        agent_responses = [AgentResponse.from_orm(agent) for agent in agents]
        paginated_response = PaginatedResponse.create(agent_responses, total, pagination)

        return AgentListResponse(**paginated_response.dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve agents",
                "error_code": "AGENT_RETRIEVAL_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Get agent by ID

    This endpoint returns agent details.
    """
    try:
        agent = await AgentCRUD.get_by_id(session, agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Agent not found",
                    "error_code": "AGENT_NOT_FOUND",
                    "details": {"agent_id": agent_id}
                }
            )

        return AgentResponse.from_orm(agent)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve agent",
                "error_code": "AGENT_RETRIEVAL_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Update agent information

    This endpoint updates agent information.
    """
    try:
        agent = await AgentCRUD.update(session, agent_id, agent_update)
        await session.commit()
        return AgentResponse.from_orm(agent)
    except NotFoundError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except ValidationError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to update agent",
                "error_code": "AGENT_UPDATE_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.post("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: int,
    status_update: AgentStatus,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Update agent status

    This endpoint updates agent status and records activity.
    """
    try:
        agent = await AgentCRUD.update_status(session, agent_id, status_update)
        await session.commit()
        return AgentResponse.from_orm(agent)
    except NotFoundError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to update agent status",
                "error_code": "AGENT_STATUS_UPDATE_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.post("/{agent_id}/tasks", response_model=AgentResponse)
async def add_agent_task(
    agent_id: int,
    agent_task: AgentTask,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Add task to agent

    This endpoint adds a new task to the agent's task queue.
    """
    try:
        agent = await AgentCRUD.add_task(session, agent_id, agent_task)
        await session.commit()
        return AgentResponse.from_orm(agent)
    except NotFoundError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to add task to agent",
                "error_code": "AGENT_TASK_ADD_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.get("/{agent_id}/performance", response_model=AgentPerformance)
async def get_agent_performance(
    agent_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Get agent performance metrics

    This endpoint returns performance metrics for the agent.
    """
    try:
        agent = await AgentCRUD.get_by_id(session, agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Agent not found",
                    "error_code": "AGENT_NOT_FOUND",
                    "details": {"agent_id": agent_id}
                }
            )

        performance_summary = agent.get_performance_summary()
        return AgentPerformance(**performance_summary)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve agent performance",
                "error_code": "AGENT_PERFORMANCE_RETRIEVAL_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Delete agent (soft delete)

    This endpoint deletes an agent (soft delete).
    """
    try:
        await AgentCRUD.delete(session, agent_id)
        await session.commit()
    except NotFoundError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to delete agent",
                "error_code": "AGENT_DELETION_FAILED",
                "details": {"error": str(e)}
            }
        )