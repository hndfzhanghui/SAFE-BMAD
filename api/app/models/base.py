"""
Base Model Class

This module contains the base SQLAlchemy model class with common fields and methods.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, Integer, DateTime, Boolean, text
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import func

Base = declarative_base()


class BaseModel(Base):
    """
    Base model class with common fields and methods
    """

    __abstract__ = True

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the record was last updated"
    )

    @declared_attr
    def __tablename__(cls):
        """
        Generate table name from class name
        """
        return cls.__name__.lower()

    def to_dict(self, exclude_fields: list = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary

        Args:
            exclude_fields: List of field names to exclude

        Returns:
            Dictionary representation of the model
        """
        exclude_fields = exclude_fields or []
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Handle datetime serialization
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value

        return result

    def to_dict_nested(self, depth: int = 1, exclude_fields: list = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary with nested relationships

        Args:
            depth: Depth of nested relationships to include
            exclude_fields: List of field names to exclude

        Returns:
            Dictionary representation with nested relationships
        """
        if depth <= 0:
            return self.to_dict(exclude_fields=exclude_fields)

        exclude_fields = exclude_fields or []
        result = self.to_dict(exclude_fields=exclude_fields)

        # Add relationship data if depth > 0
        for relationship in self.__mapper__.relationships:
            if relationship.key not in exclude_fields:
                related_obj = getattr(self, relationship.key)

                if related_obj is not None:
                    if hasattr(related_obj, '__iter__') and not isinstance(related_obj, str):
                        # Handle collection relationships
                        result[relationship.key] = [
                            item.to_dict_nested(depth - 1)
                            if hasattr(item, 'to_dict_nested')
                            else item.to_dict() if hasattr(item, 'to_dict') else str(item)
                            for item in related_obj
                        ]
                    else:
                        # Handle single relationships
                        result[relationship.key] = (
                            related_obj.to_dict_nested(depth - 1)
                            if hasattr(related_obj, 'to_dict_nested')
                            else related_obj.to_dict() if hasattr(related_obj, 'to_dict') else str(related_obj)
                        )

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any], exclude_fields: list = None):
        """
        Create model instance from dictionary

        Args:
            data: Dictionary with field values
            exclude_fields: List of field names to exclude

        Returns:
            Model instance
        """
        exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']

        # Filter data to only include valid model fields
        valid_fields = {
            column.name: value
            for column in cls.__table__.columns
            if column.name not in exclude_fields and column.name in data
        }

        return cls(**valid_fields)

    def update_from_dict(self, data: Dict[str, Any], exclude_fields: list = None):
        """
        Update model instance from dictionary

        Args:
            data: Dictionary with field values
            exclude_fields: List of field names to exclude
        """
        exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']

        for field, value in data.items():
            if field not in exclude_fields and hasattr(self, field):
                setattr(self, field, value)

    def __repr__(self) -> str:
        """
        String representation of the model
        """
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """
    Mixin class for timestamp fields
    """

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the record was last updated"
    )


class SoftDeleteMixin:
    """
    Mixin class for soft delete functionality
    """

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the record was soft deleted"
    )

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Flag indicating if the record is soft deleted"
    )

    def soft_delete(self):
        """
        Mark the record as deleted
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """
        Restore the soft deleted record
        """
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """
    Mixin class for audit fields
    """

    created_by = Column(
        Integer,
        nullable=True,
        comment="ID of the user who created the record"
    )

    updated_by = Column(
        Integer,
        nullable=True,
        comment="ID of the user who last updated the record"
    )

    deleted_by = Column(
        Integer,
        nullable=True,
        comment="ID of the user who deleted the record"
    )