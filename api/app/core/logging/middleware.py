"""
日志中间件 - FastAPI请求日志记录
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_context_logger, get_performance_logger, generate_request_id


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""

    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求日志记录"""

        # 生成请求ID
        request_id = generate_request_id()

        # 添加到请求状态中，供其他中间件或路由使用
        request.state.request_id = request_id

        # 获取上下文日志记录器
        logger = get_context_logger(
            request_id=request_id,
            user_id=self._get_user_id(request),
            session_id=self._get_session_id(request)
        )

        # 记录请求开始时间
        start_time = time.time()

        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # 记录请求信息
        if self.log_requests:
            logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "content_type": request.headers.get("content-type", "unknown"),
                    "content_length": request.headers.get("content-length", "0")
                }
            )

        # 性能监控开始
        perf_logger = get_performance_logger(
            operation=f"{request.method} {request.url.path}",
            request_id=request_id,
            method=request.method,
            path=request.url.path
        )

        # 处理请求
        try:
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)

            # 设置响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time_ms)

            # 记录响应信息
            if self.log_responses:
                logger.info(
                    f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "process_time_ms": process_time_ms,
                        "response_size": getattr(response, 'headers', {}).get('content-length', 'unknown')
                    }
                )

            # 性能监控记录
            perf_logger.info(
                f"API request completed",
                extra={
                    "duration_ms": process_time_ms,
                    "status_code": response.status_code,
                    "status": "success" if response.status_code < 400 else "error",
                    "details": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code
                    }
                }
            )

            return response

        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)

            # 记录错误信息
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "process_time_ms": process_time_ms,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "client_ip": client_ip
                },
                exc_info=True
            )

            # 性能监控错误记录
            perf_logger.error(
                f"API request failed",
                extra={
                    "duration_ms": process_time_ms,
                    "status": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "details": {
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(e)
                    }
                }
            )

            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "request_id": request_id,
                    "timestamp": time.time()
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": str(process_time_ms)
                }
            )

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 返回直接连接的IP
        return request.client.host if request.client else "unknown"

    def _get_user_id(self, request: Request) -> str:
        """从请求中获取用户ID"""
        # 这里可以根据实际的认证机制来获取用户ID
        # 例如从JWT token中解析，或从session中获取
        if hasattr(request.state, 'user_id'):
            return request.state.user_id
        return "anonymous"

    def _get_session_id(self, request: Request) -> str:
        """从请求中获取会话ID"""
        # 这里可以根据实际的会话管理机制来获取会话ID
        if hasattr(request.state, 'session_id'):
            return request.state.session_id
        return "unknown"


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """安全日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理安全相关日志"""

        # 获取请求ID（如果已经由LoggingMiddleware设置）
        request_id = getattr(request.state, 'request_id', generate_request_id())

        # 获取审计日志记录器
        audit_logger = get_context_logger(
            request_id=request_id,
            user_id=self._get_user_id(request)
        ).bind(audit=True)

        # 记录敏感操作
        if self._is_sensitive_operation(request):
            audit_logger.info(
                f"Sensitive operation attempted: {request.method} {request.url.path}",
                extra={
                    "action": f"{request.method}_{request.url.path}",
                    "resource": request.url.path,
                    "ip_address": self._get_client_ip(request),
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "sensitive": True
                }
            )

        # 处理请求
        response = await call_next(request)

        # 记录认证失败
        if response.status_code == 401:
            audit_logger.warning(
                f"Authentication failed: {request.method} {request.url.path}",
                extra={
                    "action": "auth_failed",
                    "resource": request.url.path,
                    "ip_address": self._get_client_ip(request),
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "result": "failed"
                }
            )

        # 记录授权失败
        elif response.status_code == 403:
            audit_logger.warning(
                f"Authorization failed: {request.method} {request.url.path}",
                extra={
                    "action": "authz_failed",
                    "resource": request.url.path,
                    "ip_address": self._get_client_ip(request),
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "result": "failed"
                }
            )

        return response

    def _is_sensitive_operation(self, request: Request) -> bool:
        """判断是否为敏感操作"""
        sensitive_paths = [
            "/auth/login",
            "/auth/logout",
            "/auth/register",
            "/users/",
            "/admin/",
            "/config/",
            "/secrets/"
        ]

        return any(path in request.url.path for path in sensitive_paths)

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _get_user_id(self, request: Request) -> str:
        """从请求中获取用户ID"""
        if hasattr(request.state, 'user_id'):
            return request.state.user_id
        return "anonymous"