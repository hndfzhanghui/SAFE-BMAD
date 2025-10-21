"""
Agent Model

This module contains the Agent SQLAlchemy ORM model for S-A-F-E-R agents.
"""

from sqlalchemy import Column, String, Text, JSON, Index, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Agent(BaseModel):
    """
    Agent model for S-A-F-E-R intelligent agents
    """

    __tablename__ = "agents"

    # Basic agent information
    name = Column(
        String(100),
        nullable=False,
        comment="Name of the agent"
    )

    # Agent type (S-A-F-E-R framework)
    type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Agent type (S, A, F, E, E)"
    )

    # Agent status
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Agent status (idle, running, paused, error, completed)"
    )

    # Configuration and capabilities
    configuration = Column(
        JSON,
        nullable=True,
        comment="Agent configuration parameters as JSON"
    )

    capabilities = Column(
        JSON,
        nullable=True,
        comment="Agent capabilities description as JSON"
    )

    # Scenario relationship
    scenario_id = Column(
        Integer,
        ForeignKey("scenarios.id"),
        nullable=True,
        index=True,
        comment="ID of the scenario this agent belongs to"
    )

    # Activity tracking
    last_activity = Column(
        JSON,
        nullable=True,
        comment="Last activity details as JSON"
    )

    # AI model information
    model_name = Column(
        String(50),
        nullable=True,
        comment="Name of the AI model used by this agent"
    )

    # Performance metrics
    performance_metrics = Column(
        JSON,
        nullable=True,
        comment="Performance metrics as JSON"
    )

    # Additional fields
    description = Column(
        Text,
        nullable=True,
        comment="Description of the agent's role and function"
    )

    # Agent state and configuration
    state = Column(
        JSON,
        nullable=True,
        comment="Current state of the agent as JSON"
    )

    # Task management
    current_task = Column(
        JSON,
        nullable=True,
        comment="Current task being processed as JSON"
    )

    task_queue = Column(
        JSON,
        nullable=True,
        comment="Queue of pending tasks as JSON"
    )

    # Communication
    communication_channel = Column(
        String(100),
        nullable=True,
        comment="Communication channel for the agent"
    )

    # Resource usage
    cpu_usage = Column(
        Float,
        nullable=True,
        comment="Current CPU usage percentage"
    )

    memory_usage = Column(
        Float,
        nullable=True,
        comment="Current memory usage in MB"
    )

    # Error handling
    error_count = Column(
        Float,
        default=0,
        nullable=False,
        comment="Number of errors encountered"
    )

    last_error = Column(
        JSON,
        nullable=True,
        comment="Last error details as JSON"
    )

    # Health monitoring
    health_score = Column(
        Float,
        default=100.0,
        nullable=False,
        comment="Health score of the agent (0-100)"
    )

    last_heartbeat = Column(
        String(50),
        nullable=True,
        comment="Timestamp of last heartbeat"
    )

    # Version and updates
    version = Column(
        String(20),
        nullable=True,
        comment="Version of the agent software"
    )

    update_available = Column(
        String(100),
        nullable=True,
        comment="Available update version"
    )

    # Relationships
    scenario = relationship(
        "Scenario",
        back_populates="agents"
    )

    analysis = relationship(
        "Analysis",
        back_populates="agent",
        cascade="all, delete-orphan"
    )

    sent_messages = relationship(
        "Message",
        foreign_keys="Message.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )

    received_messages = relationship(
        "Message",
        foreign_keys="Message.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_agents_scenario_status', 'scenario_id', 'status'),
        Index('idx_agents_type_status', 'type', 'status'),
        Index('idx_agents_created_at', 'created_at'),
        Index('idx_agents_health_score', 'health_score'),
        Index('idx_agents_last_heartbeat', 'last_heartbeat'),
    )

    def __repr__(self) -> str:
        return f"<Agent(name='{self.name}', type='{self.type}', status='{self.status}')>"

    def get_type_description(self) -> str:
        """
        Get human-readable description of agent type

        Returns:
            Description of the agent type
        """
        type_descriptions = {
            'S': 'Searcher - Information gathering and reconnaissance specialist',
            'A': 'Analyst - Data analysis and situation assessment expert',
            'F': 'Frontline - Tactical response and field operations specialist',
            'E': 'Executive - Strategic decision making and coordination expert',
            'E': 'Evaluator - Performance assessment and learning specialist'
        }
        return type_descriptions.get(self.type, 'Unknown agent type')

    def is_active(self) -> bool:
        """
        Check if agent is currently active

        Returns:
            True if agent is active, False otherwise
        """
        return self.status == 'running'

    def is_healthy(self) -> bool:
        """
        Check if agent is healthy based on health score

        Returns:
            True if agent is healthy, False otherwise
        """
        return self.health_score >= 70.0

    def can_process_task(self) -> bool:
        """
        Check if agent can process new tasks

        Returns:
            True if agent can process tasks, False otherwise
        """
        return (self.status == 'running' and
                self.is_healthy() and
                self.error_count < 5)

    def update_status(self, new_status: str, error_details: dict = None) -> None:
        """
        Update agent status

        Args:
            new_status: New status to set
            error_details: Optional error details if status is error
        """
        self.status = new_status

        if new_status == 'error' and error_details:
            self.error_count += 1
            self.last_error = error_details
            self.health_score = max(0, self.health_score - 10)
        elif new_status == 'running':
            self.health_score = min(100, self.health_score + 5)

    def record_activity(self, activity_type: str, details: dict) -> None:
        """
        Record agent activity

        Args:
            activity_type: Type of activity
            details: Activity details
        """
        from datetime import datetime

        self.last_activity = {
            'type': activity_type,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }

    def add_task(self, task: dict) -> None:
        """
        Add a task to the agent's queue

        Args:
            task: Task details
        """
        if self.task_queue is None:
            self.task_queue = []

        self.task_queue.append({
            'id': len(self.task_queue) + 1,
            'task': task,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        })

    def get_next_task(self) -> dict:
        """
        Get the next task from the queue

        Returns:
            Next task or None if queue is empty
        """
        if not self.task_queue:
            return None

        # Find first pending task
        for task in self.task_queue:
            if task.get('status') == 'pending':
                return task

        return None

    def complete_task(self, task_id: int, result: dict) -> None:
        """
        Mark a task as completed

        Args:
            task_id: ID of the task to complete
            result: Task result
        """
        if self.task_queue:
            for task in self.task_queue:
                if task.get('id') == task_id:
                    task['status'] = 'completed'
                    task['result'] = result
                    task['completed_at'] = datetime.utcnow().isoformat()
                    break

    def get_performance_summary(self) -> dict:
        """
        Get performance summary

        Returns:
            Performance summary dictionary
        """
        return {
            'health_score': self.health_score,
            'error_count': self.error_count,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'tasks_completed': len([t for t in self.task_queue or [] if t.get('status') == 'completed']),
            'tasks_pending': len([t for t in self.task_queue or [] if t.get('status') == 'pending']),
            'last_activity': self.last_activity
        }