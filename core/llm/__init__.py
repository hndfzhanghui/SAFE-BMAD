"""SAFE-BMAD LLM Integration Module

This module provides unified Large Language Model integration
supporting multiple LLM providers and models.
"""

from .manager import LLMManager, get_llm_manager
from .adapters import (
    BaseLLMAdapter,
    DeepSeekAdapter,
    OpenAIAdapter,
    LocalModelAdapter
)
from .types import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMConfig,
    LLMCapability
)

__version__ = "0.1.0"
__all__ = [
    "LLMManager",
    "get_llm_manager",
    "BaseLLMAdapter",
    "DeepSeekAdapter",
    "OpenAIAdapter",
    "LocalModelAdapter",
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "LLMConfig",
    "LLMCapability"
]