"""Communication Protocols for SAFE Agent System

This module defines communication protocols and message handling
for agents in the SAFE system.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
from ..base.types import AgentMessage, MessageType, Priority, AgentType


class CommunicationProtocol(Enum):
    """通信协议类型"""
    AUTOGEN_CHAT = "autogen_chat"      # AutoGen聊天协议
    SAFE_MESSAGING = "safe_messaging"  # SAFE消息协议
    REST_API = "rest_api"             # REST API协议
    WEBSOCKET = "websocket"           # WebSocket协议
    REDIS_PUBSUB = "redis_pubsub"     # Redis发布订阅协议
    MEMORY_BUS = "memory_bus"         # 内存总线协议


class TransportType(Enum):
    """传输类型"""
    IN_MEMORY = "in_memory"           # 内存传输
    HTTP = "http"                     # HTTP传输
    WEBSOCKET = "websocket"           # WebSocket传输
    REDIS = "redis"                   # Redis传输
    AMQP = "amqp"                     # AMQP传输
    KAFKA = "kafka"                   # Kafka传输


@dataclass
class MessageEnvelope:
    """消息信封"""
    protocol: CommunicationProtocol
    transport: TransportType
    destination: str
    source: str
    message: AgentMessage
    headers: Dict[str, Any]
    timestamp: datetime
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['message'] = self.message.to_dict()
        data['timestamp'] = self.timestamp.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageEnvelope":
        """从字典创建"""
        envelope = cls(
            protocol=CommunicationProtocol(data['protocol']),
            transport=TransportType(data['transport']),
            destination=data['destination'],
            source=data['source'],
            message=AgentMessage.from_dict(data['message']),
            headers=data['headers'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )
        return envelope

    def is_expired(self) -> bool:
        """检查是否过期"""
        return self.expires_at is not None and datetime.now() > self.expires_at

    def should_retry(self) -> bool:
        """检查是否应该重试"""
        return self.retry_count < self.max_retries


class MessageHandler:
    """消息处理器"""

    def __init__(self, agent_id: str):
        """初始化消息处理器

        Args:
            agent_id: Agent ID
        """
        self.agent_id = agent_id
        self.handlers: Dict[MessageType, List[Callable]] = {}
        self.logger = logging.getLogger(f"MessageHandler.{agent_id}")

    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """注册消息处理器

        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        if message_type not in self.handlers:
            self.handlers[message_type] = []
        self.handlers[message_type].append(handler)
        self.logger.info(f"Registered handler for {message_type.value}")

    def unregister_handler(self, message_type: MessageType, handler: Callable) -> None:
        """注销消息处理器

        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        if message_type in self.handlers:
            try:
                self.handlers[message_type].remove(handler)
                self.logger.info(f"Unregistered handler for {message_type.value}")
            except ValueError:
                self.logger.warning(f"Handler not found for {message_type.value}")

    async def handle_message(self, message: AgentMessage) -> Dict[str, Any]:
        """处理消息

        Args:
            message: 接收到的消息

        Returns:
            处理结果
        """
        try:
            self.logger.info(f"Handling {message.message_type.value} message from {message.sender_id}")

            # 获取对应的处理器
            handlers = self.handlers.get(message.message_type, [])

            if not handlers:
                self.logger.warning(f"No handlers for message type {message.message_type.value}")
                return {"status": "no_handler", "message": "No handler found"}

            # 并行执行所有处理器
            results = []
            for handler in handlers:
                try:
                    result = await handler(message)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Handler error: {e}")
                    results.append({"status": "error", "error": str(e)})

            return {
                "status": "success",
                "results": results,
                "message_id": message.message_id
            }

        except Exception as e:
            self.logger.error(f"Failed to handle message: {e}")
            return {"status": "error", "error": str(e)}


class SafeMessagingProtocol:
    """SAFE消息协议实现"""

    def __init__(self, agent_id: str, message_bus):
        """初始化SAFE消息协议

        Args:
            agent_id: Agent ID
            message_bus: 消息总线实例
        """
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.message_handler = MessageHandler(agent_id)
        self.logger = logging.getLogger(f"SafeMessagingProtocol.{agent_id}")

    async def send_message(
        self,
        recipient_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
        protocol: CommunicationProtocol = CommunicationProtocol.SAFE_MESSAGING,
        transport: TransportType = TransportType.IN_MEMORY,
        **kwargs
    ) -> bool:
        """发送消息

        Args:
            recipient_id: 接收者ID
            message_type: 消息类型
            content: 消息内容
            priority: 优先级
            protocol: 通信协议
            transport: 传输类型
            **kwargs: 其他参数

        Returns:
            是否发送成功
        """
        try:
            # 创建消息
            message = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=recipient_id,
                message_type=message_type,
                priority=priority,
                content=content,
                **kwargs
            )

            # 创建信封
            envelope = MessageEnvelope(
                protocol=protocol,
                transport=transport,
                destination=recipient_id,
                source=self.agent_id,
                message=message,
                headers={"content_type": "application/json"},
                timestamp=datetime.now(),
                **kwargs
            )

            # 发送消息
            success = await self.message_bus.send(envelope)

            if success:
                self.logger.info(f"Message sent to {recipient_id}: {message.message_id}")
            else:
                self.logger.error(f"Failed to send message to {recipient_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False

    async def broadcast_message(
        self,
        message_type: MessageType,
        content: Dict[str, Any],
        recipients: Optional[List[str]] = None,
        agent_types: Optional[List[AgentType]] = None,
        priority: Priority = Priority.NORMAL,
        **kwargs
    ) -> int:
        """广播消息

        Args:
            message_type: 消息类型
            content: 消息内容
            recipients: 接收者列表（None表示所有Agent）
            agent_types: Agent类型过滤
            priority: 优先级
            **kwargs: 其他参数

        Returns:
            成功发送的数量
        """
        try:
            sent_count = 0

            # 确定接收者
            if recipients:
                target_agents = recipients
            elif agent_types:
                # 根据Agent类型获取接收者
                from ..registry import get_registry
                registry = get_registry()
                target_agents = []
                for agent_type in agent_types:
                    agents = registry.get_agents_by_type(agent_type)
                    target_agents.extend([agent.get_agent_id() for agent in agents])
            else:
                # 广播给所有Agent
                from ..registry import get_registry
                registry = get_registry()
                target_agents = [agent.get_agent_id() for agent in registry.get_all_agents()]

            # 排除自己
            target_agents = [aid for aid in target_agents if aid != self.agent_id]

            # 发送给每个接收者
            for recipient_id in target_agents:
                success = await self.send_message(
                    recipient_id=recipient_id,
                    message_type=message_type,
                    content=content,
                    priority=priority,
                    **kwargs
                )
                if success:
                    sent_count += 1

            self.logger.info(f"Broadcast sent to {sent_count}/{len(target_agents)} agents")
            return sent_count

        except Exception as e:
            self.logger.error(f"Error broadcasting message: {e}")
            return 0

    async def reply_to_message(
        self,
        original_message: AgentMessage,
        content: Dict[str, Any],
        **kwargs
    ) -> bool:
        """回复消息

        Args:
            original_message: 原始消息
            content: 回复内容
            **kwargs: 其他参数

        Returns:
            是否回复成功
        """
        return await self.send_message(
            recipient_id=original_message.sender_id,
            message_type=MessageType.RESPONSE,
            content=content,
            correlation_id=original_message.message_id,
            reply_to=original_message.message_id,
            **kwargs
        )

    def register_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """注册消息处理器

        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        self.message_handler.register_handler(message_type, handler)

    def unregister_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """注销消息处理器

        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        self.message_handler.unregister_handler(message_type, handler)

    async def receive_message(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """接收消息

        Args:
            envelope: 消息信封

        Returns:
            处理结果
        """
        try:
            # 检查是否过期
            if envelope.is_expired():
                self.logger.warning(f"Received expired message: {envelope.message.message_id}")
                return {"status": "expired", "message": "Message expired"}

            # 检查接收者
            if envelope.destination != self.agent_id and envelope.destination != "broadcast":
                self.logger.warning(f"Message not for this agent: {self.agent_id}")
                return {"status": "wrong_recipient", "message": "Message not for this agent"}

            # 处理消息
            result = await self.message_handler.handle_message(envelope.message)

            self.logger.info(f"Message processed: {envelope.message.message_id}")
            return result

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return {"status": "error", "error": str(e)}


class AutogenChatProtocol:
    """AutoGen聊天协议适配器"""

    def __init__(self, agent_id: str, autogen_agent):
        """初始化AutoGen聊天协议

        Args:
            agent_id: Agent ID
            autogen_agent: AutoGen Agent实例
        """
        self.agent_id = agent_id
        self.autogen_agent = autogen_agent
        self.logger = logging.getLogger(f"AutogenChatProtocol.{agent_id}")

    async def send_chat_message(self, message: str, recipient_id: str) -> bool:
        """发送聊天消息

        Args:
            message: 消息内容
            recipient_id: 接收者ID

        Returns:
            是否发送成功
        """
        try:
            # 通过AutoGen发送消息
            # 这里需要根据AutoGen的具体API来实现
            self.logger.info(f"Sending chat message to {recipient_id}: {message[:50]}...")

            # 实际的AutoGen消息发送逻辑
            # await self.autogen_agent.send_message(recipient_id, message)

            return True

        except Exception as e:
            self.logger.error(f"Failed to send chat message: {e}")
            return False

    async def receive_chat_message(self, sender_id: str, message: str) -> None:
        """接收聊天消息

        Args:
            sender_id: 发送者ID
            message: 消息内容
        """
        try:
            self.logger.info(f"Received chat message from {sender_id}: {message[:50]}...")

            # 处理接收到的消息
            # 实际的AutoGen消息处理逻辑

        except Exception as e:
            self.logger.error(f"Failed to process chat message: {e}")


class ProtocolManager:
    """协议管理器，负责管理多种通信协议"""

    def __init__(self, agent_id: str):
        """初始化协议管理器

        Args:
            agent_id: Agent ID
        """
        self.agent_id = agent_id
        self.protocols: Dict[CommunicationProtocol, Any] = {}
        self.active_protocol = CommunicationProtocol.SAFE_MESSAGING
        self.logger = logging.getLogger(f"ProtocolManager.{agent_id}")

    def register_protocol(self, protocol: CommunicationProtocol, implementation) -> None:
        """注册协议实现

        Args:
            protocol: 协议类型
            implementation: 协议实现
        """
        self.protocols[protocol] = implementation
        self.logger.info(f"Registered protocol: {protocol.value}")

    def set_active_protocol(self, protocol: CommunicationProtocol) -> bool:
        """设置活动协议

        Args:
            protocol: 协议类型

        Returns:
            是否设置成功
        """
        if protocol in self.protocols:
            self.active_protocol = protocol
            self.logger.info(f"Active protocol set to: {protocol.value}")
            return True
        else:
            self.logger.error(f"Protocol not registered: {protocol.value}")
            return False

    async def send_message(self, **kwargs) -> bool:
        """通过活动协议发送消息

        Args:
            **kwargs: 消息参数

        Returns:
            是否发送成功
        """
        try:
            protocol_impl = self.protocols.get(self.active_protocol)
            if not protocol_impl:
                self.logger.error(f"No active protocol implementation")
                return False

            # 根据协议类型调用相应的方法
            if self.active_protocol == CommunicationProtocol.SAFE_MESSAGING:
                return await protocol_impl.send_message(**kwargs)
            elif self.active_protocol == CommunicationProtocol.AUTOGEN_CHAT:
                return await protocol_impl.send_chat_message(**kwargs)
            else:
                self.logger.error(f"Unsupported protocol: {self.active_protocol.value}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False

    def get_protocol_stats(self) -> Dict[str, Any]:
        """获取协议统计信息

        Returns:
            协议统计信息
        """
        return {
            "active_protocol": self.active_protocol.value,
            "registered_protocols": list(self.protocols.keys()),
            "total_protocols": len(self.protocols)
        }