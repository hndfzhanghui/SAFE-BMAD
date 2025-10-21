"""
Analysis Model

This module contains the Analysis SQLAlchemy ORM model for analysis results.
"""

from sqlalchemy import Column, String, Text, JSON, Index, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Analysis(BaseModel):
    """
    Analysis model for storing analysis results from agents
    """

    __tablename__ = "analysis"

    # Analysis type
    type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of analysis (situational, risk, resource, impact)"
    )

    # Analysis results
    results = Column(
        JSON,
        nullable=True,
        comment="Analysis results as JSON"
    )

    # Confidence metrics
    confidence_score = Column(
        Float,
        nullable=True,
        index=True,
        comment="Confidence score of the analysis (0.0-1.0)"
    )

    # Relationships
    agent_id = Column(
        Integer,
        ForeignKey("agents.id"),
        nullable=True,
        index=True,
        comment="ID of the agent that performed the analysis"
    )

    scenario_id = Column(
        Integer,
        ForeignKey("scenarios.id"),
        nullable=True,
        index=True,
        comment="ID of the scenario this analysis belongs to"
    )

    # Input data
    input_data = Column(
        JSON,
        nullable=True,
        comment="Input data used for analysis as JSON"
    )

    # Methodology information
    methodology = Column(
        String(100),
        nullable=True,
        comment="Analysis methodology used"
    )

    # Processing time
    processing_time = Column(
        String(50),
        nullable=True,
        comment="Time taken to process the analysis"
    )

    # Additional fields
    title = Column(
        String(200),
        nullable=True,
        comment="Title of the analysis"
    )

    summary = Column(
        Text,
        nullable=True,
        comment="Summary of the analysis results"
    )

    # Data sources
    data_sources = Column(
        JSON,
        nullable=True,
        comment="Data sources used in the analysis"
    )

    # Quality metrics
    completeness_score = Column(
        Float,
        nullable=True,
        comment="Completeness score of the analysis (0.0-1.0)"
    )

    accuracy_score = Column(
        Float,
        nullable=True,
        comment="Accuracy score of the analysis (0.0-1.0)"
    )

    relevance_score = Column(
        Float,
        nullable=True,
        comment="Relevance score of the analysis (0.0-1.0)"
    )

    # Review and validation
    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="ID of the user who reviewed this analysis"
    )

    review_status = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Review status (pending, approved, rejected)"
    )

    review_comments = Column(
        Text,
        nullable=True,
        comment="Comments from the review"
    )

    # Status and workflow
    status = Column(
        String(20),
        nullable=False,
        default='completed',
        index=True,
        comment="Status of the analysis (in_progress, completed, failed)"
    )

    # Version control
    version = Column(
        Integer,
        default=1,
        nullable=False,
        comment="Version of the analysis"
    )

    parent_analysis_id = Column(
        Integer,
        ForeignKey("analysis.id"),
        nullable=True,
        comment="ID of the parent analysis (for analysis chains)"
    )

    # Impact assessment
    impact_level = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Impact level (low, medium, high, critical)"
    )

    urgency_level = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Urgency level (low, medium, high, critical)"
    )

    # Recommendations
    recommendations = Column(
        JSON,
        nullable=True,
        comment="Analysis recommendations as JSON"
    )

    # Tags and classification
    tags = Column(
        JSON,
        nullable=True,
        comment="Tags for classification and search"
    )

    # External references
    external_references = Column(
        JSON,
        nullable=True,
        comment="External references and citations"
    )

    # Relationships
    agent = relationship(
        "Agent",
        back_populates="analysis"
    )

    scenario = relationship(
        "Scenario",
        back_populates="analysis"
    )

    decisions = relationship(
        "Decision",
        back_populates="analysis",
        cascade="all, delete-orphan"
    )

    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by]
    )

    child_analyses = relationship(
        "Analysis",
        backref="parent_analysis",
        remote_side="Analysis.id"
    )

    # Indexes
    __table_args__ = (
        Index('idx_analysis_scenario_type', 'scenario_id', 'type'),
        Index('idx_analysis_agent_created', 'agent_id', 'created_at'),
        Index('idx_analysis_confidence', 'confidence_score'),
        Index('idx_analysis_status', 'status'),
        Index('idx_analysis_review_status', 'review_status'),
        Index('idx_analysis_impact_urgency', 'impact_level', 'urgency_level'),
        Index('idx_analysis_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Analysis(type='{self.type}', confidence={self.confidence_score}, status='{self.status}')>"

    def get_type_description(self) -> str:
        """
        Get human-readable description of analysis type

        Returns:
            Description of the analysis type
        """
        type_descriptions = {
            'situational': 'Situational awareness and current status analysis',
            'risk': 'Risk assessment and threat analysis',
            'resource': 'Resource availability and allocation analysis',
            'impact': 'Impact assessment and consequence analysis',
            'trend': 'Trend analysis and forecasting',
            'vulnerability': 'Vulnerability assessment',
            'capability': 'Capability assessment and gap analysis',
            'operational': 'Operational readiness and effectiveness analysis'
        }
        return type_descriptions.get(self.type, 'Unknown analysis type')

    def is_high_confidence(self) -> bool:
        """
        Check if analysis has high confidence

        Returns:
            True if confidence score is high (>= 0.8), False otherwise
        """
        return self.confidence_score is not None and self.confidence_score >= 0.8

    def is_high_impact(self) -> bool:
        """
        Check if analysis indicates high impact

        Returns:
            True if impact level is high or critical, False otherwise
        """
        return self.impact_level in ['high', 'critical']

    def is_reviewed(self) -> bool:
        """
        Check if analysis has been reviewed

        Returns:
            True if analysis has been reviewed, False otherwise
        """
        return self.review_status in ['approved', 'rejected']

    def get_quality_score(self) -> float:
        """
        Calculate overall quality score

        Returns:
            Overall quality score (0.0-1.0)
        """
        scores = []
        if self.confidence_score is not None:
            scores.append(self.confidence_score)
        if self.completeness_score is not None:
            scores.append(self.completeness_score)
        if self.accuracy_score is not None:
            scores.append(self.accuracy_score)
        if self.relevance_score is not None:
            scores.append(self.relevance_score)

        if scores:
            return sum(scores) / len(scores)
        return 0.0

    def can_be_modified(self, user_id: int) -> bool:
        """
        Check if analysis can be modified by a user

        Args:
            user_id: ID of the user

        Returns:
            True if analysis can be modified, False otherwise
        """
        # Only allow modification if not reviewed yet
        if self.is_reviewed():
            return False

        # Allow modification by the agent that created it or admin users
        # This would need proper permission checking in a real implementation
        return True

    def add_recommendation(self, recommendation: dict) -> None:
        """
        Add a recommendation to the analysis

        Args:
            recommendation: Recommendation details
        """
        if self.recommendations is None:
            self.recommendations = []

        self.recommendations.append({
            'id': len(self.recommendations) + 1,
            'recommendation': recommendation,
            'created_at': self.created_at.isoformat() if self.created_at else None
        })

    def get_key_findings(self) -> list:
        """
        Extract key findings from the analysis results

        Returns:
            List of key findings
        """
        if not self.results:
            return []

        # Extract key findings from results JSON
        # This is a simplified implementation
        key_findings = []

        if isinstance(self.results, dict):
            if 'key_findings' in self.results:
                key_findings = self.results['key_findings']
            elif 'findings' in self.results:
                key_findings = self.results['findings']
            elif 'summary' in self.results:
                key_findings = [self.results['summary']]

        return key_findings

    def get_overall_assessment(self) -> str:
        """
        Get overall assessment from the analysis

        Returns:
            Overall assessment string
        """
        if not self.results or not isinstance(self.results, dict):
            return "No assessment available"

        return self.results.get('overall_assessment', "No assessment available")