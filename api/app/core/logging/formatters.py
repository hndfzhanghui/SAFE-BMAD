"""
日志格式化器 - 自定义日志格式
"""

import json
import sys
from datetime import datetime
from typing import Any, Dict

from loguru import logger


class StructuredFormatter:
    """结构化日志格式化器"""

    def __init__(self, include_extra: bool = True):
        self.include_extra = include_extra

    def __call__(self, record: Dict[str, Any]) -> str:
        """格式化日志记录"""

        # 基础字段
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"]
        }

        # 额外字段
        if self.include_extra and record["extra"]:
            extra = record["extra"].copy()

            # 移除系统保留字段
            for key in ["name", "record", "extra", "exception"]:
                extra.pop(key, None)

            if extra:
                log_entry.update(extra)

        # 异常信息
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class AgentLogFormatter:
    """Agent专用日志格式化器"""

    def __call__(self, record: Dict[str, Any]) -> str:
        """格式化Agent日志"""

        extra = record["extra"]

        # Agent日志格式
        return (
            f"{record['time']:YYYY-MM-DD HH:mm:ss.SSS} | "
            f"{record['level']: <8} | "
            f"{extra.get('agent_type', 'N/A'):<8} | "
            f"{extra.get('task_id', 'N/A'):<8} | "
            f"{extra.get('user_id', 'N/A'):<10} | "
            f"{record['module']:<15} | "
            f"{record['message']}"
        )


class WorkflowLogFormatter:
    """工作流日志格式化器"""

    def __call__(self, record: Dict[str, Any]) -> str:
        """格式化工作流日志"""

        extra = record["extra"]

        # 工作流日志格式
        return (
            f"{record['time']:YYYY-MM-DD HH:mm:ss.SSS} | "
            f"{record['level']: <8} | "
            f"WF:{extra.get('workflow_id', 'N/A'):<8} | "
            f"ST:{extra.get('step_id', 'N/A'):<8} | "
            f"{extra.get('agent_type', 'N/A'):<8} | "
            f"{record['message']}"
        )


class PerformanceLogFormatter:
    """性能监控日志格式化器"""

    def __call__(self, record: Dict[str, Any]) -> str:
        """格式化性能日志"""

        extra = record["extra"]

        # 性能日志格式
        perf_data = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "operation": extra.get("operation", "unknown"),
            "duration_ms": extra.get("duration_ms", 0),
            "status": extra.get("status", "success"),
            "details": extra.get("details", {}),
            "message": record["message"]
        }

        return json.dumps(perf_data, ensure_ascii=False, default=str)


class AuditLogFormatter:
    """审计日志格式化器"""

    def __call__(self, record: Dict[str, Any]) -> str:
        """格式化审计日志"""

        extra = record["extra"]

        # 审计日志格式
        audit_data = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "user_id": extra.get("user_id", "anonymous"),
            "action": extra.get("action", "unknown"),
            "resource": extra.get("resource", "unknown"),
            "result": extra.get("result", "success"),
            "ip_address": extra.get("ip_address", "unknown"),
            "user_agent": extra.get("user_agent", "unknown"),
            "details": extra.get("details", {}),
            "message": record["message"]
        }

        return json.dumps(audit_data, ensure_ascii=False, default=str)


def get_json_formatter(include_extra: bool = True) -> StructuredFormatter:
    """获取JSON格式化器"""
    return StructuredFormatter(include_extra=include_extra)


def get_structured_formatter() -> StructuredFormatter:
    """获取结构化格式化器"""
    return StructuredFormatter(include_extra=True)


def get_agent_formatter() -> AgentLogFormatter:
    """获取Agent格式化器"""
    return AgentLogFormatter()


def get_workflow_formatter() -> WorkflowLogFormatter:
    """获取工作流格式化器"""
    return WorkflowLogFormatter()


def get_performance_formatter() -> PerformanceLogFormatter:
    """获取性能格式化器"""
    return PerformanceLogFormatter()


def get_audit_formatter() -> AuditLogFormatter:
    """获取审计格式化器"""
    return AuditLogFormatter()