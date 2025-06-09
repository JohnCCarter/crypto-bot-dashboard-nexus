"""Monitoring service for trading operations."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    """Trading alert."""

    level: AlertLevel
    message: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class PerformanceMetrics:
    """Trading performance metrics."""

    def __init__(self):
        """Initialize performance metrics."""
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.current_drawdown = 0.0
        self.peak_value = 0.0
        self.trade_history: List[Dict[str, Any]] = []

    def update(self, trade: Dict[str, Any]):
        """
        Update metrics with new trade.

        Args:
            trade: Trade data dictionary
        """
        self.total_trades += 1
        pnl = trade.get("pnl", 0.0)
        self.total_pnl += pnl

        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # Update drawdown
        current_value = self.total_pnl
        if current_value > self.peak_value:
            self.peak_value = current_value
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_value - current_value) / self.peak_value
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)

        self.trade_history.append(trade)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.

        Returns:
            Dict containing performance metrics
        """
        win_rate = (
            self.winning_trades / self.total_trades if self.total_trades > 0 else 0.0
        )

        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "total_pnl": self.total_pnl,
            "max_drawdown": self.max_drawdown,
            "current_drawdown": self.current_drawdown,
            "peak_value": self.peak_value,
        }


class Monitor:
    """Service for monitoring trading operations."""

    def __init__(self, log_file: str = "trading.log"):
        """
        Initialize monitor.

        Args:
            log_file: Path to log file
        """
        self.logger = logging.getLogger("trading_monitor")
        self.logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Performance tracking
        self.performance = PerformanceMetrics()
        self.alerts: List[Alert] = []

    def log_trade(self, trade: Dict[str, Any]):
        """
        Log trade execution.

        Args:
            trade: Trade data dictionary
        """
        self.logger.info(f"Trade executed: {trade}")
        self.performance.update(trade)

    def create_alert(
        self, level: AlertLevel, message: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create and log alert.

        Args:
            level: Alert severity level
            message: Alert message
            metadata: Optional alert metadata
        """
        alert = Alert(
            level=level, message=message, timestamp=datetime.utcnow(), metadata=metadata
        )

        self.alerts.append(alert)
        self.logger.log(
            getattr(logging, level.value), f"{message} - {metadata if metadata else ''}"
        )

    def check_performance(self, thresholds: Dict[str, float]):
        """
        Check performance against thresholds.

        Args:
            thresholds: Performance thresholds
        """
        metrics = self.performance.get_metrics()

        # Check drawdown
        if metrics["current_drawdown"] > thresholds.get("max_drawdown", 0.1):
            self.create_alert(
                AlertLevel.WARNING,
                "Drawdown threshold exceeded",
                {"current_drawdown": metrics["current_drawdown"]},
            )

        # Check win rate
        if metrics["win_rate"] < thresholds.get("min_win_rate", 0.4):
            self.create_alert(
                AlertLevel.WARNING,
                "Win rate below threshold",
                {"win_rate": metrics["win_rate"]},
            )

        # Check PnL
        if metrics["total_pnl"] < thresholds.get("min_pnl", -1000):
            self.create_alert(
                AlertLevel.ERROR,
                "PnL below threshold",
                {"total_pnl": metrics["total_pnl"]},
            )

    def get_recent_alerts(
        self, level: Optional[AlertLevel] = None, hours: int = 24
    ) -> List[Alert]:
        """
        Get recent alerts.

        Args:
            level: Optional filter by alert level
            hours: Time window in hours

        Returns:
            List of recent alerts
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        alerts = [alert for alert in self.alerts if alert.timestamp > cutoff]

        if level:
            alerts = [alert for alert in alerts if alert.level == level]

        return alerts

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get performance report.

        Returns:
            Dict containing performance metrics and recent alerts
        """
        return {
            "metrics": self.performance.get_metrics(),
            "recent_alerts": [
                {
                    "level": alert.level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata,
                }
                for alert in self.get_recent_alerts()
            ],
        }
