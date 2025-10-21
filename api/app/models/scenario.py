"""
Scenario Model

This module contains the Scenario SQLAlchemy ORM model for emergency scenarios.
"""

from sqlalchemy import Column, String, Text, Integer, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Scenario(BaseModel):
    """
    Scenario model for emergency scenarios
    """

    __tablename__ = "scenarios"

    # Basic scenario information
    title = Column(
        String(200),
        nullable=False,
        comment="Title of the emergency scenario"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the emergency scenario"
    )

    # Status and priority
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Scenario status (active, resolved, pending, closed)"
    )

    priority = Column(
        String(10),
        nullable=False,
        index=True,
        comment="Priority level (low, medium, high, critical)"
    )

    # Metadata and configuration
    metadata = Column(
        JSON,
        nullable=True,
        comment="Additional scenario metadata as JSON"
    )

    # Relationships
    created_by_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="ID of the user who created this scenario"
    )

    # Timestamps
    started_at = Column(
        String(50),
        nullable=True,
        comment="Timestamp when the scenario started"
    )

    ended_at = Column(
        String(50),
        nullable=True,
        comment="Timestamp when the scenario ended"
    )

    # Location information
    location = Column(
        String(200),
        nullable=True,
        comment="Location of the emergency scenario"
    )

    # Emergency type classification
    emergency_type = Column(
        JSON,
        nullable=True,
        comment="Emergency type classification as JSON"
    )

    # Additional fields
    incident_id = Column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
        comment="External incident ID from emergency services"
    )

    severity_level = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Severity level of the emergency"
    )

    estimated_duration = Column(
        String(50),
        nullable=True,
        comment="Estimated duration of the emergency"
    )

    actual_duration = Column(
        String(50),
        nullable=True,
        comment="Actual duration of the emergency"
    )

    # Geographic information
    latitude = Column(
        String(20),
        nullable=True,
        comment="Latitude coordinate"
    )

    longitude = Column(
        String(20),
        nullable=True,
        comment="Longitude coordinate"
    )

    # Impact assessment
    affected_population = Column(
        Integer,
        nullable=True,
        comment="Number of people affected"
    )

    estimated_cost = Column(
        Integer,
        nullable=True,
        comment="Estimated financial cost"
    )

    # External references
    external_references = Column(
        JSON,
        nullable=True,
        comment="External system references and links"
    )

    # Relationships
    creator = relationship(
        "User",
        back_populates="created_scenarios",
        foreign_keys=[created_by_id]
    )

    agents = relationship(
        "Agent",
        back_populates="scenario",
        cascade="all, delete-orphan"
    )

    resources = relationship(
        "Resource",
        back_populates="scenario",
        cascade="all, delete-orphan"
    )

    analysis = relationship(
        "Analysis",
        back_populates="scenario",
        cascade="all, delete-orphan"
    )

    decisions = relationship(
        "Decision",
        back_populates="scenario",
        cascade="all, delete-orphan"
    )

    messages = relationship(
        "Message",
        back_populates="scenario",
        cascade="all, delete-orphan"
    )

    user_scenarios = relationship(
        "UserScenario",
        back_populates="scenario",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_scenarios_status_priority', 'status', 'priority'),
        Index('idx_scenarios_created_by_status', 'created_by_id', 'status'),
        Index('idx_scenarios_created_at', 'created_at'),
        Index('idx_scenarios_incident_id', 'incident_id'),
        Index('idx_scenarios_severity', 'severity_level'),
        Index('idx_scenarios_location', 'location'),
    )

    def __repr__(self) -> str:
        return f"<Scenario(title='{self.title}', status='{self.status}', priority='{self.priority}')>"

    def get_duration_hours(self) -> float:
        """
        Calculate scenario duration in hours

        Returns:
            Duration in hours, or None if timestamps are missing
        """
        if self.started_at and self.ended_at:
            # This would need proper datetime parsing
            # For now, return None
            return None
        return None

    def is_active(self) -> bool:
        """
        Check if scenario is currently active

        Returns:
            True if scenario is active, False otherwise
        """
        return self.status == 'active'

    def can_be_modified(self, user_id: int) -> bool:
        """
        Check if scenario can be modified by a user

        Args:
            user_id: ID of the user

        Returns:
            True if scenario can be modified, False otherwise
        """
        # Only allow modification if scenario is not closed
        if self.status == 'closed':
            return False

        # Creator can always modify
        if self.created_by_id == user_id:
            return True

        # This would need to check user permissions and scenario assignments
        return False

    def add_agent(self, agent) -> None:
        """
        Add an agent to this scenario

        Args:
            agent: Agent object to add
        """
        if agent not in self.agents:
            self.agents.append(agent)

    def remove_agent(self, agent) -> None:
        """
        Remove an agent from this scenario

        Args:
            agent: Agent object to remove
        """
        if agent in self.agents:
            self.agents.remove(agent)

    def get_active_agents(self) -> list:
        """
        Get list of active agents in this scenario

        Returns:
            List of active agents
        """
        return [agent for agent in self.agents if agent.status == 'running']

    def get_latest_analysis(self, analysis_type: str = None) -> object:
        """
        Get the latest analysis for this scenario

        Args:
            analysis_type: Optional type of analysis to filter by

        Returns:
            Latest analysis object or None
        """
        if not self.analysis:
            return None

        filtered_analysis = self.analysis
        if analysis_type:
            filtered_analysis = [a for a in filtered_analysis if a.type == analysis_type]

        if filtered_analysis:
            # Sort by created_at descending and return the first
            return max(filtered_analysis, key=lambda a: a.created_at)

        return None