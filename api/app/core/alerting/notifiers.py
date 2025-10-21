"""
告警通知器 - 邮件、企业微信等通知渠道
"""

import asyncio
import smtplib
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
import json
import requests

from .manager import Alert, AlertLevel, AlertStatus
from ..logging.config import get_logger

logger = get_logger("alert_notifier")


class BaseNotifier(ABC):
    """告警通知器基类"""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """发送告警通知"""
        pass

    async def send_resolution(self, alert: Alert) -> bool:
        """发送告警解决通知（可选实现）"""
        return True


class EmailNotifier(BaseNotifier):
    """邮件通知器"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
        enabled: bool = False,  # 默认禁用，需要配置
        use_tls: bool = True
    ):
        super().__init__("email", enabled)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls

    async def send_alert(self, alert: Alert) -> bool:
        """发送告警邮件"""
        if not self.enabled:
            logger.debug("Email notifier is disabled")
            return True

        try:
            # 构建邮件内容
            subject = f"[{alert.level.value.upper()}] {alert.name} - {alert.component}"
            body = self._build_email_body(alert)

            # 发送邮件
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_email_sync,
                subject,
                body
            )

            logger.info(f"Alert email sent: {alert.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            return False

    async def send_resolution(self, alert: Alert) -> bool:
        """发送告警解决邮件"""
        if not self.enabled:
            return True

        try:
            subject = f"[RESOLVED] {alert.name} - {alert.component}"
            body = self._build_resolution_body(alert)

            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_email_sync,
                subject,
                body
            )

            logger.info(f"Resolution email sent: {alert.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send resolution email: {str(e)}")
            return False

    def _send_email_sync(self, subject: str, body: str):
        """同步发送邮件"""
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html', 'utf-8'))

        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        if self.use_tls:
            server.starttls()
        server.login(self.username, self.password)
        server.send_message(msg)
        server.quit()

    def _build_email_body(self, alert: Alert) -> str:
        """构建告警邮件内容"""
        level_color = {
            AlertLevel.INFO: "#17a2b8",
            AlertLevel.WARNING: "#ffc107",
            AlertLevel.ERROR: "#dc3545",
            AlertLevel.CRITICAL: "#721c24"
        }.get(alert.level, "#6c757d")

        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .alert-header {{ background-color: {level_color}; color: white; padding: 15px; border-radius: 5px; }}
                .alert-body {{ padding: 20px; border: 1px solid #ddd; margin-top: 10px; }}
                .alert-details {{ margin-top: 15px; }}
                .detail-item {{ margin: 5px 0; }}
                .detail-label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="alert-header">
                <h2>🚨 {alert.level.value.upper()} ALERT</h2>
                <h3>{alert.name}</h3>
            </div>

            <div class="alert-body">
                <p><strong>Message:</strong> {alert.message}</p>
                <p><strong>Component:</strong> {alert.component}</p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>

                <div class="alert-details">
                    <h4>Details:</h4>
                    {self._format_details(alert.details)}
                </div>

                {self._format_labels(alert.labels)}
            </div>
        </body>
        </html>
        """

    def _build_resolution_body(self, alert: Alert) -> str:
        """构建告警解决邮件内容"""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .resolution-header {{ background-color: #28a745; color: white; padding: 15px; border-radius: 5px; }}
                .resolution-body {{ padding: 20px; border: 1px solid #ddd; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="resolution-header">
                <h2>✅ ALERT RESOLVED</h2>
                <h3>{alert.name}</h3>
            </div>

            <div class="resolution-body">
                <p><strong>Original Alert:</strong> {alert.message}</p>
                <p><strong>Component:</strong> {alert.component}</p>
                <p><strong>Alert Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Resolved Time:</strong> {alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Resolved By:</strong> {alert.resolved_by}</p>
            </div>
        </body>
        </html>
        """

    def _format_details(self, details: Dict[str, Any]) -> str:
        """格式化详细信息"""
        if not details:
            return "<p>No additional details available.</p>"

        html = ""
        for key, value in details.items():
            html += f'<div class="detail-item"><span class="detail-label">{key}:</span> {value}</div>'
        return html

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """格式化标签"""
        if not labels:
            return ""

        html = '<div class="alert-details"><h4>Labels:</h4>'
        for key, value in labels.items():
            html += f'<span class="detail-item"><strong>{key}:</strong> {value}</span> '
        html += '</div>'
        return html


class WeChatNotifier(BaseNotifier):
    """企业微信通知器"""

    def __init__(
        self,
        webhook_url: str,
        enabled: bool = False,  # 默认禁用，需要配置
        mentioned_users: List[str] = None,
        mentioned_mobiles: List[str] = None
    ):
        super().__init__("wechat", enabled)
        self.webhook_url = webhook_url
        self.mentioned_users = mentioned_users or []
        self.mentioned_mobiles = mentioned_mobiles or []

    async def send_alert(self, alert: Alert) -> bool:
        """发送企业微信告警通知"""
        if not self.enabled:
            logger.debug("WeChat notifier is disabled")
            return True

        try:
            message = self._build_wechat_message(alert)

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_wechat_sync,
                message
            )

            if response.get('errcode') == 0:
                logger.info(f"WeChat alert sent: {alert.id}")
                return True
            else:
                logger.error(f"WeChat alert failed: {response}")
                return False

        except Exception as e:
            logger.error(f"Failed to send WeChat alert: {str(e)}")
            return False

    async def send_resolution(self, alert: Alert) -> bool:
        """发送企业微信解决通知"""
        if not self.enabled:
            return True

        try:
            message = self._build_resolution_message(alert)

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_wechat_sync,
                message
            )

            if response.get('errcode') == 0:
                logger.info(f"WeChat resolution sent: {alert.id}")
                return True
            else:
                logger.error(f"WeChat resolution failed: {response}")
                return False

        except Exception as e:
            logger.error(f"Failed to send WeChat resolution: {str(e)}")
            return False

    def _send_wechat_sync(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """同步发送企业微信消息"""
        response = requests.post(
            self.webhook_url,
            json=message,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def _build_wechat_message(self, alert: Alert) -> Dict[str, Any]:
        """构建企业微信告警消息"""
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }.get(alert.level, "📋")

        content = f"""
{level_emoji} **{alert.level.value.upper()} ALERT**

**告警名称**: {alert.name}
**组件**: {alert.component}
**时间**: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**消息**: {alert.message}

**详细信息**:
{self._format_wechat_details(alert.details)}
        """

        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

        # 添加@用户
        if self.mentioned_users or self.mentioned_mobiles:
            message["markdown"]["mentioned_list"] = self.mentioned_users
            message["markdown"]["mentioned_mobile_list"] = self.mentioned_mobiles

        return message

    def _build_resolution_message(self, alert: Alert) -> Dict[str, Any]:
        """构建企业微信解决消息"""
        content = f"""
✅ **ALERT RESOLVED**

**告警名称**: {alert.name}
**组件**: {alert.component}
**告警时间**: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**解决时间**: {alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S')}
**解决者**: {alert.resolved_by}

**原始消息**: {alert.message}
        """

        return {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

    def _format_wechat_details(self, details: Dict[str, Any]) -> str:
        """格式化企业微信详细信息"""
        if not details:
            return "无额外信息"

        lines = []
        for key, value in details.items():
            lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)


class ConsoleNotifier(BaseNotifier):
    """控制台通知器 - 用于测试和开发"""

    def __init__(self, enabled: bool = True):
        super().__init__("console", enabled)

    async def send_alert(self, alert: Alert) -> bool:
        """在控制台输出告警"""
        if not self.enabled:
            return True

        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }.get(alert.level, "📋")

        print(f"\n{level_emoji} {alert.level.value.upper()} ALERT")
        print(f"   ID: {alert.id}")
        print(f"   Name: {alert.name}")
        print(f"   Component: {alert.component}")
        print(f"   Message: {alert.message}")
        print(f"   Time: {alert.timestamp}")
        if alert.details:
            print(f"   Details: {json.dumps(alert.details, indent=2, ensure_ascii=False)}")
        print()

        return True

    async def send_resolution(self, alert: Alert) -> bool:
        """在控制台输出解决通知"""
        if not self.enabled:
            return True

        print(f"\n✅ ALERT RESOLVED")
        print(f"   ID: {alert.id}")
        print(f"   Name: {alert.name}")
        print(f"   Component: {alert.component}")
        print(f"   Resolved by: {alert.resolved_by}")
        print(f"   Resolved at: {alert.resolved_at}")
        print()

        return True