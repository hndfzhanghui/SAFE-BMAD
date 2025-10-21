"""
Association Models

This module contains association table models for many-to-many relationships.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class UserScenario(BaseModel):
    """
    Association table for users and scenarios (many-to-many relationship)
    """

    __tablename__ = "user_scenarios"

    # Foreign keys
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        primary_key=True,
        comment="ID of the user"
    )

    scenario_id = Column(
        Integer,
        ForeignKey("scenarios.id"),
        nullable=False,
        primary_key=True,
        comment="ID of the scenario"
    )

    # Association attributes
    role = Column(
        String(50),
        nullable=True,
        comment="Role of the user in this scenario"
    )

    joined_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the user joined the scenario"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the user is active in this scenario"
    )

    # Permissions
    can_edit = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user can edit this scenario"
    )

    can_delete = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user can delete this scenario"
    )

    can_manage_agents = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user can manage agents in this scenario"
    )

    # Additional fields
    last_accessed = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the user last accessed this scenario"
    )

    access_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times the user accessed this scenario"
    )

    # Notifications
    notifications_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user receives notifications for this scenario"
    )

    notification_preferences = Column(
        String(100),
        nullable=True,
        comment="User's notification preferences for this scenario"
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="user_scenarios"
    )

    scenario = relationship(
        "Scenario",
        back_populates="user_scenarios"
    )

    # Indexes
    __table_args__ = (
        Index('idx_user_scenarios_user_active', 'user_id', 'is_active'),
        Index('idx_user_scenarios_scenario_active', 'scenario_id', 'is_active'),
        Index('idx_user_scenarios_role', 'role'),
        Index('idx_user_scenarios_joined_at', 'joined_at'),
    )

    def __repr__(self) -> str:
        return f"<UserScenario(user_id={self.user_id}, scenario_id={self.scenario_id}, role='{self.role}')>"

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has specific permission for this scenario

        Args:
            permission: Permission to check (edit, delete, manage_agents)

        Returns:
            True if user has permission, False otherwise
        """
        permission_map = {
            'edit': self.can_edit,
            'delete': self.can_delete,
            'manage_agents': self.can_manage_agents
        }
        return permission_map.get(permission, False)

    def grant_permission(self, permission: str) -> None:
        """
        Grant a permission to the user for this scenario

        Args:
            permission: Permission to grant (edit, delete, manage_agents)
        """
        if permission == 'edit':
            self.can_edit = True
        elif permission == 'delete':
            self.can_delete = True
        elif permission == 'manage_agents':
            self.can_manage_agents = True

    def revoke_permission(self, permission: str) -> None:
        """
        Revoke a permission from the user for this scenario

        Args:
            permission: Permission to revoke (edit, delete, manage_agents)
        """
        if permission == 'edit':
            self.can_edit = False
        elif permission == 'delete':
            self.can_delete = False
        elif permission == 'manage_agents':
            self.can_manage_agents = False

    def update_access(self) -> None:
        """
        Update access tracking information
        """
        from datetime import datetime
        self.last_accessed = datetime.utcnow()
        self.access_count += 1