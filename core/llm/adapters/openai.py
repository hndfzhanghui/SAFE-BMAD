"""OpenAI LLM Adapter

This module provides OpenAI API integration for the LLM system.
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


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI API适配器"""

    def __init__(self, config: LLMConfig):
        """初始化OpenAI适配器

        Args:
            config: LLM配置
        """
        super().__init__(config)
        self.client = None
        self._validate_openai_import()

    def _validate_openai_import(self) -> None:
        """验证OpenAI库导入"""
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI library not found. Install with: pip install openai"
            )

    async def initialize(self) -> bool:
        """初始化OpenAI适配器"""
        try:
            # 创建OpenAI客户端
            self.client = openai.AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                timeout=self.config.timeout
            )

            # 验证连接
            connection_valid = await self.validate_connection()
            if not connection_valid:
                self.logger.error("Failed to validate OpenAI API connection")
                return False

            self._client = "openai_client"
            self.logger.info(f"OpenAI adapter initialized with model: {self.model}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI adapter: {e}")
            return False

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator]:
        """OpenAI聊天完成"""
        if not self.is_initialized:
            raise RuntimeError("OpenAI adapter not initialized")

        # 准备请求参数
        request_params = {
            "model": self.model,
            "messages": self.format_messages(messages),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
            "stream": stream,
            **self.config.extra_params,
            **kwargs
        }

        # 添加工具支持
        if tools and self._supports_tool_calling():
            request_params["functions"] = self.format_tools(tools)
            if "function_call" not in kwargs:
                request_params["function_call"] = "auto"

        # 合并额外参数
        request_params.update(kwargs)

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
        """OpenAI文本完成"""
        if not self.is_initialized:
            raise RuntimeError("OpenAI adapter not initialized")

        # 将提示词转换为消息格式
        messages = [LLMMessage(role="user", content=prompt)]

        return await self.chat_completion(messages, **kwargs)

    async def validate_connection(self) -> bool:
        """验证OpenAI连接"""
        try:
            if not self.client:
                return False

            # 发送简单的请求验证API密钥
            response = await self.client.models.list()
            return True

        except Exception as e:
            self.logger.error(f"OpenAI connection validation failed: {e}")
            return False

    def _supports_tool_calling(self) -> bool:
        """检查是否支持工具调用"""
        supported_models = [
            "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
        ]
        return any(model in self.model.lower() for model in supported_models)

    async def _handle_completion_response(self, response) -> LLMResponse:
        """处理完成响应"""
        response_time = time.time()

        # 解析响应
        choice = response.choices[0]
        content = choice.message.content
        finish_reason = choice.finish_reason

        # 解析工具调用
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
                "system_fingerprint": response.system_fingerprint
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
        """清理OpenAI资源"""
        if self.client:
            await self.client.close()
            self.client = None
        self._client = None
        self.logger.info("OpenAI adapter cleaned up")

    def get_supported_capabilities(self) -> List[LLMCapability]:
        """获取支持的能力"""
        capabilities = [
            LLMCapability.TEXT_GENERATION,
            LLMCapability.ANALYSIS,
            LLMCapability.REASONING,
            LLMCapability.CONVERSATION,
            LLMCapability.CODE_GENERATION,
            LLMCapability.STREAMING
        ]

        if self._supports_tool_calling():
            capabilities.extend([
                LLMCapability.TOOL_CALLING,
                LLMCapability.FUNCTION_CALLING
            ])

        # JSON模式支持
        json_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        if any(model in self.model.lower() for model in json_models):
            capabilities.append(LLMCapability.JSON_MODE)

        return capabilities

    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        base_info = await super().get_model_info()
        base_info.update({
            "capabilities": [cap.value for cap in self.get_supported_capabilities()],
            "supports_streaming": True,
            "supports_tools": self._supports_tool_calling(),
            "provider_name": "OpenAI"
        })
        return base_info