"""Message Bus for SAFE Agent System

This module provides the message bus implementation for agent communication.
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from collections import defaultdict, deque
from .protocols import MessageEnvelope, TransportType, CommunicationProtocol
from ..base.types import AgentMessage


class MessageQueue:
    """消息队列"""

    def __init__(self, max_size: int = 1000):
        """初始化消息队列

        Args:
            max_size: 最大队列大小
        """
        self.max_size = max_size
        self._queue = deque(maxlen=max_size)
        self._lock = asyncio.Lock()

    async def put(self, envelope: MessageEnvelope) -> bool:
        """添加消息到队列

        Args:
            envelope: 消息信封

        Returns:
            是否添加成功
        """
        try:
            async with self._lock:
                self._queue.append(envelope)
                return True
        except Exception:
            return False

    async def get(self) -> Optional[MessageEnvelope]:
        """从队列获取消息

        Returns:
            消息信封或None
        """
        try:
            async with self._lock:
                if self._queue:
                    return self._queue.popleft()
                return None
        except Exception:
            return None

    async def size(self) -> int:
        """获取队列大小

        Returns:
            队列大小
        """
        async with self._lock:
            return len(self._queue)

    async def clear(self) -> None:
        """清空队列"""
        async with self._lock:
            self._queue.clear()


class MessageRouter:
    """消息路由器"""

    def __init__(self):
        """初始化消息路由器"""
        self.routes: Dict[str, Set[str]] = defaultdict(set)  # destination -> agents
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # topic -> agents
        self.logger = logging.getLogger("MessageRouter")

    def add_route(self, destination: str, agent_id: str) -> None:
        """添加路由

        Args:
            destination: 目标地址
            agent_id: Agent ID
        """
        self.routes[destination].add(agent_id)
        self.logger.info(f"Added route: {destination} -> {agent_id}")

    def remove_route(self, destination: str, agent_id: str) -> None:
        """移除路由

        Args:
            destination: 目标地址
            agent_id: Agent ID
        """
        if destination in self.routes:
            self.routes[destination].discard(agent_id)
            if not self.routes[destination]:
                del self.routes[destination]
        self.logger.info(f"Removed route: {destination} -> {agent_id}")

    def subscribe(self, topic: str, agent_id: str) -> None:
        """订阅主题

        Args:
            topic: 主题
            agent_id: Agent ID
        """
        self.subscriptions[topic].add(agent_id)
        self.logger.info(f"Agent {agent_id} subscribed to topic: {topic}")

    def unsubscribe(self, topic: str, agent_id: str) -> None:
        """取消订阅

        Args:
            topic: 主题
            agent_id: Agent ID
        """
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(agent_id)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        self.logger.info(f"Agent {agent_id} unsubscribed from topic: {topic}")

    def route_message(self, envelope: MessageEnvelope) -> List[str]:
        """路由消息

        Args:
            envelope: 消息信封

        Returns:
            目标Agent ID列表
        """
        destinations = []

        # 直接路由
        direct_routes = self.routes.get(envelope.destination, set())
        destinations.extend(direct_routes)

        # 主题路由
        if envelope.message.content.get("topic"):
            topic = envelope.message.content["topic"]
            topic_subscribers = self.subscriptions.get(topic, set())
            destinations.extend(topic_subscribers)

        # 广播路由
        if envelope.destination == "broadcast":
            from ..registry import get_registry
            registry = get_registry()
            all_agents = [agent.get_agent_id() for agent in registry.get_all_agents()]
            destinations.extend(all_agents)

        # 去重并排除发送者
        destinations = list(set(destinations) - {envelope.source})

        return destinations


class MessageBus:
    """消息总线"""

    def __init__(self):
        """初始化消息总线"""
        self.router = MessageRouter()
        self.queues: Dict[str, MessageQueue] = {}
        self.handlers: Dict[str, Callable] = {}
        self.delivered_messages: Set[str] = set()
        self.failed_messages: List[MessageEnvelope] = []
        self.message_history: List[MessageEnvelope] = []
        self.max_history_size = 10000
        self.running = False
        self.logger = logging.getLogger("MessageBus")

    async def start(self) -> None:
        """启动消息总线"""
        if self.running:
            return

        self.running = True
        self.logger.info("Message bus started")

        # 启动消息处理任务
        asyncio.create_task(self._process_messages())
        asyncio.create_task(self._cleanup_expired_messages())
        asyncio.create_task(self._retry_failed_messages())

    async def stop(self) -> None:
        """停止消息总线"""
        self.running = False
        self.logger.info("Message bus stopped")

    async def send(self, envelope: MessageEnvelope) -> bool:
        """发送消息

        Args:
            envelope: 消息信封

        Returns:
            是否发送成功
        """
        try:
            # 检查重复消息
            if envelope.message.message_id in self.delivered_messages:
                self.logger.warning(f"Duplicate message: {envelope.message.message_id}")
                return True

            # 路由消息
            destinations = self.router.route_message(envelope)

            if not destinations:
                self.logger.warning(f"No route for message: {envelope.message.message_id}")
                return False

            # 发送到每个目标
            success_count = 0
            for destination in destinations:
                if await self._send_to_agent(envelope, destination):
                    success_count += 1

            # 记录消息历史
            self._record_message(envelope)

            # 如果全部发送成功
            if success_count == len(destinations):
                self.delivered_messages.add(envelope.message.message_id)
                self.logger.info(f"Message delivered to {success_count}/{len(destinations)} agents")
                return True
            else:
                self.logger.warning(f"Message partially delivered: {success_count}/{len(destinations)}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self.failed_messages.append(envelope)
            return False

    async def _send_to_agent(self, envelope: MessageEnvelope, agent_id: str) -> bool:
        """发送消息到特定Agent

        Args:
            envelope: 消息信封
            agent_id: Agent ID

        Returns:
            是否发送成功
        """
        try:
            # 获取或创建Agent队列
            if agent_id not in self.queues:
                self.queues[agent_id] = MessageQueue()

            # 克隆信封并设置目标
            agent_envelope = MessageEnvelope(
                protocol=envelope.protocol,
                transport=envelope.transport,
                destination=agent_id,
                source=envelope.source,
                message=envelope.message,
                headers=envelope.headers.copy(),
                timestamp=envelope.timestamp,
                expires_at=envelope.expires_at,
                retry_count=envelope.retry_count,
                max_retries=envelope.max_retries
            )

            # 添加到队列
            return await self.queues[agent_id].put(agent_envelope)

        except Exception as e:
            self.logger.error(f"Failed to send to agent {agent_id}: {e}")
            return False

    async def receive(self, agent_id: str) -> Optional[MessageEnvelope]:
        """接收消息

        Args:
            agent_id: Agent ID

        Returns:
            消息信封或None
        """
        try:
            if agent_id not in self.queues:
                return None

            return await self.queues[agent_id].get()

        except Exception as e:
            self.logger.error(f"Failed to receive message for {agent_id}: {e}")
            return None

    def register_handler(self, agent_id: str, handler: Callable) -> None:
        """注册消息处理器

        Args:
            agent_id: Agent ID
            handler: 处理函数
        """
        self.handlers[agent_id] = handler
        self.logger.info(f"Registered handler for agent: {agent_id}")

    def unregister_handler(self, agent_id: str) -> None:
        """注销消息处理器

        Args:
            agent_id: Agent ID
        """
        if agent_id in self.handlers:
            del self.handlers[agent_id]
            self.logger.info(f"Unregistered handler for agent: {agent_id}")

    async def _process_messages(self) -> None:
        """处理消息的后台任务"""
        while self.running:
            try:
                # 处理每个Agent的队列
                for agent_id, queue in list(self.queues.items()):
                    if agent_id in self.handlers:
                        try:
                            envelope = await queue.get()
                            if envelope:
                                # 调用处理器
                                handler = self.handlers[agent_id]
                                await handler(envelope)
                        except Exception as e:
                            self.logger.error(f"Error processing message for {agent_id}: {e}")

                await asyncio.sleep(0.01)  # 10ms间隔

            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(1)

    async def _cleanup_expired_messages(self) -> None:
        """清理过期消息的后台任务"""
        while self.running:
            try:
                now = datetime.now()
                expired_messages = []

                # 检查各队列中的过期消息
                for agent_id, queue in self.queues.items():
                    # 这里需要更复杂的逻辑来检查队列中的过期消息
                    # 简化实现：定期清理
                    if await queue.size() > 500:  # 队列过大时清理
                        await queue.clear()

                # 清理历史记录
                if len(self.message_history) > self.max_history_size:
                    self.message_history = self.message_history[-self.max_history_size//2:]

                await asyncio.sleep(300)  # 5分钟清理一次

            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    async def _retry_failed_messages(self) -> None:
        """重试失败消息的后台任务"""
        while self.running:
            try:
                if self.failed_messages:
                    retry_messages = []
                    for envelope in self.failed_messages:
                        if envelope.should_retry():
                            envelope.retry_count += 1
                            success = await self.send(envelope)
                            if not success:
                                retry_messages.append(envelope)
                        # 如果不应该重试，直接丢弃

                    self.failed_messages = retry_messages

                await asyncio.sleep(60)  # 1分钟重试一次

            except Exception as e:
                self.logger.error(f"Error in retry loop: {e}")
                await asyncio.sleep(60)

    def _record_message(self, envelope: MessageEnvelope) -> None:
        """记录消息历史

        Args:
            envelope: 消息信封
        """
        self.message_history.append(envelope)

        # 限制历史记录大小
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size//2:]

    def get_stats(self) -> Dict[str, Any]:
        """获取消息总线统计信息

        Returns:
            统计信息
        """
        return {
            "running": self.running,
            "total_delivered": len(self.delivered_messages),
            "total_failed": len(self.failed_messages),
            "total_history": len(self.message_history),
            "active_queues": len(self.queues),
            "queue_sizes": {aid: asyncio.run(q.size()) for aid, q in self.queues.items()},
            "registered_handlers": len(self.handlers),
            "routes_count": len(self.router.routes),
            "subscriptions_count": len(self.router.subscriptions)
        }

    async def clear_all(self) -> None:
        """清空所有消息和队列"""
        for queue in self.queues.values():
            await queue.clear()
        self.delivered_messages.clear()
        self.failed_messages.clear()
        self.message_history.clear()
        self.logger.info("Message bus cleared")


# 全局消息总线实例
global_message_bus = MessageBus()


def get_message_bus() -> MessageBus:
    """获取全局消息总线实例"""
    return global_message_bus


async def start_message_bus() -> None:
    """启动全局消息总线"""
    await global_message_bus.start()


async def stop_message_bus() -> None:
    """停止全局消息总线"""
    await global_message_bus.stop()