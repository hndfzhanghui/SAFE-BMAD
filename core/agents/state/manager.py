"""State Manager for SAFE Agent System

This module provides comprehensive state management for agents.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from ..base.types import AgentStatus, AgentType, TaskInfo, Priority
from .context import Context, Session


class StateTransition(Enum):
    """状态转换类型"""
    INITIALIZING_TO_IDLE = (AgentStatus.INITIALIZING, AgentStatus.IDLE)
    IDLE_TO_BUSY = (AgentStatus.IDLE, AgentStatus.BUSY)
    BUSY_TO_IDLE = (AgentStatus.BUSY, AgentStatus.IDLE)
    BUSY_TO_ERROR = (AgentStatus.BUSY, AgentStatus.ERROR)
    ERROR_TO_IDLE = (AgentStatus.ERROR, AgentStatus.IDLE)
    IDLE_TO_STOPPED = (AgentStatus.IDLE, AgentStatus.STOPPED)
    BUSY_TO_STOPPED = (AgentStatus.BUSY, AgentStatus.STOPPED)
    ERROR_TO_STOPPED = (AgentStatus.ERROR, AgentStatus.STOPPED)

    def __init__(self, from_status: AgentStatus, to_status: AgentStatus):
        self.from_status = from_status
        self.to_status = to_status

    @classmethod
    def get_transition(cls, from_status: AgentStatus, to_status: AgentStatus) -> Optional["StateTransition"]:
        """获取状态转换"""
        for transition in cls:
            if transition.from_status == from_status and transition.to_status == to_status:
                return transition
        return None


@dataclass
class StateRecord:
    """状态记录"""
    agent_id: str
    status: AgentStatus
    timestamp: datetime
    metadata: Dict[str, Any]
    reason: Optional[str] = None
    duration: Optional[float] = None  # 状态持续时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateRecord":
        """从字典创建"""
        record = cls(
            agent_id=data['agent_id'],
            status=AgentStatus(data['status']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {}),
            reason=data.get('reason'),
            duration=data.get('duration')
        )
        return record


@dataclass
class AgentMetrics:
    """Agent指标"""
    agent_id: str
    total_state_changes: int = 0
    total_busy_time: float = 0.0
    total_error_time: float = 0.0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    average_task_duration: float = 0.0
    last_state_change: Optional[datetime] = None
    uptime_percentage: float = 0.0
    error_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.last_state_change:
            data['last_state_change'] = self.last_state_change.isoformat()
        return data


class StateTransitionRule:
    """状态转换规则"""

    def __init__(self, from_status: AgentStatus, to_status: AgentStatus, condition: Callable = None):
        """初始化转换规则

        Args:
            from_status: 源状态
            to_status: 目标状态
            condition: 转换条件函数
        """
        self.from_status = from_status
        self.to_status = to_status
        self.condition = condition or (lambda *args, **kwargs: True)

    def can_transition(self, from_status: AgentStatus, to_status: AgentStatus, **kwargs) -> bool:
        """检查是否可以转换"""
        return (self.from_status == from_status and
                self.to_status == to_status and
                self.condition(**kwargs))


class StateManager:
    """Agent状态管理器"""

    def __init__(self, max_history_size: int = 1000):
        """初始化状态管理器

        Args:
            max_history_size: 最大历史记录大小
        """
        self.max_history_size = max_history_size
        self.agent_states: Dict[str, AgentStatus] = {}
        self.state_history: List[StateRecord] = []
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.transition_rules: List[StateTransitionRule] = []
        self.state_watchers: List[Callable] = []
        self.contexts: Dict[str, Context] = {}
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("StateManager")

        # 添加默认转换规则
        self._add_default_rules()

    def _add_default_rules(self) -> None:
        """添加默认状态转换规则"""
        # 所有有效转换
        valid_transitions = [
            (AgentStatus.INITIALIZING, AgentStatus.IDLE),
            (AgentStatus.IDLE, AgentStatus.BUSY),
            (AgentStatus.BUSY, AgentStatus.IDLE),
            (AgentStatus.BUSY, AgentStatus.ERROR),
            (AgentStatus.ERROR, AgentStatus.IDLE),
            (AgentStatus.IDLE, AgentStatus.STOPPED),
            (AgentStatus.BUSY, AgentStatus.STOPPED),
            (AgentStatus.ERROR, AgentStatus.STOPPED),
        ]

        for from_status, to_status in valid_transitions:
            self.add_transition_rule(from_status, to_status)

    def add_transition_rule(self, from_status: AgentStatus, to_status: AgentStatus, condition: Callable = None) -> None:
        """添加状态转换规则

        Args:
            from_status: 源状态
            to_status: 目标状态
            condition: 转换条件
        """
        rule = StateTransitionRule(from_status, to_status, condition)
        self.transition_rules.append(rule)
        self.logger.debug(f"Added transition rule: {from_status.value} -> {to_status.value}")

    def add_state_watcher(self, watcher: Callable) -> None:
        """添加状态观察者

        Args:
            watcher: 观察者函数，接收(agent_id, old_status, new_status, metadata)参数
        """
        self.state_watchers.append(watcher)

    def remove_state_watcher(self, watcher: Callable) -> None:
        """移除状态观察者

        Args:
            watcher: 观察者函数
        """
        if watcher in self.state_watchers:
            self.state_watchers.remove(watcher)

    async def get_agent_state(self, agent_id: str) -> Optional[AgentStatus]:
        """获取Agent状态

        Args:
            agent_id: Agent ID

        Returns:
            Agent状态或None
        """
        async with self.lock:
            return self.agent_states.get(agent_id)

    async def set_agent_state(self, agent_id: str, new_status: AgentStatus, reason: str = None, metadata: Dict[str, Any] = None) -> bool:
        """设置Agent状态

        Args:
            agent_id: Agent ID
            new_status: 新状态
            reason: 转换原因
            metadata: 元数据

        Returns:
            是否设置成功
        """
        async with self.lock:
            old_status = self.agent_states.get(agent_id, AgentStatus.INITIALIZING)

            # 检查转换是否有效
            if not self._can_transition(old_status, new_status, agent_id=agent_id, metadata=metadata):
                self.logger.warning(f"Invalid state transition for {agent_id}: {old_status.value} -> {new_status.value}")
                return False

            # 计算状态持续时间
            now = datetime.now()
            duration = None
            if agent_id in self.agent_states:
                # 获取上次状态变更时间
                last_record = next((r for r in reversed(self.state_history) if r.agent_id == agent_id), None)
                if last_record:
                    duration = (now - last_record.timestamp).total_seconds()

            # 更新状态
            self.agent_states[agent_id] = new_status

            # 创建状态记录
            record = StateRecord(
                agent_id=agent_id,
                status=new_status,
                timestamp=now,
                metadata=metadata or {},
                reason=reason,
                duration=duration
            )

            # 添加到历史记录
            self.state_history.append(record)

            # 限制历史记录大小
            if len(self.state_history) > self.max_history_size:
                self.state_history = self.state_history[-self.max_history_size // 2:]

            # 更新指标
            await self._update_metrics(agent_id, old_status, new_status, duration)

            # 通知观察者
            await self._notify_watchers(agent_id, old_status, new_status, metadata)

            self.logger.info(f"Agent {agent_id} state changed: {old_status.value} -> {new_status.value}")
            return True

    def _can_transition(self, from_status: AgentStatus, to_status: AgentStatus, **kwargs) -> bool:
        """检查状态转换是否有效"""
        for rule in self.transition_rules:
            if rule.can_transition(from_status, to_status, **kwargs):
                return True
        return False

    async def _update_metrics(self, agent_id: str, old_status: AgentStatus, new_status: AgentStatus, duration: Optional[float]) -> None:
        """更新Agent指标"""
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)

        metrics = self.agent_metrics[agent_id]
        metrics.total_state_changes += 1
        metrics.last_state_change = datetime.now()

        # 更新状态持续时间指标
        if duration:
            if old_status == AgentStatus.BUSY:
                metrics.total_busy_time += duration
            elif old_status == AgentStatus.ERROR:
                metrics.total_error_time += duration

        # 计算其他指标
        await self._calculate_derived_metrics(agent_id)

    async def _calculate_derived_metrics(self, agent_id: str) -> None:
        """计算派生指标"""
        if agent_id not in self.agent_metrics:
            return

        metrics = self.agent_metrics[agent_id]

        # 计算正常运行时间百分比
        agent_records = [r for r in self.state_history if r.agent_id == agent_id]
        if agent_records:
            total_time = sum(r.duration for r in agent_records if r.duration)
            busy_time = sum(r.duration for r in agent_records
                          if r.duration and r.status == AgentStatus.BUSY)
            error_time = sum(r.duration for r in agent_records
                           if r.duration and r.status == AgentStatus.ERROR)

            if total_time > 0:
                metrics.uptime_percentage = ((total_time - error_time) / total_time) * 100

        # 计算错误率
        total_tasks = metrics.total_tasks_completed + metrics.total_tasks_failed
        if total_tasks > 0:
            metrics.error_rate = (metrics.total_tasks_failed / total_tasks) * 100

    async def _notify_watchers(self, agent_id: str, old_status: AgentStatus, new_status: AgentStatus, metadata: Optional[Dict[str, Any]]) -> None:
        """通知状态观察者"""
        for watcher in self.state_watchers:
            try:
                if asyncio.iscoroutinefunction(watcher):
                    await watcher(agent_id, old_status, new_status, metadata)
                else:
                    watcher(agent_id, old_status, new_status, metadata)
            except Exception as e:
                self.logger.error(f"Error notifying state watcher: {e}")

    async def get_state_history(self, agent_id: str = None, limit: int = 100) -> List[StateRecord]:
        """获取状态历史

        Args:
            agent_id: Agent ID，None表示所有Agent
            limit: 限制数量

        Returns:
            状态记录列表
        """
        async with self.lock:
            history = self.state_history

            if agent_id:
                history = [r for r in history if r.agent_id == agent_id]

            # 返回最新的记录
            return history[-limit:] if len(history) > limit else history

    async def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """获取Agent指标

        Args:
            agent_id: Agent ID

        Returns:
            Agent指标或None
        """
        async with self.lock:
            return self.agent_metrics.get(agent_id)

    async def get_all_agents_status(self) -> Dict[str, AgentStatus]:
        """获取所有Agent状态

        Returns:
            Agent状态字典
        """
        async with self.lock:
            return self.agent_states.copy()

    async def get_agents_by_status(self, status: AgentStatus) -> List[str]:
        """根据状态获取Agent列表

        Args:
            status: Agent状态

        Returns:
            Agent ID列表
        """
        async with self.lock:
            return [agent_id for agent_id, agent_status in self.agent_states.items()
                   if agent_status == status]

    async def record_task_completion(self, agent_id: str, success: bool, duration: float) -> None:
        """记录任务完成

        Args:
            agent_id: Agent ID
            success: 是否成功
            duration: 持续时间
        """
        async with self.lock:
            if agent_id not in self.agent_metrics:
                self.agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)

            metrics = self.agent_metrics[agent_id]
            if success:
                metrics.total_tasks_completed += 1
            else:
                metrics.total_tasks_failed += 1

            # 更新平均任务持续时间
            total_tasks = metrics.total_tasks_completed + metrics.total_tasks_failed
            current_avg = metrics.average_task_duration
            metrics.average_task_duration = (current_avg * (total_tasks - 1) + duration) / total_tasks

    def get_agent_context(self, agent_id: str) -> Optional[Context]:
        """获取Agent上下文

        Args:
            agent_id: Agent ID

        Returns:
            Agent上下文或None
        """
        return self.contexts.get(agent_id)

    def create_agent_context(self, agent_id: str) -> Context:
        """创建Agent上下文

        Args:
            agent_id: Agent ID

        Returns:
            Agent上下文
        """
        if agent_id not in self.contexts:
            self.contexts[agent_id] = Context(f"agent_{agent_id}")
        return self.contexts[agent_id]

    def remove_agent_context(self, agent_id: str) -> bool:
        """移除Agent上下文

        Args:
            agent_id: Agent ID

        Returns:
            是否移除成功
        """
        if agent_id in self.contexts:
            del self.contexts[agent_id]
            return True
        return False

    async def cleanup_expired_contexts(self) -> int:
        """清理过期上下文

        Returns:
            清理的上下文数量
        """
        cleaned = 0
        for context in self.contexts.values():
            if await context.cleanup_expired() > 0:
                cleaned += 1
        return cleaned

    async def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息

        Returns:
            统计信息
        """
        async with self.lock:
            status_counts = {}
            for status in AgentStatus:
                count = len([s for s in self.agent_states.values() if s == status])
                status_counts[status.value] = count

            return {
                "total_agents": len(self.agent_states),
                "status_distribution": status_counts,
                "total_state_records": len(self.state_history),
                "total_contexts": len(self.contexts),
                "transition_rules": len(self.transition_rules),
                "state_watchers": len(self.state_watchers)
            }

    async def export_state_data(self, agent_id: str = None) -> Dict[str, Any]:
        """导出状态数据

        Args:
            agent_id: Agent ID，None表示所有Agent

        Returns:
            状态数据
        """
        async with self.lock:
            data = {
                "timestamp": datetime.now().isoformat(),
                "agents": {},
                "history": [],
                "metrics": {}
            }

            # 导出当前状态
            for aid, status in self.agent_states.items():
                if agent_id is None or aid == agent_id:
                    data["agents"][aid] = status.value

            # 导出历史记录
            for record in self.state_history:
                if agent_id is None or record.agent_id == agent_id:
                    data["history"].append(record.to_dict())

            # 导出指标
            for aid, metrics in self.agent_metrics.items():
                if agent_id is None or aid == agent_id:
                    data["metrics"][aid] = metrics.to_dict()

            return data


# 全局状态管理器实例
global_state_manager = StateManager()


def get_state_manager() -> StateManager:
    """获取全局状态管理器"""
    return global_state_manager


# 便利函数
async def get_agent_state(agent_id: str) -> Optional[AgentStatus]:
    """获取Agent状态的便利函数"""
    return await global_state_manager.get_agent_state(agent_id)


async def set_agent_state(agent_id: str, status: AgentStatus, reason: str = None, metadata: Dict[str, Any] = None) -> bool:
    """设置Agent状态的便利函数"""
    return await global_state_manager.set_agent_state(agent_id, status, reason, metadata)