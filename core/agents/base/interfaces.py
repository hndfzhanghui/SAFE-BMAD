"""Base Interfaces for SAFE Agent Framework

This module defines the core interfaces that agents must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from .types import (
    AgentMessage, MessageType, AgentConfig, AgentCapability,
    TaskInfo, CollaborationContext, AgentStatus
)


class IAgent(ABC):
    """Agent基础接口"""

    @abstractmethod
    def get_agent_id(self) -> str:
        """获取Agent ID"""
        pass

    @abstractmethod
    def get_agent_type(self) -> str:
        """获取Agent类型"""
        pass

    @abstractmethod
    def get_status(self) -> AgentStatus:
        """获取Agent状态"""
        pass

    @abstractmethod
    async def initialize(self, config: AgentConfig) -> bool:
        """初始化Agent"""
        pass

    @abstractmethod
    async def start(self) -> bool:
        """启动Agent"""
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """停止Agent"""
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """清理资源"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """获取Agent能力列表"""
        pass


class ICommunicator(ABC):
    """通信接口"""

    @abstractmethod
    async def send_message(self, message: AgentMessage) -> bool:
        """发送消息"""
        pass

    @abstractmethod
    async def receive_message(self) -> Optional[AgentMessage]:
        """接收消息"""
        pass

    @abstractmethod
    async def broadcast_message(self, message: AgentMessage) -> bool:
        """广播消息"""
        pass

    @abstractmethod
    def register_handler(self, message_type: MessageType, handler) -> None:
        """注册消息处理器"""
        pass

    @abstractmethod
    def unregister_handler(self, message_type: MessageType) -> None:
        """注销消息处理器"""
        pass


class IAnalyzer(ABC):
    """分析接口"""

    @abstractmethod
    async def analyze(self, data: Dict[str, Any], context: Optional[CollaborationContext] = None) -> Dict[str, Any]:
        """分析数据"""
        pass

    @abstractmethod
    def get_analysis_schema(self) -> Dict[str, Any]:
        """获取分析模式"""
        pass


class IConfigurable(ABC):
    """配置接口"""

    @abstractmethod
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """更新配置"""
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        pass


class IStateManager(ABC):
    """状态管理接口"""

    @abstractmethod
    async def update_state(self, status: AgentStatus, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新状态"""
        pass

    @abstractmethod
    def get_current_state(self) -> AgentStatus:
        """获取当前状态"""
        pass

    @abstractmethod
    def get_state_history(self) -> List[Dict[str, Any]]:
        """获取状态历史"""
        pass


class ICollaborator(ABC):
    """协作接口"""

    @abstractmethod
    async def join_collaboration(self, context: CollaborationContext) -> bool:
        """加入协作"""
        pass

    @abstractmethod
    async def leave_collaboration(self, session_id: str) -> bool:
        """离开协作"""
        pass

    @abstractmethod
    async def coordinate_with(self, agent_id: str, task: TaskInfo) -> bool:
        """与其他Agent协调"""
        pass

    @abstractmethod
    def get_current_collaborations(self) -> List[str]:
        """获取当前参与的协作"""
        pass


class IMonitorable(ABC):
    """监控接口"""

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        pass

    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        pass

    @abstractmethod
    async def self_diagnose(self) -> Dict[str, Any]:
        """自我诊断"""
        pass


class ITaskHandler(ABC):
    """任务处理接口"""

    @abstractmethod
    async def assign_task(self, task: TaskInfo) -> bool:
        """分配任务"""
        pass

    @abstractmethod
    async def execute_task(self, task: TaskInfo) -> Dict[str, Any]:
        """执行任务"""
        pass

    @abstractmethod
    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务状态"""
        pass

    @abstractmethod
    def get_pending_tasks(self) -> List[TaskInfo]:
        """获取待处理任务"""
        pass


class IDiscoverable(ABC):
    """服务发现接口"""

    @abstractmethod
    def register_service(self) -> bool:
        """注册服务"""
        pass

    @abstractmethod
    def unregister_service(self) -> bool:
        """注销服务"""
        pass

    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


# 复合接口，继承多个基础接口
class ISafeAgent(IAgent, ICommunicator, IAnalyzer, IConfigurable,
                IStateManager, ICollaborator, IMonitorable, ITaskHandler, IDiscoverable):
    """SAFE Agent复合接口，包含所有必需的接口"""

    pass