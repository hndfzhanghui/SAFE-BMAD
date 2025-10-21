"""
Scenario Endpoints

This module contains scenario management endpoints for the SAFE-BMAD API.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.dependencies.database import get_db_session
from app.dependencies.security import get_current_user_id
from app.dependencies.common import get_pagination_params, PaginationParams, PaginatedResponse
from app.schemas.scenario import (
    ScenarioCreate, ScenarioUpdate, ScenarioResponse, ScenarioListResponse, ScenarioSummary
)
from app.models.scenario import Scenario
from app.models.user import User
from app.core.exceptions import NotFoundError, ConflictError, ValidationError

router = APIRouter()


# CRUD operations for scenarios
class ScenarioCRUD:
    """CRUD operations for Scenario model"""

    @staticmethod
    async def create(
        session: AsyncSession,
        scenario_create: ScenarioCreate,
        created_by_id: int
    ) -> Scenario:
        """Create a new scenario"""
        # Check if incident ID already exists
        if scenario_create.incident_id:
            result = await session.execute(
                select(Scenario).where(Scenario.incident_id == scenario_create.incident_id)
            )
            if result.scalar_one_or_none():
                raise ConflictError(
                    message="Incident ID already exists",
                    conflict_type="incident_id",
                    details={"incident_id": scenario_create.incident_id}
                )

        # Create scenario
        scenario = Scenario(
            title=scenario_create.title,
            description=scenario_create.description,
            status=scenario_create.status,
            priority=scenario_create.priority,
            metadata=scenario_create.metadata,
            created_by_id=created_by_id,
            location=scenario_create.location,
            emergency_type=scenario_create.emergency_type,
            incident_id=scenario_create.incident_id,
            severity_level=scenario_create.severity_level,
            estimated_duration=scenario_create.estimated_duration,
            latitude=scenario_create.latitude,
            longitude=scenario_create.longitude,
            affected_population=scenario_create.affected_population,
            estimated_cost=scenario_create.estimated_cost
        )

        # Set started_at if status is active
        if scenario.status == "active":
            scenario.started_at = datetime.utcnow().isoformat()

        session.add(scenario)
        await session.flush()
        await session.refresh(scenario)
        return scenario

    @staticmethod
    async def get_by_id(session: AsyncSession, scenario_id: int) -> Optional[Scenario]:
        """Get scenario by ID"""
        result = await session.execute(
            select(Scenario).where(Scenario.id == scenario_id, Scenario.is_deleted == False)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        session: AsyncSession,
        pagination: PaginationParams,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        created_by_id: Optional[int] = None
    ) -> tuple[List[Scenario], int]:
        """Get multiple scenarios with filtering and pagination"""
        query = select(Scenario).where(Scenario.is_deleted == False)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    func.lower(Scenario.title).contains(search.lower()),
                    func.lower(Scenario.description).contains(search.lower()),
                    func.lower(Scenario.location).contains(search.lower())
                )
            )

        if status:
            query = query.where(Scenario.status == status)

        if priority:
            query = query.where(Scenario.priority == priority)

        if created_by_id:
            query = query.where(Scenario.created_by_id == created_by_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.order_by(Scenario.created_at.desc())
        query = query.offset(pagination.offset).limit(pagination.limit)

        result = await session.execute(query)
        scenarios = result.scalars().all()

        return list(scenarios), total

    @staticmethod
    async def update(
        session: AsyncSession,
        scenario_id: int,
        scenario_update: ScenarioUpdate
    ) -> Optional[Scenario]:
        """Update scenario"""
        scenario = await ScenarioCRUD.get_by_id(session, scenario_id)
        if not scenario:
            raise NotFoundError(
                message="Scenario not found",
                resource_type="scenario",
                resource_id=scenario_id
            )

        # Check for incident ID conflicts if updating incident_id
        if scenario_update.incident_id and scenario_update.incident_id != scenario.incident_id:
            result = await session.execute(
                select(Scenario).where(
                    Scenario.incident_id == scenario_update.incident_id,
                    Scenario.id != scenario_id
                )
            )
            if result.scalar_one_or_none():
                raise ConflictError(
                    message="Incident ID already exists",
                    conflict_type="incident_id",
                    details={"incident_id": scenario_update.incident_id}
                )

        # Update fields
        update_data = scenario_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scenario, field, value)

        # Auto-set started_at if status is changing to active and not already set
        if scenario_update.status == "active" and not scenario.started_at:
            scenario.started_at = datetime.utcnow().isoformat()

        # Auto-set ended_at if status is changing to resolved/closed and not already set
        if scenario_update.status in ["resolved", "closed"] and not scenario.ended_at:
            scenario.ended_at = datetime.utcnow().isoformat()

        scenario.updated_at = datetime.utcnow()
        await session.flush()
        await session.refresh(scenario)
        return scenario

    @staticmethod
    async def delete(session: AsyncSession, scenario_id: int) -> bool:
        """Delete scenario (soft delete)"""
        scenario = await ScenarioCRUD.get_by_id(session, scenario_id)
        if not scenario:
            raise NotFoundError(
                message="Scenario not found",
                resource_type="scenario",
                resource_id=scenario_id
            )

        scenario.is_deleted = True
        scenario.deleted_at = datetime.utcnow()
        await session.flush()
        return True

    @staticmethod
    async def get_summary(session: AsyncSession, scenario_id: int) -> Optional[ScenarioSummary]:
        """Get scenario summary with counts"""
        scenario = await ScenarioCRUD.get_by_id(session, scenario_id)
        if not scenario:
            return None

        # Count related objects (simplified for now)
        agent_count = 0
        analysis_count = 0
        decision_count = 0
        resource_count = 0

        # In a real implementation, you would query the related tables:
        # agent_count = await session.scalar(select(func.count()).select_from(Agent).where(Agent.scenario_id == scenario_id))
        # etc.

        return ScenarioSummary(
            id=scenario.id,
            title=scenario.title,
            status=scenario.status,
            priority=scenario.priority,
            location=scenario.location,
            created_at=scenario.created_at,
            updated_at=scenario.updated_at,
            agent_count=agent_count,
            analysis_count=analysis_count,
            decision_count=decision_count,
            resource_count=resource_count
        )


# Endpoints
@router.post("/", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    scenario_create: ScenarioCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Create a new scenario

    This endpoint creates a new emergency scenario in the system.
    """
    try:
        scenario = await ScenarioCRUD.create(session, scenario_create, current_user_id)
        await session.commit()
        return ScenarioResponse.from_orm(scenario)
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
                "error": "Failed to create scenario",
                "error_code": "SCENARIO_CREATION_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.get("/", response_model=ScenarioListResponse)
async def get_scenarios(
    pagination: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search scenarios by title, description, or location"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    created_by_id: Optional[int] = Query(None, description="Filter by creator ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Get list of scenarios with pagination and filtering

    This endpoint returns a paginated list of scenarios. Supports search and filtering.
    """
    try:
        scenarios, total = await ScenarioCRUD.get_multi(
            session=session,
            pagination=pagination,
            search=search,
            status=status,
            priority=priority,
            created_by_id=created_by_id
        )

        scenario_responses = [ScenarioResponse.from_orm(scenario) for scenario in scenarios]
        paginated_response = PaginatedResponse.create(scenario_responses, total, pagination)

        return ScenarioListResponse(**paginated_response.dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve scenarios",
                "error_code": "SCENARIO_RETRIEVAL_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Get scenario by ID

    This endpoint returns scenario details.
    """
    try:
        scenario = await ScenarioCRUD.get_by_id(session, scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Scenario not found",
                    "error_code": "SCENARIO_NOT_FOUND",
                    "details": {"scenario_id": scenario_id}
                }
            )

        # TODO: Check if user has permission to view this scenario
        # For now, allow all authenticated users

        return ScenarioResponse.from_orm(scenario)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve scenario",
                "error_code": "SCENARIO_RETRIEVAL_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.get("/{scenario_id}/summary", response_model=ScenarioSummary)
async def get_scenario_summary(
    scenario_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Get scenario summary with related counts

    This endpoint returns a summary of the scenario including counts of related agents, analysis, decisions, and resources.
    """
    try:
        summary = await ScenarioCRUD.get_summary(session, scenario_id)
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Scenario not found",
                    "error_code": "SCENARIO_NOT_FOUND",
                    "details": {"scenario_id": scenario_id}
                }
            )

        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve scenario summary",
                "error_code": "SCENARIO_SUMMARY_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: int,
    scenario_update: ScenarioUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Update scenario information

    This endpoint updates scenario information.
    """
    try:
        # TODO: Check if user has permission to update this scenario
        # For now, allow all authenticated users

        scenario = await ScenarioCRUD.update(session, scenario_id, scenario_update)
        await session.commit()
        return ScenarioResponse.from_orm(scenario)
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
    except ConflictError as e:
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
                "error": "Failed to update scenario",
                "error_code": "SCENARIO_UPDATE_FAILED",
                "details": {"error": str(e)}
            }
        )


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Delete scenario (soft delete)

    This endpoint deletes a scenario (soft delete).
    """
    try:
        # TODO: Check if user has permission to delete this scenario
        # For now, allow all authenticated users

        await ScenarioCRUD.delete(session, scenario_id)
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
                "error": "Failed to delete scenario",
                "error_code": "SCENARIO_DELETION_FAILED",
                "details": {"error": str(e)}
            }
        )