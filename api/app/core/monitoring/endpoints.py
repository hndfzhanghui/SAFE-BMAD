"""
监控端点 - 健康检查和指标暴露API端点
"""

import time
import asyncio
import os
import socket
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Response, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from .health import health_checker, HealthStatus, HealthCheckResult
from .metrics import metrics_collector
from ..logging.config import get_context_logger, get_performance_logger

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check(request: Request):
    """
    基础健康检查端点

    Returns:
        基础的系统健康状态
    """
    start_time = time.time()
    perf_logger = get_performance_logger("health_check", request_id=getattr(request.state, 'request_id', None))

    try:
        # 获取主要组件的健康状态
        key_checks = {
            "api": await _check_api_health(),
            "system_resources": await health_checker.check_system_resources()
        }

        overall_status = health_checker.get_overall_status(key_checks)
        response_time = (time.time() - start_time) * 1000

        result = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.4.0",
            "checks": {name: {
                "status": check.status.value,
                "message": check.message,
                "response_time_ms": check.response_time_ms
            } for name, check in key_checks.items()},
            "response_time_ms": round(response_time, 2)
        }

        perf_logger.info("Health check completed", extra={
            "duration_ms": response_time,
            "status": overall_status.value,
            "details": {"checks_count": len(key_checks)}
        })

        return result

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        perf_logger.error(f"Health check failed: {str(e)}", extra={
            "duration_ms": response_time,
            "status": "error",
            "error": str(e)
        })

        return {
            "status": HealthStatus.UNHEALTHY.value,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.4.0",
            "error": str(e),
            "response_time_ms": round(response_time, 2)
        }


@router.get("/ready")
async def readiness_check(request: Request):
    """
    就绪状态检查端点

    Returns:
        详细的系统组件就绪状态
    """
    start_time = time.time()
    perf_logger = get_performance_logger("readiness_check", request_id=getattr(request.state, 'request_id', None))

    try:
        # 获取所有组件的就绪状态
        checks = await health_checker.check_all()
        overall_status = health_checker.get_overall_status(checks)
        response_time = (time.time() - start_time) * 1000

        # 转换检查结果为字典格式
        checks_dict = {}
        for name, check in checks.items():
            checks_dict[name] = {
                "status": check.status.value,
                "message": check.message,
                "details": check.details,
                "response_time_ms": check.response_time_ms,
                "check_time": check.check_time.isoformat()
            }

        result = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.4.0",
            "ready": overall_status == HealthStatus.HEALTHY,
            "checks": checks_dict,
            "summary": {
                "total_checks": len(checks),
                "healthy": len([c for c in checks.values() if c.status == HealthStatus.HEALTHY]),
                "degraded": len([c for c in checks.values() if c.status == HealthStatus.DEGRADED]),
                "unhealthy": len([c for c in checks.values() if c.status == HealthStatus.UNHEALTHY]),
                "unknown": len([c for c in checks.values() if c.status == HealthStatus.UNKNOWN])
            },
            "response_time_ms": round(response_time, 2)
        }

        perf_logger.info("Readiness check completed", extra={
            "duration_ms": response_time,
            "status": overall_status.value,
            "details": {
                "ready": overall_status == HealthStatus.HEALTHY,
                "total_checks": len(checks)
            }
        })

        # 如果不是健康状态，返回503
        if overall_status != HealthStatus.HEALTHY:
            raise HTTPException(status_code=503, detail=result)

        return result

    except HTTPException:
        raise
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        perf_logger.error(f"Readiness check failed: {str(e)}", extra={
            "duration_ms": response_time,
            "status": "error",
            "error": str(e)
        })

        raise HTTPException(status_code=503, detail={
            "status": HealthStatus.UNHEALTHY.value,
            "timestamp": datetime.utcnow().isoformat(),
            "ready": False,
            "error": str(e),
            "response_time_ms": round(response_time, 2)
        })


@router.get("/live")
async def liveness_check(request: Request):
    """
    存活状态检查端点

    Returns:
        基本的存活状态（进程是否在运行）
    """
    start_time = time.time()
    perf_logger = get_performance_logger("liveness_check", request_id=getattr(request.state, 'request_id', None))

    try:
        # 简单的存活检查
        response_time = (time.time() - start_time) * 1000

        result = {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - _get_process_start_time(),
            "response_time_ms": round(response_time, 2)
        }

        perf_logger.info("Liveness check completed", extra={
            "duration_ms": response_time,
            "status": "alive"
        })

        return result

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        perf_logger.error(f"Liveness check failed: {str(e)}", extra={
            "duration_ms": response_time,
            "status": "error",
            "error": str(e)
        })

        # 存活检查失败应该返回500，表示服务不可用
        raise HTTPException(status_code=500, detail={
            "status": "dead",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "response_time_ms": round(response_time, 2)
        })


@router.get("/metrics")
async def get_metrics(request: Request):
    """
    Prometheus指标端点

    Returns:
        Prometheus格式的指标数据
    """
    start_time = time.time()
    perf_logger = get_performance_logger("metrics_endpoint", request_id=getattr(request.state, 'request_id', None))

    try:
        # 获取Prometheus格式的指标
        metrics_data = metrics_collector.get_prometheus_metrics()
        response_time = (time.time() - start_time) * 1000

        perf_logger.info("Metrics retrieved", extra={
            "duration_ms": response_time,
            "data_size": len(metrics_data)
        })

        return PlainTextResponse(
            content=metrics_data,
            media_type=metrics_collector.get_content_type()
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        perf_logger.error(f"Metrics retrieval failed: {str(e)}", extra={
            "duration_ms": response_time,
            "status": "error",
            "error": str(e)
        })

        raise HTTPException(status_code=500, detail={
            "error": "Failed to retrieve metrics",
            "message": str(e),
            "response_time_ms": round(response_time, 2)
        })


@router.get("/metrics-summary")
async def get_metrics_summary(request: Request, minutes: int = 5):
    """
    获取指标摘要

    Args:
        minutes: 最近多少分钟的指标摘要

    Returns:
        指标的统计摘要信息
    """
    start_time = time.time()
    perf_logger = get_performance_logger("metrics_summary", request_id=getattr(request.state, 'request_id', None))

    try:
        # 获取指标摘要
        summary = metrics_collector.get_all_metrics_summary(minutes=minutes)
        response_time = (time.time() - start_time) * 1000

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "time_range_minutes": minutes,
            "metrics": summary,
            "summary": {
                "total_metric_types": len(summary),
                "active_metrics": len([m for m in summary.values() if m]),
                "response_time_ms": round(response_time, 2)
            }
        }

        perf_logger.info("Metrics summary retrieved", extra={
            "duration_ms": response_time,
            "time_range_minutes": minutes,
            "metric_count": len(summary)
        })

        return result

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        perf_logger.error(f"Metrics summary retrieval failed: {str(e)}", extra={
            "duration_ms": response_time,
            "status": "error",
            "error": str(e)
        })

        raise HTTPException(status_code=500, detail={
            "error": "Failed to retrieve metrics summary",
            "message": str(e),
            "response_time_ms": round(response_time, 2)
        })


@router.get("/status")
async def get_system_status(request: Request):
    """
    获取完整的系统状态

    Returns:
        包含健康检查、指标和系统信息的完整状态
    """
    start_time = time.time()
    perf_logger = get_performance_logger("system_status", request_id=getattr(request.state, 'request_id', None))

    try:
        # 并行获取各种状态信息
        health_summary = await health_checker.get_health_summary()
        metrics_summary = metrics_collector.get_all_metrics_summary(minutes=5)
        response_time = (time.time() - start_time) * 1000

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.4.0",
            "health": health_summary,
            "metrics_summary": {
                "time_range_minutes": 5,
                "total_metric_types": len(metrics_summary),
                "active_metrics": len([m for m in metrics_summary.values() if m]),
                "metrics": metrics_summary
            },
            "system_info": {
                "hostname": _get_hostname(),
                "process_id": _get_process_id(),
                "uptime_seconds": time.time() - _get_process_start_time()
            },
            "response_time_ms": round(response_time, 2)
        }

        perf_logger.info("System status retrieved", extra={
            "duration_ms": response_time,
            "overall_status": health_summary["overall_status"],
            "metric_count": len(metrics_summary)
        })

        return result

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        perf_logger.error(f"System status retrieval failed: {str(e)}", extra={
            "duration_ms": response_time,
            "status": "error",
            "error": str(e)
        })

        raise HTTPException(status_code=500, detail={
            "error": "Failed to retrieve system status",
            "message": str(e),
            "response_time_ms": round(response_time, 2)
        })


# 辅助函数
async def _check_api_health() -> "HealthCheckResult":
    """检查API健康状态"""
    start_time = time.time()

    try:
        # 简单的API自检
        await asyncio.sleep(0.01)  # 模拟检查
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            component="api",
            status=HealthStatus.HEALTHY,
            message="API service is healthy",
            details={
                "response_time_ms": round(response_time, 2),
                "version": "1.4.0"
            },
            response_time_ms=round(response_time, 2)
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return HealthCheckResult(
            component="api",
            status=HealthStatus.UNHEALTHY,
            message=f"API health check failed: {str(e)}",
            details={"error": str(e)},
            response_time_ms=round(response_time, 2)
        )


def _get_process_start_time() -> float:
    """获取进程启动时间"""
    try:
        import psutil
        return psutil.Process().create_time()
    except:
        return time.time()


def _get_hostname() -> str:
    """获取主机名"""
    try:
        import socket
        return socket.gethostname()
    except:
        return "unknown"


def _get_process_id() -> int:
    """获取进程ID"""
    try:
        import os
        return os.getpid()
    except:
        return 0