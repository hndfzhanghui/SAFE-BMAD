"""
告警规则 - 阈值告警、趋势告警等规则定义
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .manager import Alert, AlertLevel, alert_manager
from .notifiers import ConsoleNotifier
from ..logging.config import get_logger

logger = get_logger("alert_rules")


@dataclass
class MetricValue:
    """指标值"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


class AlertRule(ABC):
    """告警规则基类"""

    def __init__(self, name: str, description: str = "", enabled: bool = True):
        self.name = name
        self.description = description
        self.enabled = enabled
        self.last_evaluation = None
        self.evaluation_count = 0

    @abstractmethod
    async def evaluate(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估规则，返回需要触发的告警"""
        pass

    def create_alert(
        self,
        name: str,
        level: AlertLevel,
        message: str,
        component: str,
        details: Dict[str, Any] = None,
        labels: Dict[str, str] = None
    ) -> Alert:
        """创建告警"""
        alert_id = alert_manager.generate_alert_id(name, component)
        return Alert(
            id=alert_id,
            name=name,
            level=level,
            message=message,
            component=component,
            details=details or {},
            labels=labels or {}
        )


class ThresholdRule(AlertRule):
    """阈值告警规则"""

    def __init__(
        self,
        name: str,
        metric_name: str,
        threshold: float,
        operator: str = ">",  # >, <, >=, <=, ==, !=
        level: AlertLevel = AlertLevel.WARNING,
        component: str = "system",
        description: str = "",
        enabled: bool = True
    ):
        super().__init__(name, description, enabled)
        self.metric_name = metric_name
        self.threshold = threshold
        self.operator = operator
        self.level = level
        self.component = component

    async def evaluate(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估阈值规则"""
        if not self.enabled:
            return []

        self.last_evaluation = datetime.utcnow()
        self.evaluation_count += 1

        # 获取指标值
        metric_value = self._get_metric_value(metrics)
        if metric_value is None:
            return []

        # 检查阈值条件
        if self._check_threshold(metric_value):
            message = f"Metric '{self.metric_name}' {self.operator} {self.threshold}: current value {metric_value}"
            details = {
                "metric_name": self.metric_name,
                "current_value": metric_value,
                "threshold": self.threshold,
                "operator": self.operator
            }

            alert = self.create_alert(
                name=self.name,
                level=self.level,
                message=message,
                component=self.component,
                details=details,
                labels={"rule_type": "threshold"}
            )

            return [alert]

        return []

    def _get_metric_value(self, metrics: Dict[str, Any]) -> Optional[float]:
        """从指标数据中获取值"""
        if self.metric_name in metrics:
            return float(metrics[self.metric_name])
        return None

    def _check_threshold(self, value: float) -> bool:
        """检查阈值条件"""
        if self.operator == ">":
            return value > self.threshold
        elif self.operator == "<":
            return value < self.threshold
        elif self.operator == ">=":
            return value >= self.threshold
        elif self.operator == "<=":
            return value <= self.threshold
        elif self.operator == "==":
            return value == self.threshold
        elif self.operator == "!=":
            return value != self.threshold
        else:
            return False


class MultiLevelThresholdRule(AlertRule):
    """多级阈值告警规则"""

    def __init__(
        self,
        name: str,
        metric_name: str,
        thresholds: List[tuple],  # [(threshold, level, operator), ...]
        component: str = "system",
        description: str = "",
        enabled: bool = True
    ):
        super().__init__(name, description, enabled)
        self.metric_name = metric_name
        self.thresholds = sorted(thresholds, key=lambda x: x[0], reverse=True)  # 按阈值降序排列
        self.component = component

    async def evaluate(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估多级阈值规则"""
        if not self.enabled:
            return []

        self.last_evaluation = datetime.utcnow()
        self.evaluation_count += 1

        # 获取指标值
        metric_value = self._get_metric_value(metrics)
        if metric_value is None:
            return []

        # 检查各级阈值
        for threshold, level, operator in self.thresholds:
            if self._check_condition(metric_value, threshold, operator):
                message = f"Metric '{self.metric_name}' {operator} {threshold}: current value {metric_value}"
                details = {
                    "metric_name": self.metric_name,
                    "current_value": metric_value,
                    "threshold": threshold,
                    "operator": operator,
                    "severity": level.value
                }

                alert = self.create_alert(
                    name=self.name,
                    level=level,
                    message=message,
                    component=self.component,
                    details=details,
                    labels={"rule_type": "multi_threshold"}
                )

                return [alert]

        return []

    def _get_metric_value(self, metrics: Dict[str, Any]) -> Optional[float]:
        """从指标数据中获取值"""
        if self.metric_name in metrics:
            return float(metrics[self.metric_name])
        return None

    def _check_condition(self, value: float, threshold: float, operator: str) -> bool:
        """检查条件"""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        else:
            return False


class TrendRule(AlertRule):
    """趋势告警规则"""

    def __init__(
        self,
        name: str,
        metric_name: str,
        trend_direction: str,  # "increasing", "decreasing"
        threshold: float,
        window_minutes: int = 5,
        min_data_points: int = 3,
        level: AlertLevel = AlertLevel.WARNING,
        component: str = "system",
        description: str = "",
        enabled: bool = True
    ):
        super().__init__(name, description, enabled)
        self.metric_name = metric_name
        self.trend_direction = trend_direction
        self.threshold = threshold
        self.window_minutes = window_minutes
        self.min_data_points = min_data_points
        self.level = level
        self.component = component
        self.metric_history: List[MetricValue] = []

    async def evaluate(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估趋势规则"""
        if not self.enabled:
            return []

        self.last_evaluation = datetime.utcnow()
        self.evaluation_count += 1

        # 获取当前指标值
        current_value = self._get_metric_value(metrics)
        if current_value is None:
            return []

        # 添加到历史记录
        now = datetime.utcnow()
        metric_value = MetricValue(
            name=self.metric_name,
            value=current_value,
            timestamp=now
        )
        self.metric_history.append(metric_value)

        # 清理过期数据
        cutoff_time = now - timedelta(minutes=self.window_minutes)
        self.metric_history = [
            mv for mv in self.metric_history
            if mv.timestamp >= cutoff_time
        ]

        # 检查数据点数量
        if len(self.metric_history) < self.min_data_points:
            return []

        # 计算趋势
        trend_value = self._calculate_trend()
        if trend_value is None:
            return []

        # 检查趋势条件
        if self._check_trend(trend_value):
            message = f"Metric '{self.metric_name}' shows {self.trend_direction} trend: {trend_value:.2f} (threshold: {self.threshold})"
            details = {
                "metric_name": self.metric_name,
                "trend_value": trend_value,
                "threshold": self.threshold,
                "trend_direction": self.trend_direction,
                "data_points": len(self.metric_history),
                "window_minutes": self.window_minutes
            }

            alert = self.create_alert(
                name=self.name,
                level=self.level,
                message=message,
                component=self.component,
                details=details,
                labels={"rule_type": "trend"}
            )

            return [alert]

        return []

    def _get_metric_value(self, metrics: Dict[str, Any]) -> Optional[float]:
        """从指标数据中获取值"""
        if self.metric_name in metrics:
            return float(metrics[self.metric_name])
        return None

    def _calculate_trend(self) -> Optional[float]:
        """计算趋势值（简单线性回归斜率）"""
        if len(self.metric_history) < 2:
            return None

        # 按时间排序
        sorted_metrics = sorted(self.metric_history, key=lambda x: x.timestamp)

        # 计算线性回归斜率
        n = len(sorted_metrics)
        if n < 2:
            return None

        # 时间戳转换为秒数
        times = [(mv.timestamp - sorted_metrics[0].timestamp).total_seconds() for mv in sorted_metrics]
        values = [mv.value for mv in sorted_metrics]

        # 计算斜率
        sum_x = sum(times)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(times, values))
        sum_x2 = sum(x * x for x in times)

        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return 0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def _check_trend(self, trend_value: float) -> bool:
        """检查趋势条件"""
        if self.trend_direction == "increasing":
            return trend_value > self.threshold
        elif self.trend_direction == "decreasing":
            return trend_value < -self.threshold
        else:
            return False


class HeartbeatRule(AlertRule):
    """心跳告警规则"""

    def __init__(
        self,
        name: str,
        component: str,
        timeout_minutes: int = 5,
        level: AlertLevel = AlertLevel.ERROR,
        description: str = "",
        enabled: bool = True
    ):
        super().__init__(name, description, enabled)
        self.component = component
        self.timeout_minutes = timeout_minutes
        self.level = level
        self.last_heartbeat = None

    async def evaluate(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估心跳规则"""
        if not self.enabled:
            return []

        self.last_evaluation = datetime.utcnow()
        self.evaluation_count += 1

        # 检查是否有心跳更新
        heartbeat_key = f"{self.component}_heartbeat"
        if heartbeat_key in metrics:
            self.last_heartbeat = datetime.utcnow()
            return []

        # 检查心跳超时
        if self.last_heartbeat is None:
            # 还没有收到过心跳
            message = f"Component '{self.component}' has never sent a heartbeat"
        else:
            time_since_heartbeat = (datetime.utcnow() - self.last_heartbeat).total_seconds() / 60
            if time_since_heartbeat < self.timeout_minutes:
                return []

            message = f"Component '{self.component}' heartbeat timeout: {time_since_heartbeat:.1f} minutes ago"

        details = {
            "component": self.component,
            "timeout_minutes": self.timeout_minutes,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }

        alert = self.create_alert(
            name=self.name,
            level=self.level,
            message=message,
            component=self.component,
            details=details,
            labels={"rule_type": "heartbeat"}
        )

        return [alert]

    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.utcnow()


class ErrorRateRule(AlertRule):
    """错误率告警规则"""

    def __init__(
        self,
        name: str,
        component: str,
        error_threshold: float = 0.1,  # 10%
        window_minutes: int = 5,
        min_requests: int = 10,
        level: AlertLevel = AlertLevel.WARNING,
        description: str = "",
        enabled: bool = True
    ):
        super().__init__(name, description, enabled)
        self.component = component
        self.error_threshold = error_threshold
        self.window_minutes = window_minutes
        self.min_requests = min_requests
        self.level = level
        self.request_history: List[tuple] = []  # (timestamp, is_error)

    async def evaluate(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估错误率规则"""
        if not self.enabled:
            return []

        self.last_evaluation = datetime.utcnow()
        self.evaluation_count += 1

        # 从指标中提取请求数据
        self._extract_requests_from_metrics(metrics)

        # 清理过期数据
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        self.request_history = [
            (timestamp, is_error) for timestamp, is_error in self.request_history
            if timestamp >= cutoff_time
        ]

        # 检查最小请求数
        if len(self.request_history) < self.min_requests:
            return []

        # 计算错误率
        total_requests = len(self.request_history)
        error_requests = sum(1 for _, is_error in self.request_history if is_error)
        error_rate = error_requests / total_requests if total_requests > 0 else 0

        # 检查错误率阈值
        if error_rate > self.error_threshold:
            message = f"Component '{self.component}' error rate too high: {error_rate:.2%} ({error_requests}/{total_requests})"
            details = {
                "component": self.component,
                "error_rate": error_rate,
                "error_threshold": self.error_threshold,
                "total_requests": total_requests,
                "error_requests": error_requests,
                "window_minutes": self.window_minutes
            }

            alert = self.create_alert(
                name=self.name,
                level=self.level,
                message=message,
                component=self.component,
                details=details,
                labels={"rule_type": "error_rate"}
            )

            return [alert]

        return []

    def _extract_requests_from_metrics(self, metrics: Dict[str, Any]):
        """从指标中提取请求数据"""
        # 这里可以根据实际的指标格式来提取请求数据
        # 示例：从API请求指标中提取
        if "api_requests" in metrics:
            for request_data in metrics["api_requests"]:
                timestamp = datetime.utcnow()  # 实际应该从数据中获取
                is_error = request_data.get("status_code", 200) >= 400
                self.request_history.append((timestamp, is_error))

    def add_request(self, is_error: bool):
        """手动添加请求记录"""
        self.request_history.append((datetime.utcnow(), is_error))


# 预定义的告警规则工厂
class AlertRuleFactory:
    """告警规则工厂"""

    @staticmethod
    def create_system_cpu_rule(cpu_threshold: float = 80.0) -> ThresholdRule:
        """创建CPU使用率告警规则"""
        return ThresholdRule(
            name="high_cpu_usage",
            metric_name="cpu_usage",
            threshold=cpu_threshold,
            operator=">",
            level=AlertLevel.WARNING,
            component="system",
            description=f"CPU usage exceeds {cpu_threshold}%"
        )

    @staticmethod
    def create_system_memory_rule(memory_threshold: float = 85.0) -> ThresholdRule:
        """创建内存使用率告警规则"""
        return ThresholdRule(
            name="high_memory_usage",
            metric_name="memory_usage",
            threshold=memory_threshold,
            operator=">",
            level=AlertLevel.WARNING,
            component="system",
            description=f"Memory usage exceeds {memory_threshold}%"
        )

    @staticmethod
    def create_disk_space_rule(disk_threshold: float = 90.0) -> ThresholdRule:
        """创建磁盘空间告警规则"""
        return ThresholdRule(
            name="low_disk_space",
            metric_name="disk_usage",
            threshold=disk_threshold,
            operator=">",
            level=AlertLevel.ERROR,
            component="system",
            description=f"Disk usage exceeds {disk_threshold}%"
        )

    @staticmethod
    def create_api_error_rate_rule(error_threshold: float = 0.05) -> ErrorRateRule:
        """创建API错误率告警规则"""
        return ErrorRateRule(
            name="high_api_error_rate",
            component="api",
            error_threshold=error_threshold,
            window_minutes=5,
            min_requests=10,
            level=AlertLevel.WARNING,
            description=f"API error rate exceeds {error_threshold:.1%}"
        )

    @staticmethod
    def create_response_time_rule(response_threshold: float = 3.0) -> ThresholdRule:
        """创建响应时间告警规则"""
        return ThresholdRule(
            name="slow_response_time",
            metric_name="avg_response_time",
            threshold=response_threshold,
            operator=">",
            level=AlertLevel.WARNING,
            component="api",
            description=f"Average response time exceeds {response_threshold}s"
        )

    @staticmethod
    def create_multi_level_cpu_rule() -> MultiLevelThresholdRule:
        """创建多级CPU告警规则"""
        return MultiLevelThresholdRule(
            name="multi_level_cpu_usage",
            metric_name="cpu_usage",
            thresholds=[
                (95.0, AlertLevel.CRITICAL, ">"),
                (85.0, AlertLevel.ERROR, ">"),
                (75.0, AlertLevel.WARNING, ">")
            ],
            component="system",
            description="Multi-level CPU usage monitoring"
        )


def setup_default_rules():
    """设置默认告警规则"""
    rules = [
        AlertRuleFactory.create_system_cpu_rule(80.0),
        AlertRuleFactory.create_system_memory_rule(85.0),
        AlertRuleFactory.create_disk_space_rule(90.0),
        AlertRuleFactory.create_multi_level_cpu_rule(),
        AlertRuleFactory.create_response_time_rule(2.0)
    ]

    for rule in rules:
        alert_manager.add_rule(rule)

    logger.info(f"Setup {len(rules)} default alert rules")

    return rules