"""
Message Model

This module contains the Message SQLAlchemy ORM model for inter-agent communication.
"""

from sqlalchemy import Column, String, Text, JSON, Index, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Message(BaseModel):
    """
    Message model for communication between agents and users
    """

    __tablename__ = "messages"

    # Message content
    content = Column(
        Text,
        nullable=False,
        comment="Content of the message"
    )

    # Message classification
    message_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Type of message (query, response, notification, alert)"
    )

    # Message metadata
    metadata = Column(
        JSON,
        nullable=True,
        comment="Additional message metadata as JSON"
    )

    # Message relationships
    sender_id = Column(
        Integer,
        ForeignKey("agents.id"),
        nullable=True,
        index=True,
        comment="ID of the agent/user who sent the message"
    )

    receiver_id = Column(
        Integer,
        ForeignKey("agents.id"),
        nullable=True,
        index=True,
        comment="ID of the agent/user who received the message"
    )

    # Scenario context
    scenario_id = Column(
        Integer,
        ForeignKey("scenarios.id"),
        nullable=True,
        index=True,
        comment="ID of the scenario this message belongs to"
    )

    # Message status
    status = Column(
        String(20),
        nullable=False,
        default='sent',
        index=True,
        comment="Status of the message (sent, delivered, read, failed)"
    )

    # Read tracking
    read_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the message was read"
    )

    # Attachments and additional content
    attachments = Column(
        JSON,
        nullable=True,
        comment="Message attachments as JSON"
    )

    # Additional fields
    subject = Column(
        String(200),
        nullable=True,
        comment="Subject line of the message"
    )

    priority = Column(
        String(10),
        nullable=True,
        index=True,
        comment="Priority level (low, medium, high, critical)"
    )

    # Message threading
    thread_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Thread ID for grouping related messages"
    )

    parent_message_id = Column(
        Integer,
        ForeignKey("messages.id"),
        nullable=True,
        comment="ID of the parent message for threading"
    )

    # Response information
    response_to = Column(
        Integer,
        ForeignKey("messages.id"),
        nullable=True,
        comment="ID of the message this is responding to"
    )

    # Delivery tracking
    delivery_attempts = Column(
        String(10),
        default=0,
        nullable=False,
        comment="Number of delivery attempts made"
    )

    last_delivery_attempt = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last delivery attempt"
    )

    delivery_error = Column(
        Text,
        nullable=True,
        comment="Error message if delivery failed"
    )

    # Expiration and TTL
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the message expires"
    )

    ttl_seconds = Column(
        String(20),
        nullable=True,
        comment="Time-to-live in seconds"
    )

    # Content processing
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the message was processed"
    )

    processing_status = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Processing status (pending, processing, completed, failed)"
    )

    # External references
    external_message_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="External system message ID"
    )

    source_system = Column(
        String(50),
        nullable=True,
        comment="Source system that generated the message"
    )

    # Tags and classification
    tags = Column(
        JSON,
        nullable=True,
        comment="Tags for classification and search"
    )

    # Relationships
    sender = relationship(
        "Agent",
        foreign_keys=[sender_id],
        back_populates="sent_messages"
    )

    receiver = relationship(
        "Agent",
        foreign_keys=[receiver_id],
        back_populates="received_messages"
    )

    scenario = relationship(
        "Scenario",
        back_populates="messages"
    )

    parent_message = relationship(
        "Message",
        remote_side="Message.id",
        backref="child_messages"
    )

    response_to_message = relationship(
        "Message",
        remote_side="Message.id",
        backref="responses"
    )

    # Indexes
    __table_args__ = (
        Index('idx_messages_scenario_created', 'scenario_id', 'created_at'),
        Index('idx_messages_sender_receiver', 'sender_id', 'receiver_id'),
        Index('idx_messages_status_priority', 'status', 'priority'),
        Index('idx_messages_thread', 'thread_id'),
        Index('idx_messages_type_status', 'message_type', 'status'),
        Index('idx_messages_external_id', 'external_message_id'),
        Index('idx_messages_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Message(type='{self.message_type}', status='{self.status}', sender_id={self.sender_id})>"

    def get_type_description(self) -> str:
        """
        Get human-readable description of message type

        Returns:
            Description of the message type
        """
        type_descriptions = {
            'query': 'Query message requesting information or action',
            'response': 'Response message answering a query',
            'notification': 'Notification message providing information',
            'alert': 'Alert message indicating urgent or important information',
            'command': 'Command message instructing an action',
            'report': 'Report message providing status or results',
            'request': 'Request message asking for resources or assistance',
            'update': 'Update message providing current status',
            'confirmation': 'Confirmation message acknowledging receipt',
            'error': 'Error message reporting a problem'
        }
        return type_descriptions.get(self.message_type, 'Unknown message type')

    def is_read(self) -> bool:
        """
        Check if message has been read

        Returns:
            True if message is read, False otherwise
        """
        return self.read_at is not None

    def is_delivered(self) -> bool:
        """
        Check if message has been delivered

        Returns:
            True if message is delivered, False otherwise
        """
        return self.status in ['delivered', 'read']

    def is_failed(self) -> bool:
        """
        Check if message delivery failed

        Returns:
            True if message delivery failed, False otherwise
        """
        return self.status == 'failed'

    def mark_as_read(self) -> None:
        """
        Mark message as read
        """
        from datetime import datetime
        if not self.read_at:
            self.read_at = datetime.utcnow()
            if self.status == 'delivered':
                self.status = 'read'

    def mark_as_delivered(self) -> None:
        """
        Mark message as delivered
        """
        if self.status == 'sent':
            self.status = 'delivered'

    def mark_as_failed(self, error_message: str) -> None:
        """
        Mark message as failed

        Args:
            error_message: Error message describing the failure
        """
        from datetime import datetime

        self.status = 'failed'
        self.delivery_error = error_message
        self.last_delivery_attempt = datetime.utcnow()
        self.delivery_attempts = str(int(self.delivery_attempts) + 1)

    def is_expired(self) -> bool:
        """
        Check if message has expired

        Returns:
            True if message is expired, False otherwise
        """
        if self.expires_at:
            from datetime import datetime
            return datetime.utcnow() > self.expires_at
        return False

    def get_thread_messages(self) -> list:
        """
        Get all messages in the same thread

        Returns:
            List of messages in the same thread
        """
        # This would need a database query in a real implementation
        # For now, return empty list
        return []

    def add_attachment(self, attachment: dict) -> None:
        """
        Add an attachment to the message

        Args:
            attachment: Attachment details
        """
        if self.attachments is None:
            self.attachments = []

        self.attachments.append({
            'id': len(self.attachments) + 1,
            'attachment': attachment,
            'added_at': self.created_at.isoformat() if self.created_at else None
        })

    def get_priority_level(self) -> int:
        """
        Get priority level as integer

        Returns:
            Priority level (1=low, 2=medium, 3=high, 4=critical) or None
        """
        priority_map = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        return priority_map.get(self.priority)

    def is_high_priority(self) -> bool:
        """
        Check if message is high priority

        Returns:
            True if message is high or critical priority, False otherwise
        """
        return self.priority in ['high', 'critical']

    def get_content_preview(self, max_length: int = 100) -> str:
        """
        Get a preview of the message content

        Args:
            max_length: Maximum length of the preview

        Returns:
            Content preview string
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."