"""Agent Configuration Management

This module provides configuration management
for agents in the SAFE system.
"""

from .manager import ConfigManager
from .templates import ConfigTemplate

__all__ = [
    "ConfigManager",
    "ConfigTemplate",
]