"""SAFE-BMAD Agent Framework

This package provides the core agent framework for the SAFE-BMAD system,
including base classes, communication protocols, state management,
and configuration utilities.
"""

from .base.agent_base import SafeAgent, AgentType, AgentStatus
from .base.factory import AgentFactory
from .registry import AgentRegistry

__version__ = "0.1.0"
__all__ = [
    "SafeAgent",
    "AgentType",
    "AgentStatus",
    "AgentFactory",
    "AgentRegistry",
]