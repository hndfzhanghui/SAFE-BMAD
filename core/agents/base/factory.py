"""Agent Factory for SAFE System

This module provides factory classes for creating and managing SAFE agents.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from .agent_base import SafeAgent
from .types import AgentType, AgentConfig
from ..registry import AgentRegistry


class AgentFactory:
    """Agent工厂类，负责创建和管理Agent实例"""

    def __init__(self, registry: Optional[AgentRegistry] = None):
        """初始化Agent工厂

        Args:
            registry: Agent注册表实例
        """
        self.registry = registry or AgentRegistry()
        self.logger = logging.getLogger("AgentFactory")
        self._agent_classes: Dict[AgentType, Type[SafeAgent]] = {
            AgentType.S_AGENT: SafeAgent,
            AgentType.A_AGENT: SafeAgent,
            AgentType.F_AGENT: SafeAgent,
            AgentType.E_AGENT: SafeAgent,
            AgentType.R_AGENT: SafeAgent,
        }
        self._instances: Dict[str, SafeAgent] = {}

    def register_agent_class(self, agent_type: AgentType, agent_class: Type[SafeAgent]) -> None:
        """注册自定义Agent类

        Args:
            agent_type: Agent类型
            agent_class: Agent类
        """
        self._agent_classes[agent_type] = agent_class
        self.logger.info(f"Registered agent class for type {agent_type.value}")

    def create_agent(
        self,
        config: AgentConfig,
        **kwargs
    ) -> Optional[SafeAgent]:
        """创建Agent实例

        Args:
            config: Agent配置
            **kwargs: 额外的创建参数

        Returns:
            Agent实例或None
        """
        try:
            self.logger.info(f"Creating agent {config.agent_id} of type {config.agent_type.value}")

            # 检查是否已存在
            if config.agent_id in self._instances:
                self.logger.warning(f"Agent {config.agent_id} already exists")
                return self._instances[config.agent_id]

            # 获取Agent类
            agent_class = self._agent_classes.get(config.agent_type, SafeAgent)

            # 创建实例
            agent = agent_class(
                name=config.name,
                agent_type=config.agent_type,
                config=config,
                **kwargs
            )

            # 存储实例
            self._instances[config.agent_id] = agent

            # 注册到注册表
            self.registry.register_agent(agent)

            self.logger.info(f"Agent {config.agent_id} created successfully")
            return agent

        except Exception as e:
            self.logger.error(f"Failed to create agent {config.agent_id}: {e}")
            return None

    def create_agent_from_config(
        self,
        config_dict: Dict[str, Any],
        **kwargs
    ) -> Optional[SafeAgent]:
        """从配置字典创建Agent

        Args:
            config_dict: 配置字典
            **kwargs: 额外的创建参数

        Returns:
            Agent实例或None
        """
        try:
            config = AgentConfig.from_dict(config_dict)
            return self.create_agent(config, **kwargs)

        except Exception as e:
            self.logger.error(f"Failed to create agent from config: {e}")
            return None

    async def create_multiple_agents(
        self,
        configs: List[AgentConfig],
        **kwargs
    ) -> List[SafeAgent]:
        """批量创建Agent

        Args:
            configs: Agent配置列表
            **kwargs: 额外的创建参数

        Returns:
            Agent实例列表
        """
        agents = []
        for config in configs:
            agent = self.create_agent(config, **kwargs)
            if agent:
                agents.append(agent)

        return agents

    def get_agent(self, agent_id: str) -> Optional[SafeAgent]:
        """获取Agent实例

        Args:
            agent_id: Agent ID

        Returns:
            Agent实例或None
        """
        return self._instances.get(agent_id)

    def get_agents_by_type(self, agent_type: AgentType) -> List[SafeAgent]:
        """根据类型获取Agent列表

        Args:
            agent_type: Agent类型

        Returns:
            Agent实例列表
        """
        return [
            agent for agent in self._instances.values()
            if agent.agent_type == agent_type
        ]

    def get_all_agents(self) -> List[SafeAgent]:
        """获取所有Agent实例

        Returns:
            所有Agent实例列表
        """
        return list(self._instances.values())

    def remove_agent(self, agent_id: str) -> bool:
        """移除Agent实例

        Args:
            agent_id: Agent ID

        Returns:
            是否成功移除
        """
        try:
            if agent_id in self._instances:
                # 从注册表移除
                agent = self._instances[agent_id]
                self.registry.unregister_agent(agent_id)

                # 停止Agent
                import asyncio
                asyncio.create_task(agent.stop())

                # 从实例字典移除
                del self._instances[agent_id]

                self.logger.info(f"Agent {agent_id} removed successfully")
                return True
            else:
                self.logger.warning(f"Agent {agent_id} not found")
                return False

        except Exception as e:
            self.logger.error(f"Failed to remove agent {agent_id}: {e}")
            return False

    async def initialize_all(self) -> bool:
        """初始化所有Agent

        Returns:
            是否全部初始化成功
        """
        success = True
        for agent_id, agent in self._instances.items():
            try:
                result = await agent.initialize(agent.config)
                if not result:
                    success = False
                    self.logger.error(f"Failed to initialize agent {agent_id}")

            except Exception as e:
                success = False
                self.logger.error(f"Error initializing agent {agent_id}: {e}")

        return success

    async def start_all(self) -> bool:
        """启动所有Agent

        Returns:
            是否全部启动成功
        """
        success = True
        for agent_id, agent in self._instances.items():
            try:
                result = await agent.start()
                if not result:
                    success = False
                    self.logger.error(f"Failed to start agent {agent_id}")

            except Exception as e:
                success = False
                self.logger.error(f"Error starting agent {agent_id}: {e}")

        return success

    async def stop_all(self) -> bool:
        """停止所有Agent

        Returns:
            是否全部停止成功
        """
        success = True
        for agent_id, agent in self._instances.items():
            try:
                result = await agent.stop()
                if not result:
                    success = False
                    self.logger.error(f"Failed to stop agent {agent_id}")

            except Exception as e:
                success = False
                self.logger.error(f"Error stopping agent {agent_id}: {e}")

        return success

    async def cleanup_all(self) -> bool:
        """清理所有Agent

        Returns:
            是否全部清理成功
        """
        success = True
        for agent_id, agent in list(self._instances.items()):
            try:
                result = await agent.cleanup()
                if result:
                    # 从实例字典移除
                    del self._instances[agent_id]
                    # 从注册表移除
                    self.registry.unregister_agent(agent_id)
                else:
                    success = False
                    self.logger.error(f"Failed to cleanup agent {agent_id}")

            except Exception as e:
                success = False
                self.logger.error(f"Error cleaning up agent {agent_id}: {e}")

        return success

    def get_factory_status(self) -> Dict[str, Any]:
        """获取工厂状态

        Returns:
            工厂状态信息
        """
        agents_by_type = {}
        for agent_type in AgentType:
            agents_by_type[agent_type.value] = len(self.get_agents_by_type(agent_type))

        return {
            "total_agents": len(self._instances),
            "agents_by_type": agents_by_type,
            "agent_ids": list(self._instances.keys()),
            "registered_classes": list(self._agent_classes.keys())
        }


class TeamFactory:
    """团队工厂类，用于创建和管理Agent团队"""

    def __init__(self, agent_factory: Optional[AgentFactory] = None):
        """初始化团队工厂

        Args:
            agent_factory: Agent工厂实例
        """
        self.agent_factory = agent_factory or AgentFactory()
        self.logger = logging.getLogger("TeamFactory")
        self._team_configs = {}

    def register_team_config(self, team_name: str, config: Dict[str, Any]) -> None:
        """注册团队配置

        Args:
            team_name: 团队名称
            config: 团队配置
        """
        self._team_configs[team_name] = config
        self.logger.info(f"Registered team config for {team_name}")

    def create_safe_team(
        self,
        team_name: str = "default_team",
        llm_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[SafeAgent]:
        """创建标准的SAFE团队

        Args:
            team_name: 团队名称
            llm_config: LLM配置
            **kwargs: 额外参数

        Returns:
            Agent实例列表
        """
        agents = []

        # S-Agent
        s_config = AgentConfig(
            agent_id=f"s_agent_{team_name}",
            agent_type=AgentType.S_AGENT,
            name=f"S-Agent-{team_name}",
            system_message="我是战略家，负责制定应急响应战略框架和决策指导。",
            llm_config=llm_config,
            custom_config={"team": team_name}
        )
        agents.append(self.agent_factory.create_agent(s_config, **kwargs))

        # A-Agent
        a_config = AgentConfig(
            agent_id=f"a_agent_{team_name}",
            agent_type=AgentType.A_AGENT,
            name=f"A-Agent-{team_name}",
            system_message="我是态势感知专家，负责分析现场态势和识别关键信息。",
            llm_config=llm_config,
            custom_config={"team": team_name}
        )
        agents.append(self.agent_factory.create_agent(a_config, **kwargs))

        # F-Agent
        f_config = AgentConfig(
            agent_id=f"f_agent_{team_name}",
            agent_type=AgentType.F_AGENT,
            name=f"F-Agent-{team_name}",
            system_message="我是领域专家，负责提供专业领域的知识支持和技术指导。",
            llm_config=llm_config,
            custom_config={"team": team_name}
        )
        agents.append(self.agent_factory.create_agent(f_config, **kwargs))

        # E-Agent
        e_config = AgentConfig(
            agent_id=f"e_agent_{team_name}",
            agent_type=AgentType.E_AGENT,
            name=f"E-Agent-{team_name}",
            system_message="我是执行协调官，负责将战略转化为可执行的行动计划。",
            llm_config=llm_config,
            custom_config={"team": team_name}
        )
        agents.append(self.agent_factory.create_agent(e_config, **kwargs))

        self.logger.info(f"Created SAFE team '{team_name}' with {len(agents)} agents")
        return agents

    def create_custom_team(
        self,
        team_name: str,
        agent_configs: List[AgentConfig],
        **kwargs
    ) -> List[SafeAgent]:
        """创建自定义团队

        Args:
            team_name: 团队名称
            agent_configs: Agent配置列表
            **kwargs: 额外参数

        Returns:
            Agent实例列表
        """
        agents = []
        for config in agent_configs:
            # 为每个Agent添加团队标识
            config.custom_config = config.custom_config or {}
            config.custom_config["team"] = team_name

            agent = self.agent_factory.create_agent(config, **kwargs)
            if agent:
                agents.append(agent)

        self.logger.info(f"Created custom team '{team_name}' with {len(agents)} agents")
        return agents

    def get_team_agents(self, team_name: str) -> List[SafeAgent]:
        """获取团队Agent

        Args:
            team_name: 团队名称

        Returns:
            团队Agent列表
        """
        return [
            agent for agent in self.agent_factory.get_all_agents()
            if agent.config.custom_config.get("team") == team_name
        ]


# 全局工厂实例
global_agent_factory = AgentFactory()
global_team_factory = TeamFactory(global_agent_factory)


# 便利函数
def create_agent(config: AgentConfig, **kwargs) -> Optional[SafeAgent]:
    """创建Agent的便利函数"""
    return global_agent_factory.create_agent(config, **kwargs)


def create_safe_team(team_name: str = "default", **kwargs) -> List[SafeAgent]:
    """创建SAFE团队的便利函数"""
    return global_team_factory.create_safe_team(team_name, **kwargs)