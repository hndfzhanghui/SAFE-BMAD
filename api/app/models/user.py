"""
User Model

This module contains the User SQLAlchemy ORM model.
"""

from sqlalchemy import Column, String, Boolean, JSON, Index, DateTime, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class User(BaseModel):
    """
    User model for system users
    """

    __tablename__ = "users"

    # Basic user information
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username for the user"
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="User's email address"
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Hashed password for authentication"
    )

    full_name = Column(
        String(100),
        nullable=True,
        comment="User's full name"
    )

    # Role and permissions
    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user is a superuser"
    )

    role = Column(
        String(20),
        nullable=False,
        default="viewer",
        index=True,
        comment="User role (admin, operator, analyst, viewer)"
    )

    # User preferences and settings
    preferences = Column(
        JSON,
        nullable=True,
        comment="User preferences and settings as JSON"
    )

    # Account status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the user account is active"
    )

    # Additional fields
    phone_number = Column(
        String(20),
        nullable=True,
        comment="User's phone number"
    )

    department = Column(
        String(100),
        nullable=True,
        comment="User's department or organization"
    )

    title = Column(
        String(100),
        nullable=True,
        comment="User's job title or position"
    )

    # Email verification
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user's email has been verified"
    )

    verification_token = Column(
        String(255),
        nullable=True,
        comment="Token for email verification"
    )

    # Password reset
    reset_token = Column(
        String(255),
        nullable=True,
        comment="Token for password reset"
    )

    reset_token_expires = Column(
        DateTime,
        nullable=True,
        comment="Expiry time for password reset token"
    )

    # Last login tracking
    last_login = Column(
        DateTime,
        nullable=True,
        comment="Timestamp of last login"
    )

    login_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times the user has logged in"
    )

    # Relationships
    created_scenarios = relationship(
        "Scenario",
        back_populates="creator",
        foreign_keys="Scenario.created_by_id"
    )

    user_scenarios = relationship(
        "UserScenario",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    decisions = relationship(
        "Decision",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_users_username_active', 'username', 'is_active'),
        Index('idx_users_email_active', 'email', 'is_active'),
        Index('idx_users_role_active', 'role', 'is_active'),
        Index('idx_users_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role}')>"

    def to_dict(self, exclude_fields: list = None) -> dict:
        """
        Convert user to dictionary, excluding sensitive fields
        """
        if exclude_fields is None:
            exclude_fields = ['hashed_password', 'verification_token', 'reset_token']

        return super().to_dict(exclude_fields=exclude_fields)

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission based on role

        Args:
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        role_permissions = {
            'admin': [
                'create_user', 'read_user', 'update_user', 'delete_user',
                'create_scenario', 'read_scenario', 'update_scenario', 'delete_scenario',
                'create_agent', 'read_agent', 'update_agent', 'delete_agent',
                'create_analysis', 'read_analysis', 'update_analysis', 'delete_analysis',
                'create_decision', 'read_decision', 'update_decision', 'delete_decision',
                'create_resource', 'read_resource', 'update_resource', 'delete_resource',
                'system_admin', 'view_logs'
            ],
            'operator': [
                'create_scenario', 'read_scenario', 'update_scenario',
                'create_agent', 'read_agent', 'update_agent',
                'create_analysis', 'read_analysis', 'update_analysis',
                'create_decision', 'read_decision', 'update_decision',
                'create_resource', 'read_resource', 'update_resource'
            ],
            'analyst': [
                'read_scenario', 'create_analysis', 'read_analysis', 'update_analysis',
                'read_decision', 'create_decision', 'read_decision', 'update_decision',
                'read_resource'
            ],
            'viewer': [
                'read_scenario', 'read_analysis', 'read_decision', 'read_resource'
            ]
        }

        return permission in role_permissions.get(self.role, [])

    def can_access_scenario(self, scenario) -> bool:
        """
        Check if user can access a specific scenario

        Args:
            scenario: Scenario object or scenario ID

        Returns:
            True if user can access scenario, False otherwise
        """
        if self.role in ['admin']:
            return True

        # Check if user is the creator
        if hasattr(scenario, 'created_by_id'):
            return scenario.created_by_id == self.id
        elif isinstance(scenario, int):
            # This would require a database query in a real implementation
            return False

        # Check if user is assigned to the scenario
        # This would require checking the user_scenarios table
        return False