"""Local Model LLM Adapter

This module provides local model integration for the LLM system.
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Union, AsyncGenerator

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import BaseLLMAdapter
from ..types import (
    LLMMessage,
    LLMResponse,
    LLMConfig,
    LLMTool,
    LLMProvider,
    LLMCapability
)


class LocalModelAdapter(BaseLLMAdapter):
    """本地模型适配器，使用OpenAI兼容格式连接本地服务"""

    def __init__(self, config: LLMConfig):
        """初始化本地模型适配器

        Args:
            config: LLM配置
        """
        super().__init__(config)
        self.client = None
        self.base_url = config.api_base or "http://localhost:8080/v1"

    async def initialize(self) -> bool:
        """初始化本地模型适配器"""
        try:
            # 创建OpenAI兼容的客户端连接本地服务
            self.client = openai.AsyncOpenAI(
                api_key="local-key",  # 本地服务可以任意key
                base_url=self.base_url,
                timeout=self.config.timeout
            )

            # 验证连接
            connection_valid = await self.validate_connection()
            if not connection_valid:
                self.logger.error("Failed to validate local model connection")
                return False

            self._client = "local_client"
            self.logger.info(f"Local model adapter initialized with model: {self.model}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize local model adapter: {e}")
            return False

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator]:
        """本地模型聊天完成"""
        if not self.is_initialized:
            raise RuntimeError("Local model adapter not initialized")

        # 准备请求参数
        request_params = {
            "model": self.model,
            "messages": self.format_messages(messages),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "stream": stream,
            **self.config.extra_params,
            **kwargs
        }

        # 添加工具支持（如果本地模型支持）
        if tools:
            request_params["functions"] = self.format_tools(tools)

        async def execute_request():
            response = await self.client.chat.completions.create(**request_params)
            return response

        if stream:
            return await self._handle_stream_response(
                await self.execute_with_retry(execute_request)
            )
        else:
            return await self._handle_completion_response(
                await self.execute_with_retry(execute_request)
            )

    async def text_completion(
        self,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """本地模型文本完成"""
        if not self.is_initialized:
            raise RuntimeError("Local model adapter not initialized")

        # 将提示词转换为消息格式
        messages = [LLMMessage(role="user", content=prompt)]

        return await self.chat_completion(messages, **kwargs)

    async def validate_connection(self) -> bool:
        """验证本地模型连接"""
        try:
            if not self.client:
                return False

            # 发送简单的请求验证连接
            response = await self.client.models.list()
            return True

        except Exception as e:
            self.logger.error(f"Local model connection validation failed: {e}")
            return False

    async def _handle_completion_response(self, response) -> LLMResponse:
        """处理完成响应"""
        response_time = time.time()

        # 解析响应
        choice = response.choices[0]
        content = choice.message.content
        finish_reason = choice.finish_reason

        # 解析工具调用（如果支持）
        tool_calls = None
        if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
            tool_calls = [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in choice.message.tool_calls
            ]

        # 解析使用情况
        usage = response.usage.model_dump() if response.usage else {}

        return LLMResponse(
            content=content,
            model=response.model,
            provider=self.provider,
            usage=usage,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            response_time=response_time - self.config.timeout,
            metadata={
                "response_id": response.id,
                "created": response.created,
                "local_service_url": self.base_url
            }
        )

    async def _handle_stream_response(self, response) -> AsyncGenerator:
        """处理流式响应"""
        buffer = ""

        async for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    content = delta.content
                    buffer += content
                    yield content

    async def cleanup(self) -> None:
        """清理本地模型资源"""
        if self.client:
            await self.client.close()
            self.client = None
        self._client = None
        self.logger.info("Local model adapter cleaned up")

    def get_supported_capabilities(self) -> List[LLMCapability]:
        """获取支持的能力"""
        # 本地模型能力取决于具体模型，这里返回通用能力
        capabilities = [
            LLMCapability.TEXT_GENERATION,
            LLMCapability.ANALYSIS,
            LLMCapability.REASONING,
            LLMCapability.CONVERSATION,
            LLMCapability.STREAMING
        ]

        # 工具调用支持取决于本地模型
        if "tool" in self.model.lower():
            capabilities.extend([
                LLMCapability.TOOL_CALLING,
                LLMCapability.FUNCTION_CALLING
            ])

        return capabilities

    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        base_info = await super().get_model_info()
        base_info.update({
            "capabilities": [cap.value for cap in self.get_supported_capabilities()],
            "supports_streaming": True,
            "supports_tools": "tool" in self.model.lower(),
            "provider_name": "Local Model",
            "service_url": self.base_url
        })
        return base_info