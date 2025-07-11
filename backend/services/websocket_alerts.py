"""
Real-time Alerts for WebSocket Monitoring

This module provides comprehensive alerting system for WebSocket connections,
including performance alerts, anomaly notifications, and system health warnings.
"""

import asyncio
import json
import logging
import smtplib
import ssl
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from .websocket_connection_interface import ConnectionState, ConnectionType
from .websocket_in_memory_store import (ConnectionRecord,
                                        InMemoryConnectionStore)


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""

    CONNECTION_FAILURE = "connection_failure"
    HIGH_LATENCY = "high_latency"
    HIGH_ERROR_RATE = "high_error_rate"
    FREQUENT_RECONNECTS = "frequent_reconnects"
    LOAD_BALANCER_ISSUE = "load_balancer_issue"
    CLUSTER_NODE_DOWN = "cluster_node_down"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CAPACITY_WARNING = "capacity_warning"
    ANOMALY_DETECTED = "anomaly_detected"
    SYSTEM_HEALTH = "system_health"


class NotificationChannel(Enum):
    """Notification channels"""

    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    LOG = "log"
    CONSOLE = "console"


@dataclass
class AlertRule:
    """Alert rule configuration"""

    alert_type: AlertType
    severity: AlertSeverity
    condition: str
    threshold: Union[float, int, str]
    time_window_minutes: int = 5
    enabled: bool = True
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    cooldown_minutes: int = 15
    description: str = ""


@dataclass
class Alert:
    """Alert instance"""

    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    connection_id: Optional[str] = None
    cluster_node_id: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    notification_sent: bool = False


@dataclass
class NotificationConfig:
    """Configuration for notification channels"""

    email_config: Optional[Dict[str, Any]] = None
    webhook_config: Optional[Dict[str, Any]] = None
    slack_config: Optional[Dict[str, Any]] = None
    discord_config: Optional[Dict[str, Any]] = None


class AlertNotifier:
    """Base class for alert notifications"""

    async def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send notification for alert"""
        raise NotImplementedError


class EmailNotifier(AlertNotifier):
    """Email notification handler"""

    async def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send email notification"""
        try:
            smtp_server = config.get("smtp_server", "smtp.gmail.com")
            smtp_port = config.get("smtp_port", 587)
            username = config.get("username")
            password = config.get("password")
            from_email = config.get("from_email")
            to_emails = config.get("to_emails", [])

            if not all([username, password, from_email, to_emails]):
                logging.error("Email notification: Missing required configuration")
                return False

            # Create message
            msg = MIMEMultipart()
            msg["From"] = str(from_email)
            msg["To"] = ", ".join(str(email) for email in to_emails)
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"

            # Create HTML body
            html_body = f"""
            <html>
            <body>
                <h2>{alert.title}</h2>
                <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                <p><strong>Type:</strong> {alert.alert_type.value}</p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Message:</strong> {alert.message}</p>
            """

            if alert.connection_id:
                html_body += (
                    f"<p><strong>Connection ID:</strong> {alert.connection_id}</p>"
                )

            if alert.metrics:
                html_body += "<h3>Metrics:</h3><ul>"
                for key, value in alert.metrics.items():
                    html_body += f"<li><strong>{key}:</strong> {value}</li>"
                html_body += "</ul>"

            html_body += "</body></html>"

            msg.attach(MIMEText(html_body, "html"))

            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(str(username), str(password))
                server.send_message(msg)

            logging.info(f"Email notification sent for alert {alert.alert_id}")
            return True

        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")
            return False


class WebhookNotifier(AlertNotifier):
    """Webhook notification handler"""

    async def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send webhook notification"""
        try:
            import aiohttp

            webhook_url = config.get("webhook_url")
            if not webhook_url:
                logging.error("Webhook notification: Missing webhook URL")
                return False

            # Prepare payload
            payload = {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "connection_id": alert.connection_id,
                "cluster_node_id": alert.cluster_node_id,
                "metrics": alert.metrics,
            }

            # Add custom headers if provided
            headers = config.get("headers", {"Content-Type": "application/json"})

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url, json=payload, headers=headers
                ) as response:
                    if response.status in [200, 201, 202]:
                        logging.info(
                            f"Webhook notification sent for alert {alert.alert_id}"
                        )
                        return True
                    else:
                        logging.error(
                            f"Webhook notification failed with status {response.status}"
                        )
                        return False

        except Exception as e:
            logging.error(f"Failed to send webhook notification: {e}")
            return False


class SlackNotifier(AlertNotifier):
    """Slack notification handler"""

    async def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send Slack notification"""
        try:
            import aiohttp

            webhook_url = config.get("webhook_url")
            channel = config.get("channel", "#alerts")

            if not webhook_url:
                logging.error("Slack notification: Missing webhook URL")
                return False

            # Prepare Slack message
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ffa500",
                AlertSeverity.ERROR: "#ff0000",
                AlertSeverity.CRITICAL: "#8b0000",
            }

            payload = {
                "channel": channel,
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "#36a64f"),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True,
                            },
                            {
                                "title": "Type",
                                "value": alert.alert_type.value,
                                "short": True,
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True,
                            },
                        ],
                        "footer": "WebSocket Monitoring System",
                    }
                ],
            }

            if alert.connection_id:
                payload["attachments"][0]["fields"].append(
                    {
                        "title": "Connection ID",
                        "value": alert.connection_id,
                        "short": True,
                    }
                )

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status in [200, 201, 202]:
                        logging.info(
                            f"Slack notification sent for alert {alert.alert_id}"
                        )
                        return True
                    else:
                        logging.error(
                            f"Slack notification failed with status {response.status}"
                        )
                        return False

        except Exception as e:
            logging.error(f"Failed to send Slack notification: {e}")
            return False


class LogNotifier(AlertNotifier):
    """Log notification handler"""

    async def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Log alert to file"""
        try:
            log_level = getattr(logging, alert.severity.value.upper())
            logging.log(log_level, f"ALERT [{alert.alert_type.value}]: {alert.message}")
            return True
        except Exception as e:
            logging.error(f"Failed to log alert: {e}")
            return False


class ConsoleNotifier(AlertNotifier):
    """Console notification handler"""

    async def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Print alert to console"""
        try:
            severity_colors = {
                AlertSeverity.INFO: "\033[32m",  # Green
                AlertSeverity.WARNING: "\033[33m",  # Yellow
                AlertSeverity.ERROR: "\033[31m",  # Red
                AlertSeverity.CRITICAL: "\033[35m",  # Magenta
            }

            color = severity_colors.get(alert.severity, "\033[0m")
            reset = "\033[0m"

            print(f"{color}[{alert.severity.value.upper()}] {alert.title}{reset}")
            print(f"  Message: {alert.message}")
            print(f"  Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Type: {alert.alert_type.value}")

            if alert.connection_id:
                print(f"  Connection: {alert.connection_id}")

            print()
            return True

        except Exception as e:
            print(f"Failed to print alert to console: {e}")
            return False


class WebSocketAlertManager:
    """
    Comprehensive alert management system for WebSocket monitoring.

    Features:
    - Configurable alert rules
    - Multiple notification channels
    - Alert deduplication and cooldown
    - Historical alert tracking
    - Automatic alert resolution
    """

    def __init__(
        self,
        store: InMemoryConnectionStore,
        notification_config: Optional[NotificationConfig] = None,
    ):
        self.store = store
        self.notification_config = notification_config or NotificationConfig()

        # Alert management
        self._alerts: Dict[str, Alert] = {}
        self._alert_rules: List[AlertRule] = []
        self._alert_history: deque = deque(maxlen=10000)
        self._cooldown_timestamps: Dict[str, datetime] = {}

        # Notification handlers
        self._notifiers: Dict[NotificationChannel, AlertNotifier] = {
            NotificationChannel.EMAIL: EmailNotifier(),
            NotificationChannel.WEBHOOK: WebhookNotifier(),
            NotificationChannel.SLACK: SlackNotifier(),
            NotificationChannel.LOG: LogNotifier(),
            NotificationChannel.CONSOLE: ConsoleNotifier(),
        }

        # Background tasks
        self._alert_check_task: Optional[asyncio.Task] = None
        self._alert_cleanup_task: Optional[asyncio.Task] = None

        # Initialize default alert rules
        self._initialize_default_rules()

        # Start background tasks
        self._start_background_tasks()

    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                alert_type=AlertType.CONNECTION_FAILURE,
                severity=AlertSeverity.ERROR,
                condition="connection_state == 'error'",
                threshold=1,
                time_window_minutes=5,
                notification_channels=[
                    NotificationChannel.CONSOLE,
                    NotificationChannel.LOG,
                ],
                description="Connection failure detected",
            ),
            AlertRule(
                alert_type=AlertType.HIGH_LATENCY,
                severity=AlertSeverity.WARNING,
                condition="latency_ms > 1000",
                threshold=1000,
                time_window_minutes=5,
                notification_channels=[
                    NotificationChannel.CONSOLE,
                    NotificationChannel.LOG,
                ],
                description="High latency detected",
            ),
            AlertRule(
                alert_type=AlertType.HIGH_ERROR_RATE,
                severity=AlertSeverity.ERROR,
                condition="error_rate > 0.05",
                threshold=0.05,
                time_window_minutes=5,
                notification_channels=[
                    NotificationChannel.CONSOLE,
                    NotificationChannel.LOG,
                ],
                description="High error rate detected",
            ),
            AlertRule(
                alert_type=AlertType.FREQUENT_RECONNECTS,
                severity=AlertSeverity.WARNING,
                condition="reconnect_attempts > 3",
                threshold=3,
                time_window_minutes=10,
                notification_channels=[
                    NotificationChannel.CONSOLE,
                    NotificationChannel.LOG,
                ],
                description="Frequent reconnection attempts",
            ),
            AlertRule(
                alert_type=AlertType.SYSTEM_HEALTH,
                severity=AlertSeverity.CRITICAL,
                condition="health_score < 50",
                threshold=50,
                time_window_minutes=5,
                notification_channels=[
                    NotificationChannel.CONSOLE,
                    NotificationChannel.LOG,
                ],
                description="System health critical",
            ),
        ]

        self._alert_rules.extend(default_rules)

    def _start_background_tasks(self):
        """Start background alert checking and cleanup tasks"""

        async def alert_check_loop():
            while True:
                try:
                    await asyncio.sleep(30)  # Check every 30 seconds
                    await self._check_alerts()
                except Exception as e:
                    logging.error(f"Error in alert check loop: {e}")

        async def alert_cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # Cleanup every 5 minutes
                    await self._cleanup_old_alerts()
                except Exception as e:
                    logging.error(f"Error in alert cleanup loop: {e}")

        loop = asyncio.get_event_loop()
        self._alert_check_task = loop.create_task(alert_check_loop())
        self._alert_cleanup_task = loop.create_task(alert_cleanup_loop())

    async def _check_alerts(self):
        """Check for new alerts based on rules"""
        active_connections = self.store.get_active_connections()

        for rule in self._alert_rules:
            if not rule.enabled:
                continue

            # Check cooldown
            cooldown_key = f"{rule.alert_type.value}_{rule.severity.value}"
            if cooldown_key in self._cooldown_timestamps:
                time_since_last = (
                    datetime.now() - self._cooldown_timestamps[cooldown_key]
                )
                if time_since_last < timedelta(minutes=rule.cooldown_minutes):
                    continue

            # Check each connection against rule
            for connection in active_connections:
                await self._evaluate_alert_rule(rule, connection)

    async def _evaluate_alert_rule(self, rule: AlertRule, connection: ConnectionRecord):
        """Evaluate if connection triggers alert rule"""
        try:
            # Extract metrics for evaluation
            metrics = connection.metrics
            state = connection.state

            # Evaluate condition
            should_alert = False
            alert_metrics = {}

            if rule.alert_type == AlertType.CONNECTION_FAILURE:
                should_alert = state == ConnectionState.ERROR
                alert_metrics = {
                    "state": state.value,
                    "errors_count": metrics.errors_count,
                }

            elif rule.alert_type == AlertType.HIGH_LATENCY:
                should_alert = metrics.latency_ms > rule.threshold
                alert_metrics = {
                    "latency_ms": metrics.latency_ms,
                    "threshold": rule.threshold,
                }

            elif rule.alert_type == AlertType.HIGH_ERROR_RATE:
                total_messages = metrics.messages_sent + metrics.messages_received
                error_rate = metrics.errors_count / max(total_messages, 1)
                should_alert = error_rate > rule.threshold
                alert_metrics = {"error_rate": error_rate, "threshold": rule.threshold}

            elif rule.alert_type == AlertType.FREQUENT_RECONNECTS:
                should_alert = metrics.reconnect_attempts > rule.threshold
                alert_metrics = {
                    "reconnect_attempts": metrics.reconnect_attempts,
                    "threshold": rule.threshold,
                }

            elif rule.alert_type == AlertType.SYSTEM_HEALTH:
                # Calculate health score
                health_score = 100.0
                total_messages = metrics.messages_sent + metrics.messages_received
                if total_messages > 0:
                    error_rate = metrics.errors_count / total_messages
                    health_score -= error_rate * 50
                health_score -= min(metrics.reconnect_attempts * 10, 30)
                if metrics.latency_ms > 1000:
                    health_score -= 20

                should_alert = health_score < rule.threshold
                alert_metrics = {
                    "health_score": health_score,
                    "threshold": rule.threshold,
                }

            # Create alert if condition is met
            if should_alert:
                await self._create_alert(rule, connection, alert_metrics)

        except Exception as e:
            logging.error(f"Error evaluating alert rule {rule.alert_type.value}: {e}")

    async def _create_alert(
        self, rule: AlertRule, connection: ConnectionRecord, metrics: Dict[str, Any]
    ):
        """Create and send alert"""
        import uuid

        alert_id = str(uuid.uuid4())

        alert = Alert(
            alert_id=alert_id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            title=f"{rule.alert_type.value.replace('_', ' ').title()} Alert",
            message=rule.description,
            timestamp=datetime.now(),
            connection_id=connection.connection_id,
            cluster_node_id=connection.cluster_node_id,
            metrics=metrics,
        )

        # Store alert
        self._alerts[alert_id] = alert
        self._alert_history.append(alert)

        # Set cooldown
        cooldown_key = f"{rule.alert_type.value}_{rule.severity.value}"
        self._cooldown_timestamps[cooldown_key] = datetime.now()

        # Send notifications
        await self._send_notifications(alert, rule.notification_channels)

        logging.info(f"Alert created: {alert.alert_type.value} - {alert.message}")

    async def _send_notifications(
        self, alert: Alert, channels: List[NotificationChannel]
    ):
        """Send notifications for alert"""
        for channel in channels:
            if channel not in self._notifiers:
                logging.warning(f"Notification channel {channel.value} not supported")
                continue

            notifier = self._notifiers[channel]
            config = self._get_channel_config(channel)

            try:
                success = await notifier.send_notification(alert, config)
                if success:
                    alert.notification_sent = True
            except Exception as e:
                logging.error(f"Failed to send {channel.value} notification: {e}")

    def _get_channel_config(self, channel: NotificationChannel) -> Dict[str, Any]:
        """Get configuration for notification channel"""
        if channel == NotificationChannel.EMAIL:
            return self.notification_config.email_config or {}
        elif channel == NotificationChannel.WEBHOOK:
            return self.notification_config.webhook_config or {}
        elif channel == NotificationChannel.SLACK:
            return self.notification_config.slack_config or {}
        elif channel == NotificationChannel.DISCORD:
            return self.notification_config.discord_config or {}
        else:
            return {}

    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        alerts_to_remove = []
        for alert_id, alert in self._alerts.items():
            if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff_time:
                alerts_to_remove.append(alert_id)

        for alert_id in alerts_to_remove:
            del self._alerts[alert_id]

    def add_alert_rule(self, rule: AlertRule):
        """Add new alert rule"""
        self._alert_rules.append(rule)
        logging.info(f"Alert rule added: {rule.alert_type.value}")

    def remove_alert_rule(self, alert_type: AlertType):
        """Remove alert rule by type"""
        self._alert_rules = [
            rule for rule in self._alert_rules if rule.alert_type != alert_type
        ]
        logging.info(f"Alert rule removed: {alert_type.value}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self._alerts.values() if not alert.resolved]

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self._alert_history if alert.timestamp >= cutoff_time
        ]

    def resolve_alert(self, alert_id: str, resolution_message: str = ""):
        """Mark alert as resolved"""
        if alert_id in self._alerts:
            alert = self._alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            logging.info(f"Alert resolved: {alert_id} - {resolution_message}")

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert statistics"""
        active_alerts = self.get_active_alerts()

        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)

        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
            type_counts[alert.alert_type.value] += 1

        return {
            "total_active_alerts": len(active_alerts),
            "severity_distribution": dict(severity_counts),
            "type_distribution": dict(type_counts),
            "critical_alerts": severity_counts.get(AlertSeverity.CRITICAL.value, 0),
            "error_alerts": severity_counts.get(AlertSeverity.ERROR.value, 0),
            "warning_alerts": severity_counts.get(AlertSeverity.WARNING.value, 0),
        }

    async def shutdown(self):
        """Shutdown alert manager"""
        if self._alert_check_task:
            self._alert_check_task.cancel()
            try:
                await self._alert_check_task
            except asyncio.CancelledError:
                pass

        if self._alert_cleanup_task:
            self._alert_cleanup_task.cancel()
            try:
                await self._alert_cleanup_task
            except asyncio.CancelledError:
                pass
