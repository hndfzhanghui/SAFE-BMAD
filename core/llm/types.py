"""LLM Types and Enums

This module defines the core types and enums used throughout
the LLM integration system.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime


class LLMProvider(Enum):
    """LLM提供商枚举"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    LOCAL = "local"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    ZHIPUAI = "zhipuai"
    QWEN = "qwen"
    GLM = "glm"
    CUSTOM = "custom"


class LLMCapability(Enum):
    """LLM能力枚举"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    REASONING = "reasoning"
    CONVERSATION = "conversation"
    TOOL_CALLING = "tool_calling"
    MULTIMODAL = "multimodal"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"


@dataclass
class LLMMessage:
    """LLM消息类"""
    role: str  # system, user, assistant, tool
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，兼容不同LLM API"""
        return {
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "tool_calls": self.tool_calls,
            "tool_call_id": self.tool_call_id,
            "metadata": self.metadata
        }


@dataclass
class LLMResponse:
    """LLM响应类"""
    content: str
    model: str
    provider: LLMProvider
    usage: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    response_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider.value,
            "usage": self.usage,
            "tool_calls": self.tool_calls,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata,
            "response_time": self.response_time,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class LLMConfig:
    """LLM配置类"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    retry_count: int = 3
    capabilities: List[LLMCapability] = field(default_factory=list)
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "api_key": self.api_key,
            "api_base": self.api_base,
            "api_version": self.api_version,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "capabilities": [cap.value for cap in self.capabilities],
            "extra_params": self.extra_params
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        """从字典创建配置"""
        # 转换capabilities
        capabilities = []
        if "capabilities" in data:
            capabilities = [LLMCapability(cap) for cap in data["capabilities"]]

        config = cls(
            provider=LLMProvider(data["provider"]),
            model=data["model"],
            api_key=data.get("api_key"),
            api_base=data.get("api_base"),
            api_version=data.get("api_version"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4000),
            top_p=data.get("top_p", 1.0),
            frequency_penalty=data.get("frequency_penalty", 0.0),
            presence_penalty=data.get("presence_penalty", 0.0),
            timeout=data.get("timeout", 30),
            retry_count=data.get("retry_count", 3),
            capabilities=capabilities,
            extra_params=data.get("extra_params", {})
        )
        return config


@dataclass
class LLMTool:
    """LLM工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: callable = None
    enabled: bool = True

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI工具格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class LLMChatSession:
    """LLM聊天会话"""
    session_id: str
    messages: List[LLMMessage] = field(default_factory=list)
    config: Optional[LLMConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def add_message(self, message: LLMMessage) -> None:
        """添加消息"""
        self.messages.append(message)
        self.last_activity = datetime.now()

    def get_messages(self, include_system: bool = True) -> List[LLMMessage]:
        """获取消息列表"""
        if include_system:
            return self.messages
        return [msg for msg in self.messages if msg.role != "system"]


@dataclass
class LLMMetrics:
    """LLM使用指标"""
    provider: LLMProvider
    model: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None

    def update_success(self, response_time: float, usage: Optional[Dict[str, Any]] = None) -> None:
        """更新成功请求指标"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_response_time += response_time
        self.average_response_time = self.total_response_time / self.successful_requests
        self.last_request_time = datetime.now()

        if usage and "total_tokens" in usage:
            self.total_tokens_used += usage["total_tokens"]

    def update_failure(self) -> None:
        """更新失败请求指标"""
        self.total_requests += 1
        self.failed_requests += 1

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


# 预定义的模型配置
PREDEFINED_MODELS = {
    LLMProvider.DEEPSEEK: {
        "deepseek-chat": {
            "description": "DeepSeek Chat Model",
            "capabilities": [
                LLMCapability.TEXT_GENERATION,
                LLMCapability.ANALYSIS,
                LLMCapability.REASONING,
                LLMCapability.CONVERSATION,
                LLMCapability.CODE_GENERATION,
                LLMCapability.STREAMING
            ],
            "max_tokens": 4096,
            "default_temperature": 0.7
        },
        "deepseek-coder": {
            "description": "DeepSeek Coder Model",
            "capabilities": [
                LLMCapability.CODE_GENERATION,
                LLMCapability.ANALYSIS,
                LLMCapability.REASONING,
                LLMCapability.TOOL_CALLING
            ],
            "max_tokens": 4096,
            "default_temperature": 0.1
        }
    },
    LLMProvider.OPENAI: {
        "gpt-4": {
            "description": "OpenAI GPT-4",
            "capabilities": [
                LLMCapability.TEXT_GENERATION,
                LLMCapability.ANALYSIS,
                LLMCapability.REASONING,
                LLMCapability.CONVERSATION,
                LLMCapability.FUNCTION_CALLING,
                LLMCapability.JSON_MODE
            ],
            "max_tokens": 8192,
            "default_temperature": 0.7
        },
        "gpt-4-turbo": {
            "description": "OpenAI GPT-4 Turbo",
            "capabilities": [
                LLMCapability.TEXT_GENERATION,
                LLMCapability.ANALYSIS,
                LLMCapability.REASONING,
                LLMCapability.CONVERSATION,
                LLMCapability.FUNCTION_CALLING,
                LLMCapability.JSON_MODE,
                LLMCapability.STREAMING
            ],
            "max_tokens": 4096,
            "default_temperature": 0.7
        },
        "gpt-3.5-turbo": {
            "description": "OpenAI GPT-3.5 Turbo",
            "capabilities": [
                LLMCapability.TEXT_GENERATION,
                LLMCapability.CONVERSATION,
                LLMCapability.FUNCTION_CALLING,
                LLMCapability.STREAMING
            ],
            "max_tokens": 4096,
            "default_temperature": 0.7
        }
    },

    LLMProvider.GLM: {
        "glm-4": {
            "description": "GLM-4 - Latest generation model from Zhipu AI",
            "capabilities": [
                LLMCapability.TEXT_GENERATION,
                LLMCapability.CODE_GENERATION,
                LLMCapability.ANALYSIS,
                LLMCapability.REASONING,
                LLMCapability.CONVERSATION,
                LLMCapability.FUNCTION_CALLING,
                LLMCapability.STREAMING,
                LLMCapability.JSON_MODE
            ],
            "max_tokens": 8192,
            "default_temperature": 0.7
        },
        "glm-3-turbo": {
            "description": "GLM-3 Turbo - Efficient model for fast responses",
            "capabilities": [
                LLMCapability.TEXT_GENERATION,
                LLMCapability.CONVERSATION,
                LLMCapability.STREAMING
            ],
            "max_tokens": 4096,
            "default_temperature": 0.7
        },
        "glm-4v": {
            "description": "GLM-4V - Multimodal model with vision capabilities",
            "capabilities": [
                LLMCapability.TEXT_GENERATION,
                LLMCapability.MULTIMODAL,
                LLMCapability.ANALYSIS,
                LLMCapability.CONVERSATION,
                LLMCapability.STREAMING
            ],
            "max_tokens": 8192,
            "default_temperature": 0.7
        },
        "glm-4-long": {
            "description": "GLM-4 Long - Extended context model",
            "capabilities": [
                LLMCapability.TEXT_GENERATION,
                LLMCapability.ANALYSIS,
                LLMCapability.REASONING,
                LLMCapability.CONVERSATION,
                LLMCapability.STREAMING
            ],
            "max_tokens": 32768,
            "default_temperature": 0.7
        }
    }
}


def get_model_info(provider: LLMProvider, model: str) -> Optional[Dict[str, Any]]:
    """获取预定义模型信息"""
    return PREDEFINED_MODELS.get(provider, {}).get(model)


def get_available_models(provider: LLMProvider) -> List[str]:
    """获取可用的模型列表"""
    if provider in PREDEFINED_MODELS:
        return list(PREDEFINED_MODELS[provider].keys())
    return []


def validate_model_config(config: LLMConfig) -> List[str]:
    """验证模型配置"""
    errors = []

    if not config.provider:
        errors.append("Provider is required")

    if not config.model:
        errors.append("Model is required")

    if config.provider in [LLMProvider.OPENAI, LLMProvider.DEEPSEEK, LLMProvider.ANTHROPIC]:
        if not config.api_key:
            errors.append(f"API key is required for {config.provider.value}")

    if config.temperature < 0 or config.temperature > 2:
        errors.append("Temperature must be between 0 and 2")

    if config.max_tokens <= 0:
        errors.append("Max tokens must be positive")

    return errors