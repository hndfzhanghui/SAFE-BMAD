"""Core Types for SAFE Agent Framework

This module defines the core types and enums used throughout the agent framework.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class AgentType(Enum):
    """SAFE Agent类型枚举"""
    S_AGENT = "strategist"      # 战略协调官
    A_AGENT = "awareness"       # 态势感知专家
    F_AGENT = "field_expert"    # 领域专家
    E_AGENT = "executor"        # 执行协调官
    R_AGENT = "reviewer"        # 复盘评估者


class AgentStatus(Enum):
    """Agent状态枚举"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    BROADCAST = "broadcast"


class Priority(Enum):
    """消息优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentMessage:
    """Agent消息基类"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    receiver_id: str = ""
    message_type: MessageType = MessageType.NOTIFICATION
    priority: Priority = Priority.NORMAL
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """从字典创建消息对象"""
        message = cls()
        message.message_id = data.get("message_id", str(uuid.uuid4()))
        message.sender_id = data.get("sender_id", "")
        message.receiver_id = data.get("receiver_id", "")
        message.message_type = MessageType(data.get("message_type", MessageType.NOTIFICATION.value))
        message.priority = Priority(data.get("priority", Priority.NORMAL.value))
        message.content = data.get("content", {})

        # 解析时间戳
        if "timestamp" in data:
            message.timestamp = datetime.fromisoformat(data["timestamp"])

        message.correlation_id = data.get("correlation_id")
        message.reply_to = data.get("reply_to")
        message.metadata = data.get("metadata", {})

        return message


@dataclass
class AgentConfig:
    """Agent配置类"""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str = ""
    llm_config: Optional[Dict[str, Any]] = None
    max_consecutive_auto_reply: int = 10
    human_input_mode: str = "NEVER"
    code_execution_config: Optional[Dict[str, Any]] = None
    system_message: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    custom_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "name": self.name,
            "description": self.description,
            "llm_config": self.llm_config,
            "max_consecutive_auto_reply": self.max_consecutive_auto_reply,
            "human_input_mode": self.human_input_mode,
            "code_execution_config": self.code_execution_config,
            "system_message": self.system_message,
            "capabilities": self.capabilities,
            "dependencies": self.dependencies,
            "custom_config": self.custom_config,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """从字典创建配置对象"""
        config = cls(
            agent_id=data["agent_id"],
            agent_type=AgentType(data["agent_type"]),
            name=data["name"],
            description=data.get("description", ""),
            llm_config=data.get("llm_config"),
            max_consecutive_auto_reply=data.get("max_consecutive_auto_reply", 10),
            human_input_mode=data.get("human_input_mode", "NEVER"),
            code_execution_config=data.get("code_execution_config"),
            system_message=data.get("system_message"),
            capabilities=data.get("capabilities", []),
            dependencies=data.get("dependencies", []),
            custom_config=data.get("custom_config", {}),
        )
        return config


@dataclass
class AgentCapability:
    """Agent能力描述"""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    title: str
    description: str
    assignee: str
    status: str = "pending"
    priority: Priority = Priority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class CollaborationContext:
    """协作上下文"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scenario: str = ""
    participants: List[str] = field(default_factory=list)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    current_phase: str = "initialization"
    history: List[AgentMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)