"""LLM Manager

This module provides unified management for multiple LLM providers and models.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from datetime import datetime, timedelta

from .adapters import (
    BaseLLMAdapter,
    DeepSeekAdapter,
    OpenAIAdapter,
    LocalModelAdapter,
    GLMAdapter,
    MockAdapter
)
from .types import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMConfig,
    LLMTool,
    LLMMetrics
)


class LLMManager:
    """LLM管理器，负责管理多个LLM提供商和模型"""

    def __init__(self):
        """初始化LLM管理器"""
        self.adapters: Dict[str, BaseLLMAdapter] = {}
        self.default_adapter: Optional[str] = None
        self.sessions: Dict[str, List[LLMMessage]] = {}
        self.metrics: Dict[str, LLMMetrics] = {}
        self.logger = logging.getLogger("LLMManager")
        self._lock = asyncio.Lock()

    async def register_adapter(
        self,
        adapter_id: str,
        adapter: BaseLLMAdapter,
        is_default: bool = False
    ) -> bool:
        """注册LLM适配器

        Args:
            adapter_id: 适配器ID
            adapter: 适配器实例
            is_default: 是否设为默认

        Returns:
            是否注册成功
        """
        try:
            async with self._lock:
                if adapter_id in self.adapters:
                    self.logger.warning(f"Adapter {adapter_id} already registered, updating...")

                # 初始化适配器
                initialized = await adapter.initialize()
                if not initialized:
                    self.logger.error(f"Failed to initialize adapter {adapter_id}")
                    return False

                self.adapters[adapter_id] = adapter

                if is_default or not self.default_adapter:
                    self.default_adapter = adapter_id

                self.logger.info(f"Registered LLM adapter: {adapter_id}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to register adapter {adapter_id}: {e}")
            return False

    def unregister_adapter(self, adapter_id: str) -> bool:
        """注销LLM适配器

        Args:
            adapter_id: 适配器ID

        Returns:
            是否注销成功
        """
        try:
            if adapter_id not in self.adapters:
                self.logger.warning(f"Adapter {adapter_id} not found")
                return False

            # 清理适配器
            adapter = self.adapters[adapter_id]
            asyncio.create_task(adapter.cleanup())

            del self.adapters[adapter_id]

            # 如果是默认适配器，重新选择默认
            if self.default_adapter == adapter_id:
                if self.adapters:
                    self.default_adapter = next(iter(self.adapters))
                else:
                    self.default_adapter = None

            self.logger.info(f"Unregistered LLM adapter: {adapter_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister adapter {adapter_id}: {e}")
            return False

    async def create_adapter(
        self,
        adapter_id: str,
        config: LLMConfig,
        is_default: bool = False
    ) -> bool:
        """创建并注册适配器

        Args:
            adapter_id: 适配器ID
            config: LLM配置
            is_default: 是否设为默认

        Returns:
            是否创建成功
        """
        try:
            # 根据提供商选择适配器类
            adapter_class = self._get_adapter_class(config.provider)
            adapter = adapter_class(config)

            return await self.register_adapter(adapter_id, adapter, is_default)

        except Exception as e:
            self.logger.error(f"Failed to create adapter {adapter_id}: {e}")
            return False

    def _get_adapter_class(self, provider: LLMProvider):
        """根据提供商获取适配器类"""
        adapter_mapping = {
            LLMProvider.DEEPSEEK: DeepSeekAdapter,
            LLMProvider.OPENAI: OpenAIAdapter,
            LLMProvider.LOCAL: LocalModelAdapter,
            LLMProvider.GLM: GLMAdapter,
            LLMProvider.ANTHROPIC: MockAdapter,  # 需要实现
            LLMProvider.GOOGLE: MockAdapter,      # 需要实现
            LLMProvider.AZURE_OPENAI: MockAdapter, # 需要实现
            LLMProvider.HUGGINGFACE: MockAdapter,  # 需要实现
            LLMProvider.OLLAMA: MockAdapter,        # 需要实现
            LLMProvider.ZHIPUAI: MockAdapter,      # 已有GLM，但保留兼容
            LLMProvider.QWEN: MockAdapter,         # 需要实现
        }
        return adapter_mapping.get(provider, MockAdapter)

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        adapter_id: Optional[str] = None,
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator]:
        """聊天完成

        Args:
            messages: 消息列表
            adapter_id: 适配器ID，None表示使用默认
            tools: 工具列表
            stream: 是否流式响应
            **kwargs: 其他参数

        Returns:
            LLM响应或响应流
        """
        adapter_id = adapter_id or self.default_adapter

        if not adapter_id:
            raise ValueError("No adapter specified and no default adapter available")

        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter {adapter_id} not found")

        adapter = self.adapters[adapter_id]

        try:
            return await adapter.chat_completion(
                messages=messages,
                tools=tools,
                stream=stream,
                **kwargs
            )

        except Exception as e:
            self.logger.error(f"Chat completion failed with adapter {adapter_id}: {e}")
            raise

    async def text_completion(
        self,
        prompt: str,
        adapter_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """文本完成

        Args:
            prompt: 提示词
            adapter_id: 适配器ID，None表示使用默认
            **kwargs: 其他参数

        Returns:
            LLM响应
        """
        adapter_id = adapter_id or self.default_adapter

        if not adapter_id:
            raise ValueError("No adapter specified and no default adapter available")

        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter {adapter_id} not found")

        adapter = self.adapters[adapter_id]

        try:
            return await adapter.text_completion(prompt=prompt, **kwargs)

        except Exception as e:
            self.logger.error(f"Text completion failed with adapter {adapter_id}: {e}")
            raise

    def create_session(self, session_id: str, messages: Optional[List[LLMMessage]] = None) -> None:
        """创建聊天会话

        Args:
            session_id: 会话ID
            messages: 初始消息列表
        """
        self.sessions[session_id] = messages or []

    def add_message(self, session_id: str, message: LLMMessage) -> None:
        """添加消息到会话

        Args:
            session_id: 会话ID
            message: 消息
        """
        if session_id not in self.sessions:
            self.create_session(session_id)

        self.sessions[session_id].append(message)

    def get_session_messages(self, session_id: str) -> List[LLMMessage]:
        """获取会话消息

        Args:
            session_id: 会话ID

        Returns:
            消息列表
        """
        return self.sessions.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        """清空会话

        Args:
            session_id: 会话ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_adapter(self, adapter_id: str) -> Optional[BaseLLMAdapter]:
        """获取适配器

        Args:
            adapter_id: 适配器ID

        Returns:
            适配器实例或None
        """
        return self.adapters.get(adapter_id)

    def get_adapter_info(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """获取适配器信息

        Args:
            adapter_id: 适配器ID

        Returns:
            适配器信息字典
        """
        adapter = self.get_adapter(adapter_id)
        if not adapter:
            return None

        return {
            "adapter_id": adapter_id,
            "config": adapter.config.to_dict(),
            "is_default": adapter_id == self.default_adapter,
            "metrics": adapter.get_metrics().to_dict()
        }

    def list_adapters(self) -> List[Dict[str, Any]]:
        """列出所有适配器

        Returns:
            适配器信息列表
        """
        return [self.get_adapter_info(adapter_id) for adapter_id in self.adapters]

    def get_default_adapter(self) -> Optional[str]:
        """获取默认适配器ID

        Returns:
            默认适配器ID或None
        """
        return self.default_adapter

    async def set_default_adapter(self, adapter_id: str) -> bool:
        """设置默认适配器

        Args:
            adapter_id: 适配器ID

        Returns:
            是否设置成功
        """
        if adapter_id not in self.adapters:
            self.logger.error(f"Adapter {adapter_id} not found")
            return False

        self.default_adapter = adapter_id
        self.logger.info(f"Set default adapter: {adapter_id}")
        return True

    async def validate_adapter(self, adapter_id: str) -> bool:
        """验证适配器连接

        Args:
            adapter_id: 适配器ID

        Returns:
            是否验证成功
        """
        adapter = self.get_adapter(adapter_id)
        if not adapter:
            return False

        try:
            return await adapter.validate_connection()
        except Exception as e:
            self.logger.error(f"Validation failed for adapter {adapter_id}: {e}")
            return False

    async def validate_all_adapters(self) -> Dict[str, bool]:
        """验证所有适配器连接

        Returns:
            验证结果字典
        """
        results = {}

        for adapter_id in self.adapters:
            results[adapter_id] = await self.validate_adapter(adapter_id)

        return results

    async def cleanup(self) -> None:
        """清理所有适配器资源"""
        cleanup_tasks = []

        for adapter_id, adapter in self.adapters.items():
            task = asyncio.create_task(adapter.cleanup())
            cleanup_tasks.append(task)

        # 等待所有清理任务完成
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        self.adapters.clear()
        self.default_adapter = None
        self.sessions.clear()

        self.logger.info("LLM manager cleaned up")

    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息

        Returns:
            统计信息字典
        """
        adapter_stats = {}
        total_requests = 0
        total_tokens = 0
        successful_requests = 0

        for adapter_id, adapter in self.adapters.items():
            metrics = adapter.get_metrics()
            adapter_stats[adapter_id] = {
                "provider": metrics.provider.value,
                "model": metrics.model,
                "total_requests": metrics.total_requests,
                "success_rate": metrics.success_rate,
                "average_response_time": metrics.average_response_time
            }

            total_requests += metrics.total_requests
            total_tokens += metrics.total_tokens_used
            successful_requests += metrics.successful_requests

        overall_success_rate = successful_requests / total_requests if total_requests > 0 else 0

        return {
            "total_adapters": len(self.adapters),
            "default_adapter": self.default_adapter,
            "adapter_stats": adapter_stats,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "overall_success_rate": overall_success_rate,
            "active_sessions": len(self.sessions)
        }


# 全局LLM管理器实例
global_llm_manager = LLMManager()


def get_llm_manager() -> LLMManager:
    """获取全局LLM管理器"""
    return global_llm_manager


# 便利函数
async def register_llm_adapter(adapter_id: str, config: LLMConfig, is_default: bool = False) -> bool:
    """注册LLM适配器的便利函数"""
    return await global_llm_manager.create_adapter(adapter_id, config, is_default)


async def chat_with_llm(
    messages: List[LLMMessage],
    adapter_id: Optional[str] = None,
    **kwargs
) -> Union[LLMResponse, AsyncGenerator]:
    """与LLM聊天的便利函数"""
    return await global_llm_manager.chat_completion(messages, adapter_id, **kwargs)


async def text_with_llm(
    prompt: str,
    adapter_id: Optional[str] = None,
    **kwargs
) -> LLMResponse:
    """文本完成的便利函数"""
    return await global_llm_manager.text_completion(prompt, adapter_id, **kwargs)