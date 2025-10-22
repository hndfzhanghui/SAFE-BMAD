"""GLM (Zhipu AI) Adapter

This module provides adapter for GLM API from Zhipu AI.
GLM models include:
- glm-4: Latest generation model
- glm-3-turbo: Efficient model for fast responses
- glm-4v: Multimodal model with vision capabilities
- glm-4-long: Extended context model
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
import json
import httpx
from datetime import datetime

from .base import BaseLLMAdapter
from ..types import (
    LLMResponse,
    LLMMessage,
    LLMConfig,
    LLMTool,
    LLMCapability
)


class GLMAdapter(BaseLLMAdapter):
    """GLM (Zhipu AI) API Adapter"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url = config.api_base or "https://open.bigmodel.cn/api/paas/v4"
        self.model = config.model or "glm-4"
        self.client: Optional[httpx.AsyncClient] = None
        self.logger = logging.getLogger(f"GLMAdapter.{config.model}")

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.config.timeout or 60.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            self.logger.info(f"GLM adapter initialized for model: {self.model}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize GLM adapter: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        if self.client:
            await self.client.aclose()
            self.client = None

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """转换消息格式"""
        converted = []

        for message in messages:
            msg_dict = {
                "role": message.role,
                "content": message.content
            }

            # 添加工具调用结果
            if message.tool_call_id:
                msg_dict["tool_call_id"] = message.tool_call_id
            if message.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]

            converted.append(msg_dict)

        return converted

    def _convert_tools(self, tools: List[LLMTool]) -> List[Dict[str, Any]]:
        """转换工具格式"""
        converted = []

        for tool in tools:
            converted.append({
                "type": "function",
                "function": {
                    "name": tool.function.name,
                    "description": tool.function.description,
                    "parameters": tool.function.parameters
                }
            })

        return converted

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        """聊天对话"""
        if not self.client:
            raise RuntimeError("GLM adapter not initialized")

        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature or self.config.temperature or 0.7,
            "max_tokens": max_tokens or self.config.max_tokens or 4096,
            "stream": stream
        }

        # 添加工具
        if tools:
            payload["tools"] = self._convert_tools(tools)

        # 添加响应格式 - 使用extra_params检查
        response_format = self.config.extra_params.get("response_format", "text")
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        start_time = datetime.now()

        try:
            if stream:
                return await self._handle_stream_response(payload, start_time)
            else:
                return await self._handle_regular_response(payload, start_time)

        except httpx.HTTPStatusError as e:
            self.logger.error(f"GLM API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"GLM API error: {e}")
            raise

    async def _handle_regular_response(
        self,
        payload: Dict[str, Any],
        start_time: datetime
    ) -> LLMResponse:
        """处理常规响应"""
        response = await self.client.post(
            "/chat/completions",
            json=payload,
            headers=self._get_headers()
        )
        response.raise_for_status()

        data = response.json()
        end_time = datetime.now()

        # 提取消息
        choice = data["choices"][0]
        message = choice["message"]

        # 转换工具调用
        tool_calls = []
        if "tool_calls" in message and message["tool_calls"]:
            tool_calls = message["tool_calls"]

        return LLMResponse(
            content=message.get("content", ""),
            model=data.get("model", self.model),
            provider=self.config.provider,
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage", {}),
            response_time=(end_time - start_time).total_seconds()
        )

    async def _handle_stream_response(
        self,
        payload: Dict[str, Any],
        start_time: datetime
    ) -> LLMResponse:
        """处理流式响应"""
        response = await self.client.post(
            "/chat/completions",
            json=payload,
            headers=self._get_headers()
        )
        response.raise_for_status()

        content = ""
        tool_calls = []
        finish_reason = None
        usage = {}

        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]  # 移除 "data: " 前缀
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    if "choices" in data and data["choices"]:
                        choice = data["choices"][0]
                        delta = choice.get("delta", {})

                        # 累积内容
                        if "content" in delta:
                            content += delta["content"]

                        # 处理工具调用
                        if "tool_calls" in delta:
                            for tc_delta in delta["tool_calls"]:
                                if "index" not in tc_delta:
                                    continue

                                index = tc_delta["index"]
                                # 确保有足够的位置
                                while len(tool_calls) <= index:
                                    tool_calls.append({
                                        "id": "",
                                        "function": {"name": "", "arguments": ""}
                                    })

                                if "id" in tc_delta:
                                    tool_calls[index]["id"] = tc_delta["id"]
                                if "function" in tc_delta:
                                    func = tc_delta["function"]
                                    if "name" in func:
                                        tool_calls[index]["function"]["name"] = func["name"]
                                    if "arguments" in func:
                                        tool_calls[index]["function"]["arguments"] += func["arguments"]

                        finish_reason = choice.get("finish_reason")

                except json.JSONDecodeError:
                    continue

        # 转换工具调用格式
        formatted_tool_calls = []
        for tc in tool_calls:
            if tc.get("id") or tc.get("function", {}).get("name"):
                formatted_tool_calls.append(tc)

        end_time = datetime.now()

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.config.provider,
            tool_calls=formatted_tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            response_time=(end_time - start_time).total_seconds()
        )

    async def text_completion(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """文本补全"""
        messages = [LLMMessage(role="user", content=prompt)]
        return await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def validate_connection(self) -> bool:
        """验证连接"""
        if not self.client:
            return False

        try:
            # 发送简单的测试请求
            test_messages = [
                {"role": "user", "content": "Hi"}
            ]

            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": test_messages,
                    "max_tokens": 10
                },
                headers=self._get_headers()
            )

            if response.status_code == 200:
                self.logger.info("GLM API connection validated successfully")
                return True
            else:
                self.logger.error(f"GLM API validation failed: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"GLM API validation error: {e}")
            return False

    def get_supported_capabilities(self) -> List[LLMCapability]:
        """获取支持的能力"""
        capabilities = [
            LLMCapability.TEXT_GENERATION,
            LLMCapability.CONVERSATION,
            LLMCapability.STREAMING
        ]

        # 根据模型添加特定能力
        if self.model == "glm-4":
            capabilities.extend([
                LLMCapability.CODE_GENERATION,
                LLMCapability.ANALYSIS,
                LLMCapability.REASONING,
                LLMCapability.FUNCTION_CALLING,
                LLMCapability.JSON_MODE
            ])
        elif "v" in self.model:  # glm-4v
            capabilities.append(LLMCapability.MULTIMODAL)
        elif "long" in self.model:  # glm-4-long
            capabilities.extend([
                LLMCapability.ANALYSIS,
                LLMCapability.REASONING
            ])

        return capabilities

    def _supports_function_calling(self) -> bool:
        """是否支持函数调用"""
        return self.model == "glm-4"

    def _supports_multimodal(self) -> bool:
        """是否支持多模态"""
        return "v" in self.model

    def _supports_streaming(self) -> bool:
        """是否支持流式响应"""
        return True

    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        base_info = await super().get_model_info()
        base_info.update({
            "capabilities": [cap.value for cap in self.get_supported_capabilities()],
            "supports_streaming": self._supports_streaming(),
            "supports_tools": self._supports_function_calling(),
            "supports_multimodal": self._supports_multimodal(),
            "base_url": self.base_url,
            "provider_name": "GLM (Zhipu AI)"
        })
        return base_info