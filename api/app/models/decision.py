"""
Decision Model

This module contains the Decision SQLAlchemy ORM model for decision records.
"""

from sqlalchemy import Column, String, Text, JSON, Index, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Decision(BaseModel):
    """
    Decision model for recording decisions made during emergency scenarios
    """

    __tablename__ = "decisions"

    # Basic decision information
    title = Column(
        String(200),
        nullable=False,
        comment="Title of the decision"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the decision"
    )

    # Decision classification
    decision_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of decision (strategic, tactical, operational)"
    )

    # Decision options and outcomes
    options = Column(
        JSON,
        nullable=True,
        comment="Decision options considered as JSON"
    )

    recommendation = Column(
        JSON,
        nullable=True,
        comment="Recommended decision as JSON"
    )

    # Decision status
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Status of the decision (pending, approved, rejected, implemented)"
    )

    # Relationships
    analysis_id = Column(
        Integer,
        ForeignKey("analysis.id"),
        nullable=True,
        index=True,
        comment="ID of the analysis that led to this decision"
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="ID of the user who made this decision"
    )

    scenario_id = Column(
        Integer,
        ForeignKey("scenarios.id"),
        nullable=True,
        index=True,
        comment="ID of the scenario this decision belongs to"
    )

    # Decision rationale
    rationale = Column(
        JSON,
        nullable=True,
        comment="Decision rationale and justification as JSON"
    )

    # Confidence and urgency
    confidence_level = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Confidence level in the decision (low, medium, high)"
    )

    urgency_level = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Urgency level of the decision (low, medium, high, critical)"
    )

    # Implementation tracking
    implemented_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the decision was implemented"
    )

    implementation_status = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Implementation status (not_started, in_progress, completed, failed)"
    )

    # Outcomes and feedback
    outcomes = Column(
        JSON,
        nullable=True,
        comment="Decision outcomes as JSON"
    )

    effectiveness_score = Column(
        String(10),
        nullable=True,
        comment="Effectiveness score (1-10)"
    )

    lessons_learned = Column(
        Text,
        nullable=True,
        comment="Lessons learned from this decision"
    )

    # Approval workflow
    approved_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="ID of the user who approved this decision"
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the decision was approved"
    )

    # Review and audit
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the decision was reviewed"
    )

    review_comments = Column(
        Text,
        nullable=True,
        comment="Comments from the review"
    )

    # Tags and classification
    tags = Column(
        JSON,
        nullable=True,
        comment="Tags for classification and search"
    )

    # Relationships
    analysis = relationship(
        "Analysis",
        back_populates="decisions"
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="decisions"
    )

    scenario = relationship(
        "Scenario",
        back_populates="decisions"
    )

    approver = relationship(
        "User",
        foreign_keys=[approved_by]
    )

    # Indexes
    __table_args__ = (
        Index('idx_decisions_scenario_status', 'scenario_id', 'status'),
        Index('idx_decisions_user_created', 'user_id', 'created_at'),
        Index('idx_decisions_analysis', 'analysis_id'),
        Index('idx_decisions_type_status', 'decision_type', 'status'),
        Index('idx_decisions_urgency', 'urgency_level'),
        Index('idx_decisions_confidence', 'confidence_level'),
        Index('idx_decisions_implemented', 'implemented_at'),
        Index('idx_decisions_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Decision(title='{self.title}', type='{self.decision_type}', status='{self.status}')>"

    def get_type_description(self) -> str:
        """
        Get human-readable description of decision type

        Returns:
            Description of the decision type
        """
        type_descriptions = {
            'strategic': 'Strategic decisions affecting overall direction and long-term goals',
            'tactical': 'Tactical decisions for specific methods and approaches',
            'operational': 'Operational decisions for day-to-day activities and execution'
        }
        return type_descriptions.get(self.decision_type, 'Unknown decision type')

    def is_implemented(self) -> bool:
        """
        Check if decision has been implemented

        Returns:
            True if decision is implemented, False otherwise
        """
        return self.implemented_at is not None

    def is_approved(self) -> bool:
        """
        Check if decision has been approved

        Returns:
            True if decision is approved, False otherwise
        """
        return self.approved_at is not None

    def can_be_modified(self, user_id: int) -> bool:
        """
        Check if decision can be modified by a user

        Args:
            user_id: ID of the user

        Returns:
            True if decision can be modified, False otherwise
        """
        # Cannot modify if already implemented
        if self.is_implemented():
            return False

        # Creator can modify before approval
        if self.user_id == user_id and not self.is_approved():
            return True

        # This would need proper permission checking
        return False

    def get_effectiveness_rating(self) -> int:
        """
        Get effectiveness rating as integer

        Returns:
            Effectiveness rating (1-10) or None
        """
        if self.effectiveness_score:
            try:
                return int(self.effectiveness_score)
            except (ValueError, TypeError):
                pass
        return None

    def is_effective(self) -> bool:
        """
        Check if decision was effective (rating >= 7)

        Returns:
            True if decision was effective, False otherwise
        """
        rating = self.get_effectiveness_rating()
        return rating is not None and rating >= 7

    def add_outcome(self, outcome: dict) -> None:
        """
        Add an outcome to the decision

        Args:
            outcome: Outcome details
        """
        if self.outcomes is None:
            self.outcomes = []

        self.outcomes.append({
            'id': len(self.outcomes) + 1,
            'outcome': outcome,
            'recorded_at': self.created_at.isoformat() if self.created_at else None
        })

    def get_implementation_duration(self) -> str:
        """
        Calculate implementation duration

        Returns:
            Implementation duration as string or None
        """
        if self.implemented_at and self.created_at:
            # This would need proper datetime calculation
            # For now, return None
            return None
        return None