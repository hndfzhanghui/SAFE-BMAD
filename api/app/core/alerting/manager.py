"""
告警管理器 - 告警规则管理和通知发送
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict

from ..logging.config import get_context_logger

logger = get_context_logger(
    request_id="alerting",
    user_id="system",
    agent_type="alert_manager",
    task_id="monitoring",
    session_id="alerting"
)


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """告警信息"""
    id: str
    name: str
    level: AlertLevel
    message: str
    component: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: AlertStatus = AlertStatus.ACTIVE
    details: Dict[str, Any] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level.value,
            "message": self.message,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "details": self.details,
            "labels": self.labels,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by
        }


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List["AlertRule"] = []
        self.notifiers: List["BaseNotifier"] = []
        self.suppression_rules: List[Callable[[Alert], bool]] = []
        self.alert_history: List[Alert] = []
        self._lock = asyncio.Lock()
        self._running = False

        # 告警统计
        self.stats = {
            "total_alerts": 0,
            "active_alerts": 0,
            "resolved_alerts": 0,
            "suppressed_alerts": 0,
            "alerts_by_level": defaultdict(int),
            "alerts_by_component": defaultdict(int)
        }

    def add_rule(self, rule: "AlertRule"):
        """添加告警规则"""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """移除告警规则"""
        self.alert_rules = [rule for rule in self.alert_rules if rule.name != rule_name]
        logger.info(f"Removed alert rule: {rule_name}")

    def add_notifier(self, notifier: "BaseNotifier"):
        """添加通知器"""
        self.notifiers.append(notifier)
        logger.info(f"Added notifier: {notifier.__class__.__name__}")

    def add_suppression_rule(self, rule: Callable[[Alert], bool]):
        """添加抑制规则"""
        self.suppression_rules.append(rule)
        logger.info("Added suppression rule")

    async def evaluate_rules(self, metrics: Dict[str, Any] = None):
        """评估所有告警规则"""
        metrics = metrics or {}

        for rule in self.alert_rules:
            try:
                alerts = await rule.evaluate(metrics)
                for alert in alerts:
                    await self.process_alert(alert)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {str(e)}")

    async def process_alert(self, alert: Alert):
        """处理告警"""
        async with self._lock:
            # 检查是否已存在相同的活跃告警
            existing_alert = self._find_existing_alert(alert)
            if existing_alert:
                logger.debug(f"Alert already exists: {alert.id}")
                return

            # 检查抑制规则
            if self._is_suppressed(alert):
                alert.status = AlertStatus.SUPPRESSED
                self.stats["suppressed_alerts"] += 1
                logger.info(f"Alert suppressed: {alert.id}")
                return

            # 添加到活跃告警
            self.alerts[alert.id] = alert
            self.alert_history.append(alert)
            self.stats["total_alerts"] += 1
            self.stats["active_alerts"] += 1
            self.stats["alerts_by_level"][alert.level.value] += 1
            self.stats["alerts_by_component"][alert.component] += 1

            logger.warning(f"New alert: {alert.name} - {alert.message}")

            # 发送通知
            await self._send_notifications(alert)

    def _find_existing_alert(self, alert: Alert) -> Optional[Alert]:
        """查找已存在的相同告警"""
        for existing_alert in self.alerts.values():
            if (existing_alert.name == alert.name and
                existing_alert.component == alert.component and
                existing_alert.status == AlertStatus.ACTIVE and
                existing_alert.level == alert.level):
                return existing_alert
        return None

    def _is_suppressed(self, alert: Alert) -> bool:
        """检查告警是否被抑制"""
        for rule in self.suppression_rules:
            try:
                if rule(alert):
                    return True
            except Exception as e:
                logger.error(f"Error evaluating suppression rule: {str(e)}")
        return False

    async def _send_notifications(self, alert: Alert):
        """发送告警通知"""
        for notifier in self.notifiers:
            try:
                await notifier.send_alert(alert)
            except Exception as e:
                logger.error(f"Error sending notification via {notifier.__class__.__name__}: {str(e)}")

    async def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """解决告警"""
        async with self._lock:
            if alert_id not in self.alerts:
                logger.warning(f"Alert not found: {alert_id}")
                return False

            alert = self.alerts[alert_id]
            if alert.status != AlertStatus.ACTIVE:
                logger.warning(f"Alert is not active: {alert_id}")
                return False

            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by

            self.stats["active_alerts"] -= 1
            self.stats["resolved_alerts"] += 1

            logger.info(f"Alert resolved: {alert_id} by {resolved_by}")

            # 发送解决通知
            await self._send_resolution_notifications(alert)

            return True

    async def _send_resolution_notifications(self, alert: Alert):
        """发送告警解决通知"""
        for notifier in self.notifiers:
            try:
                if hasattr(notifier, 'send_resolution'):
                    await notifier.send_resolution(alert)
            except Exception as e:
                logger.error(f"Error sending resolution notification via {notifier.__class__.__name__}: {str(e)}")

    def get_active_alerts(self, level: Optional[AlertLevel] = None, component: Optional[str] = None) -> List[Alert]:
        """获取活跃告警"""
        alerts = [alert for alert in self.alerts.values() if alert.status == AlertStatus.ACTIVE]

        if level:
            alerts = [alert for alert in alerts if alert.level == level]

        if component:
            alerts = [alert for alert in alerts if alert.component == component]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_alert_history(self, hours: int = 24, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]

        return sorted(recent_alerts, key=lambda a: a.timestamp, reverse=True)[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """获取告警统计信息"""
        return {
            **self.stats,
            "active_alerts_count": len(self.get_active_alerts()),
            "total_rules": len(self.alert_rules),
            "total_notifiers": len(self.notifiers),
            "suppression_rules_count": len(self.suppression_rules),
            "last_updated": datetime.utcnow().isoformat()
        }

    async def start_background_tasks(self):
        """启动后台任务"""
        if self._running:
            return

        self._running = True

        async def alert_monitoring():
            """后台告警监控任务"""
            while self._running:
                try:
                    # 这里可以添加定期评估逻辑
                    await asyncio.sleep(60)  # 每分钟检查一次
                except Exception as e:
                    logger.error(f"Alert monitoring error: {str(e)}")
                    await asyncio.sleep(60)

        async def cleanup_resolved_alerts():
            """清理已解决的告警"""
            while self._running:
                try:
                    # 清理24小时前已解决的告警
                    cutoff_time = datetime.utcnow() - timedelta(hours=24)
                    to_remove = []

                    for alert_id, alert in self.alerts.items():
                        if (alert.status == AlertStatus.RESOLVED and
                            alert.resolved_at and
                            alert.resolved_at < cutoff_time):
                            to_remove.append(alert_id)

                    async with self._lock:
                        for alert_id in to_remove:
                            del self.alerts[alert_id]

                    if to_remove:
                        logger.info(f"Cleaned up {len(to_remove)} resolved alerts")

                    await asyncio.sleep(3600)  # 每小时清理一次
                except Exception as e:
                    logger.error(f"Alert cleanup error: {str(e)}")
                    await asyncio.sleep(3600)

        # 启动后台任务
        asyncio.create_task(alert_monitoring())
        asyncio.create_task(cleanup_resolved_alerts())

        logger.info("Alert manager background tasks started")

    def stop_background_tasks(self):
        """停止后台任务"""
        self._running = False
        logger.info("Alert manager background tasks stopped")

    def generate_alert_id(self, name: str, component: str) -> str:
        """生成告警ID"""
        timestamp = int(time.time())
        return f"{component}_{name}_{timestamp}"

    async def create_manual_alert(
        self,
        name: str,
        level: AlertLevel,
        message: str,
        component: str,
        details: Dict[str, Any] = None,
        labels: Dict[str, str] = None
    ) -> Alert:
        """创建手动告警"""
        alert_id = self.generate_alert_id(name, component)
        alert = Alert(
            id=alert_id,
            name=name,
            level=level,
            message=message,
            component=component,
            details=details or {},
            labels=labels or {}
        )

        await self.process_alert(alert)
        return alert


# 全局告警管理器实例
alert_manager = AlertManager()