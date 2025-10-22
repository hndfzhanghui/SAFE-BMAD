"""LLM Configuration Manager

This module manages LLM configurations and provider settings.
"""

import yaml
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from .types import LLMProvider, LLMConfig, get_model_info


class LLMConfigManager:
    """LLM配置管理器"""

    def __init__(self, config_dir: str = "config/llm"):
        """初始化配置管理器

        Args:
            config_dir: 配置目录
        """
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger("LLMConfigManager")
        self._providers_config: Dict[str, Any] = {}
        self._model_configs: Dict[str, Dict[str, Any]] = {}

        # 加载配置
        self._load_configs()

    def _load_configs(self) -> None:
        """加载所有配置文件"""
        try:
            # 加载提供商配置
            providers_file = self.config_dir / "providers.yaml"
            if providers_file.exists():
                with open(providers_file, 'r', encoding='utf-8') as f:
                    self._providers_config = yaml.safe_load(f)
                    self.logger.info(f"Loaded providers config from {providers_file}")

            # 加载模型配置
            config_files = list(self.config_dir.glob("*.yaml"))
            for config_file in config_files:
                if config_file.name != "providers.yaml":
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config_data = yaml.safe_load(f)
                            # 根据文件名推断提供者
                            provider_name = None
                            if 'provider' in config_data:
                                provider_name = config_data['provider']
                                if provider_name not in self._model_configs:
                                    self._model_configs[provider_name] = {}
                                # 使用文件名作为配置名
                                config_name = config_file.stem
                                self._model_configs[provider_name][config_name] = config_data
                            else:
                                # 使用文件名作为配置名
                                config_name = config_file.stem
                                # 如果没有provider字段，跳过该配置
                                self.logger.warning(f"No provider specified in {config_file}, skipping")
                                continue
                    except Exception as e:
                        self.logger.error(f"Failed to load config from {config_file}: {e}")

            self.logger.info(f"Loaded {len(self._model_configs)} provider configs")

        except Exception as e:
            self.logger.error(f"Failed to load LLM configs: {e}")

    def get_provider_config(self, provider: LLMProvider) -> Dict[str, Any]:
        """获取提供商配置

        Args:
            provider: 提供商类型

        Returns:
            提供商配置字典
        """
        provider_str = provider.value
        return self._providers_config.get(provider_str, {})

    def get_model_config(
        self,
        provider: LLMProvider,
        model_name: Optional[str] = None,
        config_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取模型配置

        Args:
            provider: 提供商类型
            model_name: 模型名称
            config_name: 配置名称

        Returns:
            配置字典或None
        """
        provider_str = provider.value
        provider_configs = self._model_configs.get(provider_str, {})

        # 按优先级查找配置
        config = None
        search_order = [config_name, model_name]

        for search_key in search_order:
            if search_key:
                if search_key in provider_configs:
                    config = provider_configs[search_key]
                    break

        return config

    def create_llm_config(
        self,
        provider: LLMProvider,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        **overrides
    ) -> LLMConfig:
        """创建LLM配置

        Args:
            provider: 提供商类型
            model_name: 模型名称
            api_key: API密钥
            **overrides: 覆盖参数

        Returns:
            LLM配置对象
        """
        try:
            # 获取基础配置
            base_config = self.get_model_config(provider, model_name)

            # 合并覆盖参数
            config_data = {}
            if base_config:
                config_data.update(base_config)

            config_data.update(overrides)

            # 从环境变量获取API密钥
            if not api_key:
                api_key = self._get_api_key(provider)

            # 从环境变量获取API基础URL
            if 'api_base' not in config_data:
                config_data['api_base'] = self._get_api_base(provider)

            # 确保必需字段
            config_data.update({
                'provider': provider,
                'model': model_name or config_data.get('model'),
                'api_key': api_key,
            })

            # 创建LLM配置对象
            config = LLMConfig.from_dict(config_data)

            self.logger.debug(f"Created LLM config for {provider.value}:{config_data.get('model')}")
            return config

        except Exception as e:
            self.logger.error(f"Failed to create LLM config: {e}")
            raise

    def get_available_models(self, provider: LLMProvider) -> List[Dict[str, Any]]:
        """获取可用的模型列表

        Args:
            provider: 提供商类型

        Returns:
            模型列表
        """
        provider_configs = self._model_configs.get(provider.value, {})
        models = []

        for model_name, config in provider_configs.items():
            model_info = get_model_info(provider, model_name)
            if model_info:
                models.append({
                    'name': model_name,
                    'description': model_info['description'],
                    'capabilities': model_info['capabilities'],
                    'config': config
                })

        return models

    def get_default_adapter_id(self, provider: LLMProvider) -> str:
        """获取默认适配器ID

        Args:
            provider: 提供商类型

        Returns:
            默认适配器ID
        """
        provider_config = self.get_provider_config(provider)
        return provider_config.get('default_adapter', f"{provider.value}_main")

    def _get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """从环境变量获取API密钥

        Args:
            provider: 提供商类型

        Returns:
            API密钥或None
        """
        env_mappings = {
            LLMProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.GOOGLE: "GOOGLE_API_KEY",
            LLMProvider.GLM: "GLM_API_KEY",
            LLMProvider.ZHIPUAI: "ZHIPUAI_API_KEY"
        }

        env_key = env_mappings.get(provider)
        if env_key:
            return os.getenv(env_key)

        return None

    def _get_api_base(self, provider: LLMProvider) -> Optional[str]:
        """从环境变量获取API基础URL

        Args:
            provider: 提供商类型

        Returns:
            API基础URL或None
        """
        env_mappings = {
            LLMProvider.DEEPSEEK: "DEEPSEEK_API_BASE_URL",
            LLMProvider.OPENAI: "OPENAI_API_BASE",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_BASE_URL",
        LLMProvider.GOOGLE: "GOOGLE_API_BASE"
        }

        env_key = env_mappings.get(provider)
        if env_key:
            return os.getenv(env_key)

        return None

    def validate_config(self, config: LLMConfig) -> List[str]:
        """验证LLM配置

        Args:
            config: LLM配置

        Returns:
            错误列表
        """
        errors = []

        # 基础验证
        if not config.provider:
            errors.append("Provider is required")

        if not config.model:
            errors.append("Model is required")

        if not config.api_key and config.provider not in [LLMProvider.LOCAL]:
            errors.append("API key is required for this provider")

        # 获取模型信息进行验证
        model_info = get_model_info(config.provider, config.model)
        if not model_info:
            errors.append(f"Invalid model {config.model} for provider {config.provider.value}")

        # 模型特定验证
        if model_info:
            max_tokens = model_info.get("max_tokens", 4000)
            if config.max_tokens > max_tokens:
                errors.append(f"Max tokens {config.max_tokens} exceeds model limit {max_tokens}")

            if config.temperature < 0 or config.temperature > 2:
                errors.append("Temperature must be between 0 and 2")

        return errors

    def reload_configs(self) -> None:
        """重新加载配置"""
        self.logger.info("Reloading LLM configurations")
        self._model_configs.clear()
        self._load_configs()

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要

        Returns:
            配置摘要字典
        """
        summary = {
            "providers_configured": len(self._providers_config),
            "models_configured": {
                provider: len(configs)
                for provider, configs in self._model_configs.items()
            },
            "total_models": sum(len(configs) for configs in self._model_configs.values()),
            "config_dir": str(self.config_dir),
            "environment_keys": {
                provider: f"{provider.value}_API_KEY"
                for provider in [LLMProvider.DEEPSEEK, LLMProvider.OPENAI, LLMProvider.GOOGLE, LLMProvider.GLM]
            }
        }

        return summary


# 全局配置管理器实例
global_config_manager = LLMConfigManager()


def get_config_manager() -> LLMConfigManager:
    """获取全局配置管理器"""
    return global_config_manager


# 便利函数
def load_agent_llm_config(
    config_name: str,
    provider: Optional[LLMProvider] = None,
    **kwargs
) -> Optional[LLMConfig]:
    """加载Agent LLM配置的便利函数

    Args:
        config_name: 配置名称
        provider: 提供商类型
        **kwargs: 其他参数

    Returns:
        LLM配置或None
    """
    try:
        manager = get_config_manager()

        # 如果指定了提供商，从提供商配置中获取
        if provider:
            model_config = manager.get_model_config(provider, config_name, config_name)
            if model_config:
                return manager.create_llm_config(
                    provider=provider,
                    model_name=model_config.get('model'),
                    **model_config,
                    **kwargs
                )

        # 否则尝试从所有提供商中查找
        for prov in LLMProvider:
            model_config = manager.get_model_config(prov, config_name, config_name)
            if model_config:
                return manager.create_llm_config(
                    provider=prov,
                    model_name=model_config.get('model'),
                    **model_config,
                    **kwargs
                )

        return None

    except Exception as e:
        logging.error(f"Failed to load agent LLM config {config_name}: {e}")
        return None


def get_available_llm_providers() -> List[LLMProvider]:
    """获取可用的LLM提供商列表"""
    return [LLMProvider.DEEPSEEK, LLMProvider.OPENAI, LLMProvider.LOCAL]