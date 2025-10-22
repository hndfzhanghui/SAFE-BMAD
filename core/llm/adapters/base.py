"""Base LLM Adapter

This module defines the base class for all LLM adapters.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from ..types import (
    LLMMessage,
    LLMResponse,
    LLMConfig,
    LLMTool,
    LLMChatSession,
    LLMProvider,
    LLMMetrics
)


class BaseLLMAdapter(ABC):
    """LLM适配器基类"""

    def __init__(self, config: LLMConfig):
        """初始化LLM适配器

        Args:
            config: LLM配置
        """
        self.config = config
        self.provider = config.provider
        self.model = config.model
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.provider.value}")
        self.metrics = LLMMetrics(provider=self.provider, model=self.model)
        self._client = None

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化适配器

        Returns:
            是否初始化成功
        """
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator]:
        """聊天完成

        Args:
            messages: 消息列表
            tools: 可用工具列表
            stream: 是否流式响应
            **kwargs: 其他参数

        Returns:
            LLM响应或响应流
        """
        pass

    @abstractmethod
    async def text_completion(
        self,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """文本完成

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            LLM响应
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """验证连接

        Returns:
            连接是否有效
        """
        pass

    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息

        Returns:
            模型信息字典
        """
        return {
            "provider": self.provider.value,
            "model": self.model,
            "config": self.config.to_dict()
        }

    def format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """格式化消息为标准格式

        Args:
            messages: LLM消息列表

        Returns:
            标准格式的消息列表
        """
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": msg.role,
                "content": msg.content
            }
            if msg.name:
                formatted_msg["name"] = msg.name
            if msg.tool_calls:
                formatted_msg["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                formatted_msg["tool_call_id"] = msg.tool_call_id
            formatted_messages.append(formatted_msg)
        return formatted_messages

    def format_tools(self, tools: Optional[List[LLMTool]]) -> Optional[List[Dict[str, Any]]]:
        """格式化工具为标准格式

        Args:
            tools: 工具列表

        Returns:
            格式化的工具列表
        """
        if not tools:
            return None
        return [tool.to_openai_format() for tool in tools]

    async def execute_with_retry(
        self,
        func: callable,
        *args,
        **kwargs
    ) -> Any:
        """带重试的执行

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            执行结果
        """
        last_exception = None

        for attempt in range(self.config.retry_count):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_count - 1:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying..."
                    )
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    self.logger.error(
                        f"All {self.config.retry_count} attempts failed"
                    )

        # 记录失败指标
        self.metrics.update_failure()
        raise last_exception

    async def measure_response_time(
        self,
        func: callable,
        *args,
        **kwargs
    ) -> Any:
        """测量响应时间

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            执行结果
        """
        import time
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            response_time = time.time() - start_time

            # 更新成功指标
            if hasattr(result, 'usage'):
                self.metrics.update_success(response_time, result.usage)
            else:
                self.metrics.update_success(response_time)

            return result
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.update_failure()
            raise e

    def get_metrics(self) -> LLMMetrics:
        """获取使用指标

        Returns:
            指标对象
        """
        return self.metrics

    async def cleanup(self) -> None:
        """清理资源"""
        if self._client:
            # 子类应该重写此方法来清理客户端资源
            pass

    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._client is not None


class MockAdapter(BaseLLMAdapter):
    """模拟适配器，用于测试"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._initialized = False

    async def initialize(self) -> bool:
        """初始化模拟适配器"""
        self._client = "mock_client"
        self._initialized = True
        self.logger.info(f"Mock adapter for {self.provider.value} initialized")
        return True

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator]:
        """模拟聊天完成"""
        await asyncio.sleep(0.1)  # 模拟网络延迟

        last_message = messages[-1] if messages else None
        if last_message and last_message.role == "user":
            content = f"Mock response to: {last_message.content}"
        else:
            content = "Mock response"

        response = LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            usage={"total_tokens": 100},
            finish_reason="stop",
            response_time=0.1
        )

        if stream:
            # 简单的流式响应模拟
            async def stream_generator():
                words = content.split()
                for word in words:
                    yield word + " "
                    await asyncio.sleep(0.05)
            return stream_generator()
        else:
            return response

    async def text_completion(self, prompt: str, **kwargs) -> LLMResponse:
        """模拟文本完成"""
        return await self.chat_completion([
            LLMMessage(role="user", content=prompt)
        ])

    async def validate_connection(self) -> bool:
        """验证模拟连接"""
        return self._initialized

    async def cleanup(self) -> None:
        """清理模拟资源"""
        self._client = None
        self._initialized = False