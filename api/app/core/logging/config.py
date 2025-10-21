"""
日志配置模块 - 结构化日志配置
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from loguru import logger


class LoggingConfig:
    """日志配置类"""

    def __init__(self):
        self.env = os.getenv("ENV", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # 标准日志字段
        self.standard_fields = [
            "timestamp",
            "level",
            "message",
            "module",
            "function",
            "line",
            "request_id",
            "user_id",
            "agent_type",
            "task_id",
            "workflow_id",
            "session_id"
        ]

    def get_log_format(self, format_type: str = "structured") -> str:
        """获取日志格式"""

        if format_type == "json":
            return (
                "{"
                '"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
                '"level": "{level}", '
                '"message": "{message}", '
                '"module": "{module}", '
                '"function": "{function}", '
                '"line": {line}, '
                '"request_id": "{extra[request_id]:N/A}", '
                '"user_id": "{extra[user_id]:anonymous}", '
                '"agent_type": "{extra[agent_type]:system}", '
                '"task_id": "{extra[task_id]:unknown}", '
                '"workflow_id": "{extra[workflow_id]:unknown}", '
                '"session_id": "{extra[session_id]:unknown}"'
                "}"
            )
        elif format_type == "console":
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[request_id]:N/A:<8}</cyan> | "
                "<cyan>{extra[user_id]:anonymous:<10}</cyan> | "
                "<cyan>{extra[agent_type]:system:<8}</cyan> | "
                "<level>{message}</level>"
            )
        elif format_type == "console_safe":
            # 安全的控制台格式，不依赖extra字段
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{module:<15}</cyan> | "
                "<level>{message}</level>"
            )
        elif format_type == "structured_safe":
            # 安全的结构化格式，使用默认值
            return (
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{extra[request_id]:N/A:<8} | "
                "{extra[user_id]:anonymous:<10} | "
                "{extra[agent_type]:system:<8} | "
                "{module}:{function}:{line} | "
                "{message}"
            )
        else:  # structured
            return (
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{extra[request_id]:N/A:<8} | "
                "{extra[user_id]:anonymous:<10} | "
                "{extra[agent_type]:system:<8} | "
                "{module}:{function}:{line} | "
                "{message}"
            )


def setup_logging(
    env: str = None,
    log_level: str = None,
    log_dir: str = None
) -> None:
    """
    设置结构化日志系统

    Args:
        env: 环境名称 (development/staging/production)
        log_level: 日志级别
        log_dir: 日志目录
    """

    # 移除默认处理器
    logger.remove()

    config = LoggingConfig()
    config.env = env or config.env
    config.log_level = log_level or config.log_level
    if log_dir:
        config.log_dir = Path(log_dir)
        config.log_dir.mkdir(exist_ok=True)

    # 控制台输出 - 使用安全格式避免字段缺失错误
    logger.add(
        sys.stdout,
        format=config.get_log_format("console_safe"),
        level=config.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # 主应用日志
    logger.add(
        config.log_dir / "app.log",
        format=config.get_log_format("structured_safe"),
        level=config.log_level,
        rotation="50 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )

    # JSON格式日志 (用于日志聚合)
    logger.add(
        config.log_dir / "app.json",
        format=config.get_log_format("json"),
        level="INFO",
        rotation="100 MB",
        retention="14 days",
        compression="zip",
        encoding="utf-8"
    )

    # Agent专用日志
    logger.add(
        config.log_dir / "agents.log",
        format=config.get_log_format("structured_safe"),
        level="DEBUG",
        rotation="20 MB",
        retention="7 days",
        compression="zip",
        filter=lambda record: "agent_type" in record["extra"] and record["extra"]["agent_type"],
        encoding="utf-8"
    )

    # SOP工作流日志
    logger.add(
        config.log_dir / "workflows.log",
        format=config.get_log_format("structured_safe"),
        level="INFO",
        rotation="20 MB",
        retention="14 days",
        compression="zip",
        filter=lambda record: "workflow_id" in record["extra"] and record["extra"]["workflow_id"],
        encoding="utf-8"
    )

    # 错误日志
    logger.add(
        config.log_dir / "errors.log",
        format=config.get_log_format("console_safe"),
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )

    # 性能监控日志
    logger.add(
        config.log_dir / "performance.log",
        format=config.get_log_format("json"),
        level="INFO",
        rotation="30 MB",
        retention="7 days",
        compression="zip",
        filter=lambda record: "performance" in record["extra"],
        encoding="utf-8"
    )

    # 审计日志
    logger.add(
        config.log_dir / "audit.log",
        format=config.get_log_format("json"),
        level="INFO",
        rotation="50 MB",
        retention="90 days",  # 审计日志保留更长时间
        compression="zip",
        filter=lambda record: "audit" in record["extra"],
        encoding="utf-8"
    )

    # 环境特定配置
    if config.env == "production":
        # 生产环境：更严格的日志级别
        logger.remove()

        # 仅生产环境控制台日志
        logger.add(
            sys.stdout,
            format=config.get_log_format("json"),
            level="WARNING",
            colorize=False
        )

        # 生产环境文件日志
        logger.add(
            config.log_dir / "production.log",
            format=config.get_log_format("json"),
            level="INFO",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8"
        )

    elif config.env == "staging":
        # 测试环境配置
        pass  # 使用默认配置

    logger.info(f"日志系统初始化完成 - 环境: {config.env}, 级别: {config.log_level}")


def get_logger(name: str = None, **extra_fields) -> logger:
    """
    获取带上下文的日志记录器

    Args:
        name: 日志记录器名称
        **extra_fields: 额外的上下文字段

    Returns:
        配置好的日志记录器
    """

    if name:
        return logger.bind(name=name, **extra_fields)
    else:
        return logger.bind(**extra_fields)


# 预定义的日志记录器
def get_agent_logger(agent_type: str, task_id: str = None, **extra) -> logger:
    """获取Agent专用日志记录器"""
    return logger.bind(
        agent_type=agent_type,
        task_id=task_id or "unknown",
        **extra
    )


def get_workflow_logger(workflow_id: str, step_id: str = None, **extra) -> logger:
    """获取工作流专用日志记录器"""
    return logger.bind(
        workflow_id=workflow_id,
        step_id=step_id or "unknown",
        **extra
    )


def get_audit_logger(user_id: str = None, action: str = None, **extra) -> logger:
    """获取审计日志记录器"""
    return logger.bind(
        audit=True,
        user_id=user_id or "anonymous",
        action=action,
        **extra
    )


def get_performance_logger(operation: str = None, **extra) -> logger:
    """获取性能监控日志记录器"""
    return logger.bind(
        performance=True,
        operation=operation,
        **extra
    )


# 全局请求ID生成器
import uuid

def generate_request_id() -> str:
    """生成请求ID"""
    return str(uuid.uuid4())[:8]


def get_context_logger(
    request_id: str = None,
    user_id: str = None,
    agent_type: str = None,
    task_id: str = None,
    workflow_id: str = None,
    session_id: str = None
) -> logger:
    """
    获取带完整上下文的日志记录器

    Args:
        request_id: 请求ID
        user_id: 用户ID
        agent_type: Agent类型
        task_id: 任务ID
        workflow_id: 工作流ID
        session_id: 会话ID

    Returns:
        带上下文的日志记录器
    """

    return logger.bind(
        request_id=request_id or generate_request_id(),
        user_id=user_id or "anonymous",
        agent_type=agent_type or "system",
        task_id=task_id or "unknown",
        workflow_id=workflow_id or "unknown",
        session_id=session_id or "unknown"
    )