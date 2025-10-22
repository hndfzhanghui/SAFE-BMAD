#!/usr/bin/env python3
"""
LLM API 测试服务器
为前端提供LLM API调用服务
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, '/Users/huizhang/PycharmProjects/S3DA2/SAFE-BMAD')

# 加载环境变量
load_dotenv('/Users/huizhang/PycharmProjects/S3DA2/SAFE-BMAD/.env')

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from core.llm.types import LLMConfig, LLMProvider, LLMMessage
from core.llm.manager import get_llm_manager
from core.llm.adapters import DeepSeekAdapter, GLMAdapter, OpenAIAdapter


# 创建FastAPI应用
app = FastAPI(
    title="LLM API 测试平台",
    description="支持 DeepSeek、GLM、OpenAI 等多个大模型提供商",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
llm_manager = get_llm_manager()
active_connections = {}


class ChatRequest(BaseModel):
    """聊天请求模型"""
    provider: str
    message: str
    conversation_history: list = []
    temperature: float = 0.7
    max_tokens: int = 1000


class ChatResponse(BaseModel):
    """聊天响应模型"""
    success: bool
    content: str = None
    error: str = None
    metadata: dict = {}
    provider: str = None
    model: str = None
    response_time: float = None
    usage: dict = None


@app.get("/")
async def read_root():
    """返回前端页面"""
    try:
        # 读取HTML文件
        html_path = Path("/Users/huizhang/PycharmProjects/S3DA2/SAFE-BMAD/web/llm_test_frontend.html")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)

    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "前端页面未找到"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"服务器错误: {str(e)}"}
        )


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """处理聊天请求"""
    try:
        print(f"🔍 收到聊天请求: {request.provider} - {request.message[:50]}...")

        # 验证提供商
        if request.provider not in ["deepseek", "glm", "openai", "local"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的提供商: {request.provider}"
            )

        # 获取API密钥
        api_key = get_api_key(request.provider)
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail=f"未找到 {request.provider} 的API密钥"
            )

        # 创建或获取适配器
        adapter_id = f"chat_{request.provider}"

        # 检查是否已存在适配器
        if adapter_id not in active_connections:
            # 创建新适配器
            config = LLMConfig(
                provider=get_provider_enum(request.provider),
                model=get_default_model(request.provider),
                api_key=api_key,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

            success = await llm_manager.create_adapter(
                adapter_id=adapter_id,
                config=config,
                is_default=False
            )

            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=f"创建 {request.provider} 适配器失败"
                )

            active_connections[adapter_id] = {
                "created_at": datetime.now(),
                "provider": request.provider,
                "model": get_default_model(request.provider)
            }

            print(f"✅ 创建 {request.provider} 适配器成功")

        # 转换消息格式
        messages = []

        # 添加系统消息
        messages.append(LLMMessage(role="system", content="你是一个专业的AI助手，请提供准确、有用的回答。"))

        # 添加历史对话
        for hist_msg in request.conversation_history[-10:]:  # 限制历史长度
            if hist_msg.get("role") and hist_msg.get("content"):
                messages.append(LLMMessage(
                    role=hist_msg["role"],
                    content=hist_msg["content"]
                ))

        # 添加当前用户消息
        messages.append(LLMMessage(role="user", content=request.message))

        # 调用LLM
        start_time = datetime.now()

        try:
            response = await llm_manager.chat_completion(
                adapter_id=adapter_id,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            # 更新连接信息
            if adapter_id in active_connections:
                active_connections[adapter_id]["last_used"] = end_time
                active_connections[adapter_id]["request_count"] = active_connections[adapter_id].get("request_count", 0) + 1

            print(f"✅ {request.provider} 响应成功: {response.content[:100] if response.content else 'None'}...")

            return ChatResponse(
                success=True,
                content=response.content,
                provider=request.provider,
                model=get_default_model(request.provider),
                response_time=response_time,
                usage=response.usage,
                metadata={
                    "adapter_id": adapter_id,
                    "total_messages": len(messages),
                    "timestamp": end_time.isoformat()
                }
            )

        except Exception as llm_error:
            end_time = datetime.now()
            error_response = str(llm_error)
            response_time = (end_time - start_time).total_seconds()

            print(f"❌ {request.provider} LLM调用失败: {error_response}")

            return ChatResponse(
                success=False,
                error=error_response,
                provider=request.provider,
                response_time=response_time,
                metadata={
                    "error_type": type(llm_error).__name__,
                    "timestamp": end_time.isoformat()
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 服务器错误: {str(e)}")
        return ChatResponse(
            success=False,
            error=f"服务器内部错误: {str(e)}",
            provider=request.provider,
            response_time=0.0,
            metadata={
                "error_type": "server_error",
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "status": "running",
        "providers": {
            "deepseek": {
                "available": bool(os.getenv("DEEPSEEK_API_KEY")),
                "name": "DeepSeek",
                "models": ["deepseek-chat", "deepseek-coder"]
            },
            "glm": {
                "available": bool(os.getenv("GLM_API_KEY")),
                "name": "GLM (智谱AI)",
                "models": ["glm-4", "glm-3-turbo", "glm-4v"]
            },
            "openai": {
                "available": bool(os.getenv("OPENAI_API_KEY")),
                "name": "OpenAI",
                "models": ["gpt-4", "gpt-3.5-turbo"]
            },
            "local": {
                "available": False,  # 需要本地服务运行
                "name": "Local Model",
                "models": ["local-chat", "local-coder"]
            }
        },
        "active_connections": len(active_connections),
        "connection_details": active_connections,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/models/{provider}")
async def get_provider_models(provider: str):
    """获取指定提供商的模型列表"""
    try:
        from core.llm.types import get_available_models, get_model_info, LLMProvider

        if provider not in ["deepseek", "glm", "openai", "local"]:
            raise HTTPException(status_code=404, detail="提供商未找到")

        provider_enum = get_provider_enum(provider)
        models = get_available_models(provider_enum)

        model_details = []
        for model in models:
            model_info = get_model_info(provider_enum, model)
            if model_info:
                model_details.append({
                    "name": model,
                    "description": model_info.get("description", ""),
                    "capabilities": [cap.value for cap in model_info.get("capabilities", [])],
                    "max_tokens": model_info.get("max_tokens", 0)
                })

        return {
            "provider": provider,
            "models": model_details
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


# 辅助函数
def get_api_key(provider: str) -> str:
    """获取API密钥"""
    env_mappings = {
        "deepseek": "DEEPSEEK_API_KEY",
        "glm": "GLM_API_KEY",
        "openai": "OPENAI_API_KEY",
        "local": "LOCAL_API_KEY"
    }

    env_key = env_mappings.get(provider)
    return os.getenv(env_key) if env_key else None


def get_provider_enum(provider: str) -> LLMProvider:
    """获取提供商枚举"""
    provider_mappings = {
        "deepseek": LLMProvider.DEEPSEEK,
        "glm": LLMProvider.GLM,
        "openai": LLMProvider.OPENAI,
        "local": LLMProvider.LOCAL
    }
    return provider_mappings.get(provider)


def get_default_model(provider: str) -> str:
    """获取默认模型"""
    default_models = {
        "deepseek": "deepseek-chat",
        "glm": "glm-4",
        "openai": "gpt-3.5-turbo",
        "local": "local-chat"
    }
    return default_models.get(provider, "deepseek-chat")


# 启动服务器
if __name__ == "__main__":
    print("🚀 启动LLM API测试服务器...")
    print(f"📍 服务地址: http://localhost:8000")
    print(f"🌐 前端页面: http://localhost:8000")
    print(f"📋 API文档: http://localhost:8000/docs")
    print(f"🔑 API状态: http://localhost:8000/api/status")
    print("=" * 50)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )