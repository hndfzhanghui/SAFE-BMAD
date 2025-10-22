"""DeepSeek LLM Adapter

This module provides DeepSeek API integration for the LLM system.
"""

import asyncio
import json
import time
import httpx
from typing import List, Dict, Any, Optional, Union, AsyncGenerator

from .base import BaseLLMAdapter
from ..types import (
    LLMMessage,
    LLMResponse,
    LLMConfig,
    LLMTool,
    LLMProvider,
    LLMCapability
)


class DeepSeekAdapter(BaseLLMAdapter):
    """DeepSeek API适配器"""

    def __init__(self, config: LLMConfig):
        """初始化DeepSeek适配器

        Args:
            config: LLM配置
        """
        super().__init__(config)
        self.client = None
        self.base_url = config.api_base or "https://api.deepseek.com/v1"
        self.session = None

    async def initialize(self) -> bool:
        """初始化DeepSeek适配器"""
        try:
            # 创建HTTP客户端
            self.session = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=self.config.timeout
            )

            # 验证连接
            connection_valid = await self.validate_connection()
            if not connection_valid:
                self.logger.error("Failed to validate DeepSeek API connection")
                return False

            self._client = "deepseek_client"
            self.logger.info(f"DeepSeek adapter initialized with model: {self.model}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize DeepSeek adapter: {e}")
            return False

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator]:
        """DeepSeek聊天完成"""
        if not self.is_initialized:
            raise RuntimeError("DeepSeek adapter not initialized")

        # 准备请求参数
        request_data = {
            "model": self.model,
            "messages": self.format_messages(messages),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
            "stream": stream,
            **self.config.extra_params
        }

        # 添加工具支持
        if tools and self._supports_tool_calling():
            request_data["tools"] = self.format_tools(tools)
            if "tool_choice" not in kwargs:
                request_data["tool_choice"] = "auto"

        # 合并额外参数
        request_data.update(kwargs)

        async def execute_request():
            response = await self.session.post(
                "/chat/completions",
                json=request_data
            )
            response.raise_for_status()
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
        """DeepSeek文本完成"""
        if not self.is_initialized:
            raise RuntimeError("DeepSeek adapter not initialized")

        # 将提示词转换为消息格式
        messages = [LLMMessage(role="user", content=prompt)]

        return await self.chat_completion(messages, **kwargs)

    async def validate_connection(self) -> bool:
        """验证DeepSeek连接"""
        try:
            if not self.session:
                return False

            # 发送简单的请求验证API密钥
            response = await self.session.get(
                "/models",
                timeout=10
            )
            return response.status_code == 200

        except Exception as e:
            self.logger.error(f"DeepSeek connection validation failed: {e}")
            return False

    def _supports_tool_calling(self) -> bool:
        """检查是否支持工具调用"""
        supported_models = ["deepseek-chat", "deepseek-coder"]
        return any(model in self.model.lower() for model in supported_models)

    async def _handle_completion_response(self, response: httpx.Response) -> LLMResponse:
        """处理完成响应"""
        response_data = response.json()
        response_time = time.time()

        # 解析响应
        choice = response_data["choices"][0]
        content = choice["message"]["content"]
        finish_reason = choice.get("finish_reason", "stop")

        # 解析工具调用
        tool_calls = None
        if "tool_calls" in choice["message"]:
            tool_calls = choice["message"]["tool_calls"]

        # 解析使用情况
        usage = response_data.get("usage", {})

        return LLMResponse(
            content=content,
            model=response_data["model"],
            provider=self.provider,
            usage=usage,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            response_time=response_time - self.config.timeout,
            metadata={
                "response_id": response_data.get("id"),
                "created": response_data.get("created"),
                "system_fingerprint": response_data.get("system_fingerprint")
            }
        )

    async def _handle_stream_response(self, response: httpx.Response) -> AsyncGenerator:
        """处理流式响应"""
        buffer = ""

        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]  # 移除 "data: " 前缀
                if data_str.strip() == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0]["delta"]
                        if "content" in delta:
                            content = delta["content"]
                            buffer += content
                            yield content
                except json.JSONDecodeError:
                    continue

    async def cleanup(self) -> None:
        """清理DeepSeek资源"""
        if self.session:
            await self.session.aclose()
            self.session = None
        self._client = None
        self.logger.info("DeepSeek adapter cleaned up")

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

        return capabilities

    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        base_info = await super().get_model_info()
        base_info.update({
            "capabilities": [cap.value for cap in self.get_supported_capabilities()],
            "supports_streaming": True,
            "supports_tools": self._supports_tool_calling(),
            "base_url": self.base_url,
            "provider_name": "DeepSeek"
        })
        return base_info