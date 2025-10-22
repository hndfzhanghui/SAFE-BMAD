"""Agent Communication Framework

This module provides communication protocols and message handling
for agents in the SAFE system.
"""

from .message_bus import MessageBus
from .protocols import CommunicationProtocol
from .transports import TransportType

__all__ = [
    "MessageBus",
    "CommunicationProtocol",
    "TransportType",
]