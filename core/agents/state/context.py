"""Context Management for SAFE Agent System

This module provides context and session management for agents.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict
from ..base.types import AgentMessage, MessageType


@dataclass
class ContextData:
    """上下文数据项"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """检查是否过期"""
        return self.expires_at is not None and datetime.now() > self.expires_at

    def access(self) -> Any:
        """访问数据"""
        self.access_count += 1
        self.updated_at = datetime.now()
        return self.value

    def update(self, value: Any, expires_at: Optional[datetime] = None) -> None:
        """更新数据"""
        self.value = value
        self.updated_at = datetime.now()
        if expires_at:
            self.expires_at = expires_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextData":
        """从字典创建"""
        item = cls(
            key=data['key'],
            value=data['value'],
            access_count=data.get('access_count', 0),
            metadata=data.get('metadata', {})
        )
        item.created_at = datetime.fromisoformat(data['created_at'])
        item.updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('expires_at'):
            item.expires_at = datetime.fromisoformat(data['expires_at'])
        return item


class Context:
    """Agent上下文管理器"""

    def __init__(self, context_id: str = None):
        """初始化上下文

        Args:
            context_id: 上下文ID，不提供则自动生成
        """
        self.context_id = context_id or str(uuid.uuid4())
        self.data: Dict[str, ContextData] = {}
        self.shared_data: Dict[str, Any] = {}  # 共享数据，不被ContextData管理
        self.parent_context: Optional[Context] = None
        self.child_contexts: Set[str] = set()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.access_count = 0
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(f"Context.{self.context_id}")

    async def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据

        Args:
            key: 数据键
            default: 默认值

        Returns:
            数据值或默认值
        """
        async with self.lock:
            self.access_count += 1

            # 检查当前上下文
            if key in self.data:
                item = self.data[key]
                if not item.is_expired():
                    return item.access()
                else:
                    # 过期数据，清理
                    del self.data[key]
                    self.logger.debug(f"Expired context data removed: {key}")

            # 检查父上下文
            if self.parent_context:
                return await self.parent_context.get(key, default)

            return default

    async def set(self, key: str, value: Any, expires_in: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """设置上下文数据

        Args:
            key: 数据键
            value: 数据值
            expires_in: 过期时间（秒）
            metadata: 元数据
        """
        async with self.lock:
            expires_at = None
            if expires_in:
                expires_at = datetime.now() + timedelta(seconds=expires_in)

            if key in self.data:
                self.data[key].update(value, expires_at)
                if metadata:
                    self.data[key].metadata.update(metadata)
            else:
                self.data[key] = ContextData(
                    key=key,
                    value=value,
                    expires_at=expires_at,
                    metadata=metadata or {}
                )

            self.updated_at = datetime.now()
            self.logger.debug(f"Context data set: {key}")

    async def delete(self, key: str) -> bool:
        """删除上下文数据

        Args:
            key: 数据键

        Returns:
            是否删除成功
        """
        async with self.lock:
            if key in self.data:
                del self.data[key]
                self.updated_at = datetime.now()
                self.logger.debug(f"Context data deleted: {key}")
                return True
            return False

    async def exists(self, key: str) -> bool:
        """检查数据是否存在

        Args:
            key: 数据键

        Returns:
            是否存在
        """
        async with self.lock:
            if key in self.data and not self.data[key].is_expired():
                return True

            if self.parent_context:
                return await self.parent_context.exists(key)

            return False

    async def get_keys(self, include_expired: bool = False) -> List[str]:
        """获取所有数据键

        Args:
            include_expired: 是否包含过期的键

        Returns:
            数据键列表
        """
        async with self.lock:
            keys = []
            for key, item in self.data.items():
                if include_expired or not item.is_expired():
                    keys.append(key)

            # 包含父上下文的键
            if self.parent_context:
                parent_keys = await self.parent_context.get_keys(include_expired)
                # 去重
                keys.extend([k for k in parent_keys if k not in keys])

            return keys

    async def clear(self) -> None:
        """清空所有数据"""
        async with self.lock:
            self.data.clear()
            self.shared_data.clear()
            self.updated_at = datetime.now()
            self.logger.debug("Context cleared")

    async def cleanup_expired(self) -> int:
        """清理过期数据

        Returns:
            清理的项目数量
        """
        async with self.lock:
            expired_keys = [key for key, item in self.data.items() if item.is_expired()]
            for key in expired_keys:
                del self.data[key]

            if expired_keys:
                self.updated_at = datetime.now()
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired context items")

            return len(expired_keys)

    # 共享数据方法（不会被自动清理）
    async def get_shared(self, key: str, default: Any = None) -> Any:
        """获取共享数据"""
        async with self.lock:
            self.access_count += 1
            return self.shared_data.get(key, default)

    async def set_shared(self, key: str, value: Any) -> None:
        """设置共享数据"""
        async with self.lock:
            self.shared_data[key] = value
            self.updated_at = datetime.now()
            self.logger.debug(f"Shared data set: {key}")

    async def create_child_context(self) -> "Context":
        """创建子上下文"""
        child_context = Context()
        child_context.parent_context = self
        self.child_contexts.add(child_context.context_id)
        self.logger.debug(f"Created child context: {child_context.context_id}")
        return child_context

    def get_context_info(self) -> Dict[str, Any]:
        """获取上下文信息"""
        return {
            "context_id": self.context_id,
            "data_count": len(self.data),
            "shared_data_count": len(self.shared_data),
            "child_contexts_count": len(self.child_contexts),
            "has_parent": self.parent_context is not None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "context_id": self.context_id,
            "data": {k: v.to_dict() for k, v in self.data.items()},
            "shared_data": self.shared_data,
            "parent_context_id": self.parent_context.context_id if self.parent_context else None,
            "child_contexts": list(self.child_contexts),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count
        }


class Session:
    """Agent会话管理器"""

    def __init__(self, session_id: str = None, timeout_minutes: int = 60):
        """初始化会话

        Args:
            session_id: 会话ID，不提供则自动生成
            timeout_minutes: 会话超时时间（分钟）
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.contexts: Dict[str, Context] = {}
        self.global_context = Context(f"{self.session_id}_global")
        self.timeout_minutes = timeout_minutes
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.active = True
        self.participants: Set[str] = set()
        self.messages: List[AgentMessage] = []
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(f"Session.{self.session_id}")

    async def create_context(self, context_id: str = None) -> Context:
        """创建上下文

        Args:
            context_id: 上下文ID

        Returns:
            上下文实例
        """
        async with self.lock:
            context = Context(context_id)
            self.contexts[context.context_id] = context
            await self._update_activity()
            self.logger.debug(f"Created context: {context.context_id}")
            return context

    async def get_context(self, context_id: str) -> Optional[Context]:
        """获取上下文

        Args:
            context_id: 上下文ID

        Returns:
            上下文实例或None
        """
        async with self.lock:
            await self._update_activity()
            return self.contexts.get(context_id)

    async def remove_context(self, context_id: str) -> bool:
        """移除上下文

        Args:
            context_id: 上下文ID

        Returns:
            是否移除成功
        """
        async with self.lock:
            if context_id in self.contexts:
                del self.contexts[context_id]
                await self._update_activity()
                self.logger.debug(f"Removed context: {context_id}")
                return True
            return False

    async def add_participant(self, agent_id: str) -> None:
        """添加参与者

        Args:
            agent_id: Agent ID
        """
        async with self.lock:
            self.participants.add(agent_id)
            await self._update_activity()

    async def remove_participant(self, agent_id: str) -> None:
        """移除参与者

        Args:
            agent_id: Agent ID
        """
        async with self.lock:
            self.participants.discard(agent_id)
            await self._update_activity()

    async def add_message(self, message: AgentMessage) -> None:
        """添加消息到会话

        Args:
            message: 消息
        """
        async with self.lock:
            self.messages.append(message)
            await self._update_activity()

    async def get_messages(self, limit: int = 100, agent_id: Optional[str] = None) -> List[AgentMessage]:
        """获取会话消息

        Args:
            limit: 限制数量
            agent_id: 特定Agent的消息

        Returns:
            消息列表
        """
        async with self.lock:
            messages = self.messages

            if agent_id:
                messages = [msg for msg in messages if msg.sender_id == agent_id or msg.receiver_id == agent_id]

            # 返回最新的消息
            return messages[-limit:] if len(messages) > limit else messages

    async def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now() > self.last_activity + timedelta(minutes=self.timeout_minutes)

    async def cleanup_expired_contexts(self) -> int:
        """清理过期的上下文

        Returns:
            清理的上下文数量
        """
        async with self.lock:
            expired_contexts = []
            for context_id, context in self.contexts.items():
                if await context.cleanup_expired() > 0:
                    expired_contexts.append(context_id)

            await self._update_activity()
            return len(expired_contexts)

    async def _update_activity(self) -> None:
        """更新活动时间"""
        self.last_activity = datetime.now()

    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        return {
            "session_id": self.session_id,
            "contexts_count": len(self.contexts),
            "participants_count": len(self.participants),
            "messages_count": len(self.messages),
            "active": self.active,
            "timeout_minutes": self.timeout_minutes,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "participants": list(self.participants)
        }

    async def close(self) -> None:
        """关闭会话"""
        async with self.lock:
            self.active = False
            self.contexts.clear()
            self.participants.clear()
            self.logger.info(f"Session {self.session_id} closed")


class SessionManager:
    """会话管理器"""

    def __init__(self):
        """初始化会话管理器"""
        self.sessions: Dict[str, Session] = {}
        self.default_timeout = 60  # 默认超时时间（分钟）
        self.cleanup_interval = 300  # 清理间隔（秒）
        self.running = False
        self.cleanup_task = None
        self.logger = logging.getLogger("SessionManager")

    async def start(self) -> None:
        """启动会话管理器"""
        if self.running:
            return

        self.running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Session manager started")

    async def stop(self) -> None:
        """停止会话管理器"""
        self.running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        # 关闭所有会话
        for session in self.sessions.values():
            await session.close()

        self.logger.info("Session manager stopped")

    async def create_session(self, session_id: str = None, timeout_minutes: int = None) -> Session:
        """创建会话

        Args:
            session_id: 会话ID
            timeout_minutes: 超时时间

        Returns:
            会话实例
        """
        session = Session(
            session_id=session_id,
            timeout_minutes=timeout_minutes or self.default_timeout
        )
        self.sessions[session.session_id] = session
        self.logger.info(f"Created session: {session.session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话

        Args:
            session_id: 会话ID

        Returns:
            会话实例或None
        """
        session = self.sessions.get(session_id)
        if session and not await session.is_expired():
            return session
        elif session and await session.is_expired():
            # 清理过期会话
            await self.remove_session(session_id)
            return None
        return None

    async def remove_session(self, session_id: str) -> bool:
        """移除会话

        Args:
            session_id: 会话ID

        Returns:
            是否移除成功
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            await session.close()
            del self.sessions[session_id]
            self.logger.info(f"Removed session: {session_id}")
            return True
        return False

    async def cleanup_expired_sessions(self) -> int:
        """清理过期会话

        Returns:
            清理的会话数量
        """
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if await session.is_expired():
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self.remove_session(session_id)

        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while self.running:
            try:
                await self.cleanup_expired_sessions()

                # 清理会话中的过期上下文
                for session in self.sessions.values():
                    await session.cleanup_expired_contexts()

                await asyncio.sleep(self.cleanup_interval)

            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        return {
            "total_sessions": len(self.sessions),
            "default_timeout": self.default_timeout,
            "cleanup_interval": self.cleanup_interval,
            "running": self.running,
            "session_ids": list(self.sessions.keys())
        }


# 全局会话管理器实例
global_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """获取全局会话管理器"""
    return global_session_manager


async def start_session_manager() -> None:
    """启动全局会话管理器"""
    await global_session_manager.start()


async def stop_session_manager() -> None:
    """停止全局会话管理器"""
    await global_session_manager.stop()