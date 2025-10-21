"""
性能监控指标收集器 - Prometheus指标和性能数据收集
"""

import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import psutil
import asyncio

from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from ..logging.config import get_context_logger

logger = get_context_logger(
    request_id="metrics",
    user_id="system",
    agent_type="metrics_collector",
    task_id="collection",
    session_id="monitoring"
)


@dataclass
class PerformanceMetric:
    """性能指标数据结构"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None
    unit: str = ""
    description: str = ""

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.registry = CollectorRegistry()
        self._metrics_store = defaultdict(lambda: deque(maxlen=1000))  # 最近1000个数据点
        self._lock = threading.Lock()

        # Prometheus指标定义
        self._setup_prometheus_metrics()

        # Agent协作监控指标
        self.agent_processing_time = Histogram(
            'agent_processing_duration_seconds',
            'Agent processing duration in seconds',
            ['agent_type', 'task_type', 'status'],
            registry=self.registry
        )

        # SOP工作流监控指标
        self.sop_workflow_duration = Histogram(
            'sop_workflow_duration_seconds',
            'SOP workflow completion time in seconds',
            ['workflow_name', 'severity_level', 'status'],
            registry=self.registry
        )

        # Plan任务状态指标
        self.plan_task_status = Gauge(
            'plan_task_status',
            'Current plan task status by type',
            ['status', 'assignee', 'task_type'],
            registry=self.registry
        )

        # Agent协作请求计数
        self.agent_collaboration_count = Counter(
            'agent_collaboration_total',
            'Total agent collaboration requests',
            ['requester', 'target', 'operation_type'],
            registry=self.registry
        )

        # API请求指标
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )

        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # 系统资源指标
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )

        self.system_memory_usage = Gauge(
            'system_memory_usage_percent',
            'System memory usage percentage',
            registry=self.registry
        )

        self.system_disk_usage = Gauge(
            'system_disk_usage_percent',
            'System disk usage percentage',
            registry=self.registry
        )

        # 应用指标
        self.active_sessions = Gauge(
            'active_sessions_total',
            'Number of active user sessions',
            registry=self.registry
        )

        self.active_agents = Gauge(
            'active_agents_total',
            'Number of active agents',
            ['agent_type'],
            registry=self.registry
        )

        # 错误指标
        self.error_total = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )

    def _setup_prometheus_metrics(self):
        """设置Prometheus指标"""
        pass

    def record_agent_processing_time(self, agent_type: str, task_type: str, duration_seconds: float, status: str = "success"):
        """记录Agent处理时间"""
        self.agent_processing_time.labels(
            agent_type=agent_type,
            task_type=task_type,
            status=status
        ).observe(duration_seconds)

        # 存储到内部指标
        metric = PerformanceMetric(
            name="agent_processing_time",
            value=duration_seconds,
            timestamp=datetime.utcnow(),
            labels={
                "agent_type": agent_type,
                "task_type": task_type,
                "status": status
            },
            unit="seconds",
            description="Agent processing duration"
        )
        self._store_metric(metric)

    def record_workflow_duration(self, workflow_name: str, severity_level: str, duration_seconds: float, status: str = "completed"):
        """记录工作流完成时间"""
        self.sop_workflow_duration.labels(
            workflow_name=workflow_name,
            severity_level=severity_level,
            status=status
        ).observe(duration_seconds)

        metric = PerformanceMetric(
            name="workflow_duration",
            value=duration_seconds,
            timestamp=datetime.utcnow(),
            labels={
                "workflow_name": workflow_name,
                "severity_level": severity_level,
                "status": status
            },
            unit="seconds",
            description="Workflow completion duration"
        )
        self._store_metric(metric)

    def update_plan_task_status(self, status: str, assignee: str, task_type: str, count: int = 1):
        """更新Plan任务状态"""
        self.plan_task_status.labels(
            status=status,
            assignee=assignee,
            task_type=task_type
        ).set(count)

        metric = PerformanceMetric(
            name="plan_task_status",
            value=count,
            timestamp=datetime.utcnow(),
            labels={
                "status": status,
                "assignee": assignee,
                "task_type": task_type
            },
            unit="count",
            description="Plan task status count"
        )
        self._store_metric(metric)

    def record_agent_collaboration(self, requester: str, target: str, operation_type: str):
        """记录Agent协作请求"""
        self.agent_collaboration_count.labels(
            requester=requester,
            target=target,
            operation_type=operation_type
        ).inc()

        metric = PerformanceMetric(
            name="agent_collaboration",
            value=1,
            timestamp=datetime.utcnow(),
            labels={
                "requester": requester,
                "target": target,
                "operation_type": operation_type
            },
            unit="count",
            description="Agent collaboration request"
        )
        self._store_metric(metric)

    def record_api_request(self, method: str, endpoint: str, status_code: int, duration_seconds: float):
        """记录API请求"""
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()

        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration_seconds)

        metric = PerformanceMetric(
            name="api_request",
            value=duration_seconds,
            timestamp=datetime.utcnow(),
            labels={
                "method": method,
                "endpoint": endpoint,
                "status_code": str(status_code)
            },
            unit="seconds",
            description="API request duration"
        )
        self._store_metric(metric)

    def update_system_metrics(self):
        """更新系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)

            # 内存使用率
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.percent)

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk_usage.set(disk_percent)

            # 记录系统指标
            for name, value in [
                ("cpu_usage", cpu_percent),
                ("memory_usage", memory.percent),
                ("disk_usage", disk_percent)
            ]:
                metric = PerformanceMetric(
                    name=f"system_{name}",
                    value=value,
                    timestamp=datetime.utcnow(),
                    unit="percent",
                    description=f"System {name.replace('_', ' ')}"
                )
                self._store_metric(metric)

        except Exception as e:
            logger.error(f"Failed to update system metrics: {str(e)}")

    def update_active_sessions(self, count: int):
        """更新活跃会话数"""
        self.active_sessions.set(count)

        metric = PerformanceMetric(
            name="active_sessions",
            value=count,
            timestamp=datetime.utcnow(),
            unit="count",
            description="Number of active sessions"
        )
        self._store_metric(metric)

    def update_active_agents(self, agent_type: str, count: int):
        """更新活跃Agent数量"""
        self.active_agents.labels(agent_type=agent_type).set(count)

        metric = PerformanceMetric(
            name="active_agents",
            value=count,
            timestamp=datetime.utcnow(),
            labels={"agent_type": agent_type},
            unit="count",
            description="Number of active agents"
        )
        self._store_metric(metric)

    def record_error(self, error_type: str, component: str, error_message: str = ""):
        """记录错误"""
        self.error_total.labels(
            error_type=error_type,
            component=component
        ).inc()

        metric = PerformanceMetric(
            name="error",
            value=1,
            timestamp=datetime.utcnow(),
            labels={
                "error_type": error_type,
                "component": component,
                "error_message": error_message[:100]  # 截断长错误消息
            },
            unit="count",
            description="Error occurrence"
        )
        self._store_metric(metric)

    def _store_metric(self, metric: PerformanceMetric):
        """存储指标到内部存储"""
        with self._lock:
            self._metrics_store[metric.name].append(metric)

    def get_metrics_summary(self, metric_name: str, minutes: int = 5) -> Dict[str, Any]:
        """获取指标摘要"""
        with self._lock:
            if metric_name not in self._metrics_store:
                return {}

            # 获取最近N分钟的数据
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            recent_metrics = [
                m for m in self._metrics_store[metric_name]
                if m.timestamp >= cutoff_time
            ]

            if not recent_metrics:
                return {}

            values = [m.value for m in recent_metrics]

            return {
                "metric_name": metric_name,
                "time_range_minutes": minutes,
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "latest": recent_metrics[-1].value,
                "latest_timestamp": recent_metrics[-1].timestamp.isoformat(),
                "unit": recent_metrics[-1].unit
            }

    def get_all_metrics_summary(self, minutes: int = 5) -> Dict[str, Dict[str, Any]]:
        """获取所有指标摘要"""
        summary = {}
        with self._lock:
            for metric_name in self._metrics_store.keys():
                summary[metric_name] = self.get_metrics_summary(metric_name, minutes)
        return summary

    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        return generate_latest(self.registry).decode('utf-8')

    def get_content_type(self) -> str:
        """获取Prometheus指标内容类型"""
        return CONTENT_TYPE_LATEST

    def cleanup_old_metrics(self, hours: int = 24):
        """清理旧指标数据"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        with self._lock:
            for metric_name in self._metrics_store.keys():
                # 保留最近的指标
                recent_metrics = deque(
                    (m for m in self._metrics_store[metric_name] if m.timestamp >= cutoff_time),
                    maxlen=1000
                )
                self._metrics_store[metric_name] = recent_metrics

        logger.info(f"Cleaned up metrics older than {hours} hours")

    async def start_background_collection(self):
        """启动后台指标收集"""
        async def collect_system_metrics():
            while True:
                try:
                    self.update_system_metrics()
                    await asyncio.sleep(30)  # 每30秒收集一次系统指标
                except Exception as e:
                    logger.error(f"System metrics collection error: {str(e)}")
                    await asyncio.sleep(60)  # 错误时等待更长时间

        async def cleanup_metrics():
            while True:
                try:
                    self.cleanup_old_metrics(hours=1)  # 每小时清理一次超过1小时的指标
                    await asyncio.sleep(3600)  # 每小时执行一次
                except Exception as e:
                    logger.error(f"Metrics cleanup error: {str(e)}")
                    await asyncio.sleep(3600)

        # 启动后台任务
        asyncio.create_task(collect_system_metrics())
        asyncio.create_task(cleanup_metrics())

        logger.info("Background metrics collection started")


# 全局指标收集器实例
metrics_collector = MetricsCollector()