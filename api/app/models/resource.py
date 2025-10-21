"""
Resource Model

This module contains the Resource SQLAlchemy ORM model for emergency resources.
"""

from sqlalchemy import Column, String, JSON, Index, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Resource(BaseModel):
    """
    Resource model for emergency response resources
    """

    __tablename__ = "resources"

    # Basic resource information
    name = Column(
        String(200),
        nullable=False,
        comment="Name of the resource"
    )

    # Resource classification
    type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of resource (personnel, equipment, facility, supply)"
    )

    # Resource status
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Status of the resource (available, deployed, maintenance, unavailable)"
    )

    # Location information
    location = Column(
        JSON,
        nullable=True,
        comment="Resource location as JSON (coordinates, address, etc.)"
    )

    # Specifications and details
    specifications = Column(
        JSON,
        nullable=True,
        comment="Technical specifications as JSON"
    )

    # Quantity information
    quantity = Column(
        Integer,
        nullable=True,
        comment="Quantity of the resource"
    )

    unit = Column(
        String(20),
        nullable=True,
        comment="Unit of measurement for the resource"
    )

    # Scenario relationship
    scenario_id = Column(
        Integer,
        ForeignKey("scenarios.id"),
        nullable=True,
        index=True,
        comment="ID of the scenario this resource belongs to"
    )

    # Allocation tracking
    allocation_history = Column(
        JSON,
        nullable=True,
        comment="Allocation history as JSON"
    )

    # Contact information
    contact_info = Column(
        JSON,
        nullable=True,
        comment="Contact information as JSON"
    )

    # Additional fields
    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the resource"
    )

    # Availability
    available_from = Column(
        String(50),
        nullable=True,
        comment="Timestamp when resource becomes available"
    )

    available_until = Column(
        String(50),
        nullable=True,
        comment="Timestamp when resource becomes unavailable"
    )

    # Priority
    priority = Column(
        String(10),
        nullable=True,
        index=True,
        comment="Priority level (low, medium, high, critical)"
    )

    # Cost information
    cost_per_hour = Column(
        String(20),
        nullable=True,
        comment="Cost per hour to use this resource"
    )

    total_cost = Column(
        String(20),
        nullable=True,
        comment="Total cost for the resource"
    )

    # Deployment information
    deployed_at = Column(
        String(50),
        nullable=True,
        comment="Timestamp when resource was deployed"
    )

    deployment_location = Column(
        JSON,
        nullable=True,
        comment="Current deployment location as JSON"
    )

    # Maintenance information
    last_maintenance = Column(
        String(50),
        nullable=True,
        comment="Timestamp of last maintenance"
    )

    next_maintenance = Column(
        String(50),
        nullable=True,
        comment="Timestamp of next scheduled maintenance"
    )

    # Performance metrics
    utilization_rate = Column(
        String(10),
        nullable=True,
        comment="Current utilization rate percentage"
    )

    efficiency_score = Column(
        String(10),
        nullable=True,
        comment="Efficiency score (1-10)"
    )

    # Requirements and dependencies
    requirements = Column(
        JSON,
        nullable=True,
        comment="Requirements for using this resource as JSON"
    )

    dependencies = Column(
        JSON,
        nullable=True,
        comment="Dependencies on other resources as JSON"
    )

    # Tags and classification
    tags = Column(
        JSON,
        nullable=True,
        comment="Tags for classification and search"
    )

    # External references
    external_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="External system ID for this resource"
    )

    supplier = Column(
        String(200),
        nullable=True,
        comment="Supplier or provider of this resource"
    )

    # Relationships
    scenario = relationship(
        "Scenario",
        back_populates="resources"
    )

    # Indexes
    __table_args__ = (
        Index('idx_resources_scenario_status', 'scenario_id', 'status'),
        Index('idx_resources_type_status', 'type', 'status'),
        Index('idx_resources_priority', 'priority'),
        Index('idx_resources_location', 'location'),
        Index('idx_resources_created_at', 'created_at'),
        Index('idx_resources_external_id', 'external_id'),
    )

    def __repr__(self) -> str:
        return f"<Resource(name='{self.name}', type='{self.type}', status='{self.status}')>"

    def get_type_description(self) -> str:
        """
        Get human-readable description of resource type

        Returns:
            Description of the resource type
        """
        type_descriptions = {
            'personnel': 'Human resources - staff, experts, responders',
            'equipment': 'Equipment and machinery - vehicles, tools, devices',
            'facility': 'Facilities and infrastructure - buildings, hospitals, shelters',
            'supply': 'Supplies and materials - food, water, medical supplies',
            'vehicle': 'Vehicles - trucks, ambulances, aircraft',
            'communication': 'Communication equipment - radios, satellite systems',
            'medical': 'Medical resources - hospitals, clinics, medical equipment',
            'shelter': 'Shelter resources - temporary housing, tents',
            'food': 'Food and water resources',
            'power': 'Power generation and distribution resources'
        }
        return type_descriptions.get(self.type, 'Unknown resource type')

    def is_available(self) -> bool:
        """
        Check if resource is currently available

        Returns:
            True if resource is available, False otherwise
        """
        return self.status == 'available'

    def is_deployed(self) -> bool:
        """
        Check if resource is currently deployed

        Returns:
            True if resource is deployed, False otherwise
        """
        return self.status == 'deployed'

    def can_be_deployed(self) -> bool:
        """
        Check if resource can be deployed

        Returns:
            True if resource can be deployed, False otherwise
        """
        return self.status in ['available', 'maintenance']

    def deploy(self, location: dict, deployed_by: int) -> None:
        """
        Deploy the resource to a location

        Args:
            location: Deployment location details
            deployed_by: ID of the user deploying the resource
        """
        from datetime import datetime

        self.status = 'deployed'
        self.deployment_location = location
        self.deployed_at = datetime.utcnow().isoformat()

        # Add to allocation history
        if self.allocation_history is None:
            self.allocation_history = []

        self.allocation_history.append({
            'action': 'deployed',
            'location': location,
            'deployed_by': deployed_by,
            'timestamp': self.deployed_at
        })

    def recall(self) -> None:
        """
        Recall the resource from deployment
        """
        from datetime import datetime

        if self.status == 'deployed':
            self.status = 'available'
            self.deployment_location = None
            self.deployed_at = None

            # Add to allocation history
            if self.allocation_history is None:
                self.allocation_history = []

            self.allocation_history.append({
                'action': 'recalled',
                'timestamp': datetime.utcnow().isoformat()
            })

    def get_efficiency_rating(self) -> int:
        """
        Get efficiency rating as integer

        Returns:
            Efficiency rating (1-10) or None
        """
        if self.efficiency_score:
            try:
                return int(self.efficiency_score)
            except (ValueError, TypeError):
                pass
        return None

    def is_efficient(self) -> bool:
        """
        Check if resource is efficient (rating >= 7)

        Returns:
            True if resource is efficient, False otherwise
        """
        rating = self.get_efficiency_rating()
        return rating is not None and rating >= 7

    def add_allocation_record(self, action: str, details: dict) -> None:
        """
        Add an allocation record to the history

        Args:
            action: Action type (deployed, recalled, transferred, maintained)
            details: Action details
        """
        from datetime import datetime

        if self.allocation_history is None:
            self.allocation_history = []

        self.allocation_history.append({
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })

    def get_current_location(self) -> dict:
        """
        Get current location of the resource

        Returns:
            Current location as dict or None
        """
        if self.deployment_location:
            return self.deployment_location
        elif self.location:
            return self.location
        return None

    def get_utilization_percentage(self) -> float:
        """
        Get utilization rate as percentage

        Returns:
            Utilization rate as float (0-100) or None
        """
        if self.utilization_rate:
            try:
                return float(self.utilization_rate.rstrip('%'))
            except (ValueError, AttributeError):
                pass
        return None