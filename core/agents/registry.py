"""Agent Registry for SAFE System

This module provides agent registration and discovery functionality.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from .base.agent_base import SafeAgent
from .base.types import AgentType, AgentStatus, AgentCapability


class AgentRegistry:
    """Agent注册表，负责Agent的注册、发现和管理"""

    def __init__(self):
        """初始化Agent注册表"""
        self._agents: Dict[str, SafeAgent] = {}
        self._agents_by_type: Dict[AgentType, Set[str]] = {agent_type: set() for agent_type in AgentType}
        self._agents_by_status: Dict[AgentStatus, Set[str]] = {status: set() for status in AgentStatus}
        self._capabilities: Dict[str, Set[str]] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._services: Dict[str, Dict[str, Any]] = {}
        self._health_checks: Dict[str, datetime] = {}
        self._watchers: List[Callable] = []
        self.logger = logging.getLogger("AgentRegistry")

    def register_agent(self, agent: SafeAgent) -> bool:
        """注册Agent

        Args:
            agent: Agent实例

        Returns:
            是否注册成功
        """
        try:
            agent_id = agent.get_agent_id()
            agent_type = AgentType(agent.get_agent_type())

            if agent_id in self._agents:
                self.logger.warning(f"Agent {agent_id} already registered, updating...")
                self.unregister_agent(agent_id)

            # 添加到注册表
            self._agents[agent_id] = agent
            self._agents_by_type[agent_type].add(agent_id)
            self._agents_by_status[agent.get_status()].add(agent_id)

            # 初始化能力和依赖
            self._capabilities[agent_id] = set()
            self._dependencies[agent_id] = set()

            # 注册服务
            service_info = agent.get_service_info()
            self._services[agent_id] = service_info

            # 记录健康检查时间
            self._health_checks[agent_id] = datetime.now()

            # 通知观察者
            self._notify_watchers("agent_registered", {"agent_id": agent_id, "agent": agent})

            self.logger.info(f"Agent {agent_id} registered successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register agent: {e}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent

        Args:
            agent_id: Agent ID

        Returns:
            是否注销成功
        """
        try:
            if agent_id not in self._agents:
                self.logger.warning(f"Agent {agent_id} not found")
                return False

            agent = self._agents[agent_id]
            agent_type = AgentType(agent.get_agent_type())

            # 从各个索引中移除
            del self._agents[agent_id]
            self._agents_by_type[agent_type].discard(agent_id)

            # 从所有状态索引中移除
            for status_set in self._agents_by_status.values():
                status_set.discard(agent_id)

            # 清理其他数据
            self._capabilities.pop(agent_id, None)
            self._dependencies.pop(agent_id, None)
            self._services.pop(agent_id, None)
            self._health_checks.pop(agent_id, None)

            # 通知观察者
            self._notify_watchers("agent_unregistered", {"agent_id": agent_id})

            self.logger.info(f"Agent {agent_id} unregistered successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False

    def get_agent(self, agent_id: str) -> Optional[SafeAgent]:
        """获取Agent实例

        Args:
            agent_id: Agent ID

        Returns:
            Agent实例或None
        """
        return self._agents.get(agent_id)

    def get_agents_by_type(self, agent_type: AgentType) -> List[SafeAgent]:
        """根据类型获取Agent列表

        Args:
            agent_type: Agent类型

        Returns:
            Agent实例列表
        """
        agent_ids = self._agents_by_type[agent_type]
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def get_agents_by_status(self, status: AgentStatus) -> List[SafeAgent]:
        """根据状态获取Agent列表

        Args:
            status: Agent状态

        Returns:
            Agent实例列表
        """
        agent_ids = self._agents_by_status[status]
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def get_agents_by_capability(self, capability: str) -> List[SafeAgent]:
        """根据能力获取Agent列表

        Args:
            capability: 能力名称

        Returns:
            具有该能力的Agent列表
        """
        agent_ids = [
            aid for aid, caps in self._capabilities.items()
            if capability in caps
        ]
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def find_agents(self, **filters) -> List[SafeAgent]:
        """查找符合条件的Agent

        Args:
            **filters: 过滤条件

        Returns:
            符合条件的Agent列表
        """
        result = list(self._agents.values())

        # 按类型过滤
        if "agent_type" in filters:
            agent_type = filters["agent_type"]
            if isinstance(agent_type, str):
                agent_type = AgentType(agent_type)
            result = [a for a in result if a.agent_type == agent_type]

        # 按状态过滤
        if "status" in filters:
            status = filters["status"]
            if isinstance(status, str):
                status = AgentStatus(status)
            result = [a for a in result if a.get_status() == status]

        # 按能力过滤
        if "capability" in filters:
            capability = filters["capability"]
            result = [a for a in result if any(cap.name == capability for cap in a.get_capabilities())]

        # 按名称过滤
        if "name_contains" in filters:
            name_contains = filters["name_contains"].lower()
            result = [a for a in result if name_contains in a.config.name.lower()]

        # 按团队过滤
        if "team" in filters:
            team = filters["team"]
            result = [a for a in result if a.config.custom_config.get("team") == team]

        return result

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """更新Agent状态

        Args:
            agent_id: Agent ID
            status: 新状态

        Returns:
            是否更新成功
        """
        try:
            if agent_id not in self._agents:
                return False

            agent = self._agents[agent_id]
            old_status = agent.get_status()

            # 从旧状态索引中移除
            self._agents_by_status[old_status].discard(agent_id)

            # 添加到新状态索引
            self._agents_by_status[status].add(agent_id)

            # 通知观察者
            self._notify_watchers("status_changed", {
                "agent_id": agent_id,
                "old_status": old_status,
                "new_status": status
            })

            return True

        except Exception as e:
            self.logger.error(f"Failed to update agent status: {e}")
            return False

    def add_agent_capability(self, agent_id: str, capability: str) -> bool:
        """添加Agent能力

        Args:
            agent_id: Agent ID
            capability: 能力名称

        Returns:
            是否添加成功
        """
        try:
            if agent_id not in self._capabilities:
                return False

            self._capabilities[agent_id].add(capability)
            return True

        except Exception as e:
            self.logger.error(f"Failed to add agent capability: {e}")
            return False

    def remove_agent_capability(self, agent_id: str, capability: str) -> bool:
        """移除Agent能力

        Args:
            agent_id: Agent ID
            capability: 能力名称

        Returns:
            是否移除成功
        """
        try:
            if agent_id not in self._capabilities:
                return False

            self._capabilities[agent_id].discard(capability)
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove agent capability: {e}")
            return False

    def get_agent_dependencies(self, agent_id: str) -> Set[str]:
        """获取Agent依赖

        Args:
            agent_id: Agent ID

        Returns:
            依赖的Agent ID集合
        """
        return self._dependencies.get(agent_id, set()).copy()

    def add_agent_dependency(self, agent_id: str, dependency_id: str) -> bool:
        """添加Agent依赖

        Args:
            agent_id: Agent ID
            dependency_id: 依赖的Agent ID

        Returns:
            是否添加成功
        """
        try:
            if agent_id not in self._dependencies:
                return False

            if dependency_id not in self._agents:
                self.logger.warning(f"Dependency agent {dependency_id} not found")
                return False

            self._dependencies[agent_id].add(dependency_id)
            return True

        except Exception as e:
            self.logger.error(f"Failed to add agent dependency: {e}")
            return False

    def remove_agent_dependency(self, agent_id: str, dependency_id: str) -> bool:
        """移除Agent依赖

        Args:
            agent_id: Agent ID
            dependency_id: 依赖的Agent ID

        Returns:
            是否移除成功
        """
        try:
            if agent_id not in self._dependencies:
                return False

            self._dependencies[agent_id].discard(dependency_id)
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove agent dependency: {e}")
            return False

    def get_service_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取服务信息

        Args:
            agent_id: Agent ID

        Returns:
            服务信息或None
        """
        return self._services.get(agent_id)

    def discover_services(self, **filters) -> List[Dict[str, Any]]:
        """发现服务

        Args:
            **filters: 过滤条件

        Returns:
            符合条件的服务信息列表
        """
        services = []

        for agent_id, service_info in self._services.items():
            # 应用过滤条件
            match = True

            if "agent_type" in filters:
                if service_info.get("agent_type") != filters["agent_type"]:
                    match = False

            if "capability" in filters:
                if filters["capability"] not in service_info.get("capabilities", []):
                    match = False

            if "status" in filters:
                if service_info.get("status") != filters["status"]:
                    match = False

            if match:
                services.append(service_info)

        return services

    def update_health_check(self, agent_id: str) -> bool:
        """更新健康检查时间

        Args:
            agent_id: Agent ID

        Returns:
            是否更新成功
        """
        try:
            if agent_id in self._agents:
                self._health_checks[agent_id] = datetime.now()
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to update health check: {e}")
            return False

    def get_unhealthy_agents(self, timeout_minutes: int = 5) -> List[str]:
        """获取不健康的Agent

        Args:
            timeout_minutes: 超时时间（分钟）

        Returns:
            不健康的Agent ID列表
        """
        timeout = timedelta(minutes=timeout_minutes)
        now = datetime.now()

        unhealthy_agents = []
        for agent_id, last_check in self._health_checks.items():
            if now - last_check > timeout:
                unhealthy_agents.append(agent_id)

        return unhealthy_agents

    async def health_check_all(self) -> Dict[str, bool]:
        """对所有Agent进行健康检查

        Returns:
            健康检查结果
        """
        results = {}

        for agent_id, agent in self._agents.items():
            try:
                is_healthy = await agent.health_check()
                results[agent_id] = is_healthy

                if is_healthy:
                    self.update_health_check(agent_id)

            except Exception as e:
                self.logger.error(f"Health check failed for {agent_id}: {e}")
                results[agent_id] = False

        return results

    def add_watcher(self, callback: Callable) -> None:
        """添加观察者

        Args:
            callback: 回调函数
        """
        self._watchers.append(callback)

    def remove_watcher(self, callback: Callable) -> None:
        """移除观察者

        Args:
            callback: 回调函数
        """
        if callback in self._watchers:
            self._watchers.remove(callback)

    def _notify_watchers(self, event: str, data: Dict[str, Any]) -> None:
        """通知所有观察者

        Args:
            event: 事件名称
            data: 事件数据
        """
        for watcher in self._watchers:
            try:
                watcher(event, data)
            except Exception as e:
                self.logger.error(f"Watcher notification failed: {e}")

    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息

        Returns:
            统计信息
        """
        stats = {
            "total_agents": len(self._agents),
            "agents_by_type": {
                agent_type.value: len(agents)
                for agent_type, agents in self._agents_by_type.items()
            },
            "agents_by_status": {
                status.value: len(agents)
                for status, agents in self._agents_by_status.items()
            },
            "total_capabilities": sum(len(caps) for caps in self._capabilities.values()),
            "total_dependencies": sum(len(deps) for deps in self._dependencies.values()),
            "unhealthy_agents": len(self.get_unhealthy_agents()),
            "watchers_count": len(self._watchers)
        }

        return stats

    def get_all_agents(self) -> List[SafeAgent]:
        """获取所有注册的Agent

        Returns:
            所有Agent列表
        """
        return list(self._agents.values())

    def clear_registry(self) -> bool:
        """清空注册表

        Returns:
            是否清空成功
        """
        try:
            self._agents.clear()
            for agent_set in self._agents_by_type.values():
                agent_set.clear()
            for status_set in self._agents_by_status.values():
                status_set.clear()
            self._capabilities.clear()
            self._dependencies.clear()
            self._services.clear()
            self._health_checks.clear()

            self.logger.info("Registry cleared successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear registry: {e}")
            return False


# 全局注册表实例
global_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """获取全局注册表实例"""
    return global_registry


def register_agent(agent: SafeAgent) -> bool:
    """注册Agent的便利函数"""
    return global_registry.register_agent(agent)


def unregister_agent(agent_id: str) -> bool:
    """注销Agent的便利函数"""
    return global_registry.unregister_agent(agent_id)


def get_agent(agent_id: str) -> Optional[SafeAgent]:
    """获取Agent的便利函数"""
    return global_registry.get_agent(agent_id)