"""Configuration Manager for SAFE Agent System

This module provides comprehensive configuration management for agents.
"""

import asyncio
import json
import logging
import yaml
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
from ..base.types import AgentConfig, AgentType
from .templates import TemplateManager, get_template_manager


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str = "config"):
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        self.agent_configs: Dict[str, AgentConfig] = {}
        self.team_configs: Dict[str, Dict[str, Any]] = {}
        self.environment_configs: Dict[str, Dict[str, Any]] = {}
        self.template_manager = get_template_manager()
        self.watchers: List[Callable] = []
        self.file_modification_times: Dict[str, float] = {}
        self.logger = logging.getLogger("ConfigManager")

    async def load_agent_config(self, config_path: Union[str, Path]) -> Optional[AgentConfig]:
        """加载Agent配置

        Args:
            config_path: 配置文件路径

        Returns:
            Agent配置或None
        """
        try:
            config_path = Path(config_path)

            if not config_path.exists():
                self.logger.error(f"Config file not found: {config_path}")
                return None

            # 根据文件扩展名选择解析器
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                self.logger.error(f"Unsupported config file format: {config_path.suffix}")
                return None

            # 创建AgentConfig
            agent_config = AgentConfig.from_dict(data)

            # 验证配置
            errors = self._validate_agent_config(agent_config)
            if errors:
                raise ConfigValidationError(f"Config validation failed: {', '.join(errors)}")

            # 缓存配置
            self.agent_configs[agent_config.agent_id] = agent_config

            # 记录文件修改时间
            self.file_modification_times[str(config_path)] = config_path.stat().st_mtime

            self.logger.info(f"Loaded agent config: {agent_config.agent_id}")
            return agent_config

        except Exception as e:
            self.logger.error(f"Failed to load agent config from {config_path}: {e}")
            return None

    async def save_agent_config(self, agent_config: AgentConfig, config_path: Union[str, Path]) -> bool:
        """保存Agent配置

        Args:
            agent_config: Agent配置
            config_path: 配置文件路径

        Returns:
            是否保存成功
        """
        try:
            config_path = Path(config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # 验证配置
            errors = self._validate_agent_config(agent_config)
            if errors:
                raise ConfigValidationError(f"Config validation failed: {', '.join(errors)}")

            # 转换为字典
            data = agent_config.to_dict()

            # 根据文件扩展名选择格式
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                self.logger.error(f"Unsupported config file format: {config_path.suffix}")
                return False

            # 缓存配置
            self.agent_configs[agent_config.agent_id] = agent_config

            # 记录文件修改时间
            self.file_modification_times[str(config_path)] = config_path.stat().st_mtime

            # 通知观察者
            await self._notify_watchers("config_saved", {
                "agent_id": agent_config.agent_id,
                "config_path": str(config_path)
            })

            self.logger.info(f"Saved agent config: {agent_config.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save agent config to {config_path}: {e}")
            return False

    async def create_agent_config(
        self,
        agent_id: str,
        agent_type: AgentType,
        name: str,
        template_name: Optional[str] = None,
        **overrides
    ) -> Optional[AgentConfig]:
        """创建Agent配置

        Args:
            agent_id: Agent ID
            agent_type: Agent类型
            name: Agent名称
            template_name: 模板名称
            **overrides: 覆盖参数

        Returns:
            Agent配置或None
        """
        try:
            # 使用模板或创建基础配置
            if template_name:
                config_data = self.template_manager.create_config(template_name, **overrides)
                if not config_data:
                    self.logger.error(f"Template not found: {template_name}")
                    return None
            else:
                # 使用Agent类型对应的默认模板
                config_data = self.template_manager.create_config(agent_type.value, **overrides)
                if not config_data:
                    # 创建基础配置
                    config_data = {
                        "agent_id": agent_id,
                        "agent_type": agent_type.value,
                        "name": name,
                        "description": f"{agent_type.value} agent",
                        "system_message": f"I am a {agent_type.value} agent named {name}.",
                        "max_consecutive_auto_reply": 10,
                        "human_input_mode": "NEVER",
                        "code_execution_config": False
                    }

            # 确保必需字段
            config_data["agent_id"] = agent_id
            config_data["agent_type"] = agent_type.value
            config_data["name"] = name

            # 创建AgentConfig
            agent_config = AgentConfig.from_dict(config_data)

            # 验证配置
            errors = self._validate_agent_config(agent_config)
            if errors:
                raise ConfigValidationError(f"Config validation failed: {', '.join(errors)}")

            # 缓存配置
            self.agent_configs[agent_id] = agent_config

            self.logger.info(f"Created agent config: {agent_id}")
            return agent_config

        except Exception as e:
            self.logger.error(f"Failed to create agent config for {agent_id}: {e}")
            return None

    async def update_agent_config(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """更新Agent配置

        Args:
            agent_id: Agent ID
            updates: 更新内容

        Returns:
            是否更新成功
        """
        try:
            if agent_id not in self.agent_configs:
                self.logger.error(f"Agent config not found: {agent_id}")
                return False

            # 获取当前配置
            current_config = self.agent_configs[agent_id]
            current_data = current_config.to_dict()

            # 应用更新
            current_data.update(updates)

            # 创建新配置
            new_config = AgentConfig.from_dict(current_data)

            # 验证配置
            errors = self._validate_agent_config(new_config)
            if errors:
                raise ConfigValidationError(f"Config validation failed: {', '.join(errors)}")

            # 更新配置
            self.agent_configs[agent_id] = new_config

            # 通知观察者
            await self._notify_watchers("config_updated", {
                "agent_id": agent_id,
                "updates": updates
            })

            self.logger.info(f"Updated agent config: {agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update agent config for {agent_id}: {e}")
            return False

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """获取Agent配置

        Args:
            agent_id: Agent ID

        Returns:
            Agent配置或None
        """
        return self.agent_configs.get(agent_id)

    def list_agent_configs(self) -> List[str]:
        """列出所有Agent配置ID

        Returns:
            Agent ID列表
        """
        return list(self.agent_configs.keys())

    async def remove_agent_config(self, agent_id: str) -> bool:
        """移除Agent配置

        Args:
            agent_id: Agent ID

        Returns:
            是否移除成功
        """
        try:
            if agent_id in self.agent_configs:
                del self.agent_configs[agent_id]

                # 通知观察者
                await self._notify_watchers("config_removed", {
                    "agent_id": agent_id
                })

                self.logger.info(f"Removed agent config: {agent_id}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to remove agent config for {agent_id}: {e}")
            return False

    async def load_team_config(self, config_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """加载团队配置

        Args:
            config_path: 配置文件路径

        Returns:
            团队配置或None
        """
        try:
            config_path = Path(config_path)

            if not config_path.exists():
                self.logger.error(f"Team config file not found: {config_path}")
                return None

            # 解析配置文件
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                self.logger.error(f"Unsupported config file format: {config_path.suffix}")
                return None

            team_name = data.get("team_name")
            if team_name:
                self.team_configs[team_name] = data
                self.logger.info(f"Loaded team config: {team_name}")
                return data

        except Exception as e:
            self.logger.error(f"Failed to load team config from {config_path}: {e}")
        return None

    async def save_team_config(self, team_config: Dict[str, Any], config_path: Union[str, Path]) -> bool:
        """保存团队配置

        Args:
            team_config: 团队配置
            config_path: 配置文件路径

        Returns:
            是否保存成功
        """
        try:
            config_path = Path(config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            team_name = team_config.get("team_name")
            if not team_name:
                self.logger.error("Team config missing 'team_name' field")
                return False

            # 保存配置文件
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(team_config, f, default_flow_style=False, allow_unicode=True)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(team_config, f, indent=2, ensure_ascii=False)
            else:
                self.logger.error(f"Unsupported config file format: {config_path.suffix}")
                return False

            # 缓存配置
            self.team_configs[team_name] = team_config

            self.logger.info(f"Saved team config: {team_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save team config to {config_path}: {e}")
            return False

    def get_team_config(self, team_name: str) -> Optional[Dict[str, Any]]:
        """获取团队配置

        Args:
            team_name: 团队名称

        Returns:
            团队配置或None
        """
        return self.team_configs.get(team_name)

    async def watch_config_files(self, interval: int = 30) -> None:
        """监控配置文件变化

        Args:
            interval: 检查间隔（秒）
        """
        while True:
            try:
                await self._check_config_file_changes()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in config file watching: {e}")
                await asyncio.sleep(interval)

    async def _check_config_file_changes(self) -> None:
        """检查配置文件变化"""
        for config_path, agent_config in self.agent_configs.items():
            expected_file = self.config_dir / f"{agent_config.agent_id}.yaml"
            if expected_file.exists():
                current_mtime = expected_file.stat().st_mtime
                last_mtime = self.file_modification_times.get(str(expected_file), 0)

                if current_mtime > last_mtime:
                    # 文件已修改，重新加载
                    await self.load_agent_config(expected_file)
                    await self._notify_watchers("config_file_changed", {
                        "agent_id": agent_config.agent_id,
                        "config_path": str(expected_file)
                    })

    def _validate_agent_config(self, config: AgentConfig) -> List[str]:
        """验证Agent配置

        Args:
            config: Agent配置

        Returns:
            错误列表
        """
        errors = []

        # 基础验证
        if not config.agent_id:
            errors.append("agent_id is required")

        if not config.name:
            errors.append("name is required")

        if config.max_consecutive_auto_reply < 1:
            errors.append("max_consecutive_auto_reply must be >= 1")

        # 根据Agent类型验证特定字段
        if config.agent_type == AgentType.S_AGENT:
            if not any("strategic" in cap.lower() or "analysis" in cap.lower()
                      for cap in config.capabilities):
                errors.append("S-Agent should have strategic analysis capabilities")

        elif config.agent_type == AgentType.A_AGENT:
            if not any("monitor" in cap.lower() or "situat" in cap.lower()
                      for cap in config.capabilities):
                errors.append("A-Agent should have situation monitoring capabilities")

        elif config.agent_type == AgentType.F_AGENT:
            if not any("expert" in cap.lower() or "technical" in cap.lower()
                      for cap in config.capabilities):
                errors.append("F-Agent should have expert capabilities")

        elif config.agent_type == AgentType.E_AGENT:
            if not any("execut" in cap.lower() or "plan" in cap.lower()
                      for cap in config.capabilities):
                errors.append("E-Agent should have execution planning capabilities")

        return errors

    async def _notify_watchers(self, event: str, data: Dict[str, Any]) -> None:
        """通知配置观察者

        Args:
            event: 事件类型
            data: 事件数据
        """
        for watcher in self.watchers:
            try:
                if asyncio.iscoroutinefunction(watcher):
                    await watcher(event, data)
                else:
                    watcher(event, data)
            except Exception as e:
                self.logger.error(f"Error notifying config watcher: {e}")

    def add_watcher(self, watcher: Callable) -> None:
        """添加配置观察者

        Args:
            watcher: 观察者函数
        """
        self.watchers.append(watcher)

    def remove_watcher(self, watcher: Callable) -> None:
        """移除配置观察者

        Args:
            watcher: 观察者函数
        """
        if watcher in self.watchers:
            self.watchers.remove(watcher)

    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息

        Returns:
            统计信息
        """
        return {
            "agent_configs_count": len(self.agent_configs),
            "team_configs_count": len(self.team_configs),
            "environment_configs_count": len(self.environment_configs),
            "watchers_count": len(self.watchers),
            "config_dir": str(self.config_dir),
            "template_count": len(self.template_manager.templates)
        }

    async def export_configs(self, output_dir: str) -> bool:
        """导出所有配置

        Args:
            output_dir: 输出目录

        Returns:
            是否导出成功
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 导出Agent配置
            for agent_config in self.agent_configs.values():
                config_file = output_path / f"{agent_config.agent_id}.yaml"
                await self.save_agent_config(agent_config, config_file)

            # 导出团队配置
            for team_name, team_config in self.team_configs.items():
                config_file = output_path / f"team_{team_name}.yaml"
                await self.save_team_config(team_config, config_file)

            self.logger.info(f"Exported configs to {output_dir}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export configs: {e}")
            return False


# 全局配置管理器
global_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    return global_config_manager