"""
Advanced Analytics for WebSocket Performance Monitoring

This module provides comprehensive analytics and insights for WebSocket connections,
including performance metrics, anomaly detection, and predictive analysis.
"""

import asyncio
import json
import math
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import stats

from .websocket_connection_interface import ConnectionMetrics, ConnectionType
from .websocket_in_memory_store import ConnectionRecord, InMemoryConnectionStore


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""

    connection_type: ConnectionType
    timestamp: datetime
    avg_latency_ms: float
    avg_bandwidth_mbps: float
    error_rate: float
    connection_success_rate: float
    message_throughput: float
    active_connections: int
    total_messages: int
    peak_concurrent_connections: int


@dataclass
class AnomalyDetection:
    """Anomaly detection results"""

    connection_id: str
    anomaly_type: str
    severity: str  # low, medium, high, critical
    timestamp: datetime
    description: str
    metrics: Dict[str, Any]
    confidence: float


@dataclass
class PredictiveInsight:
    """Predictive analysis insights"""

    insight_type: str
    timestamp: datetime
    prediction: str
    confidence: float
    timeframe: str
    factors: List[str]
    recommendations: List[str]


class WebSocketAnalytics:
    """
    Advanced analytics engine for WebSocket performance monitoring.

    Features:
    - Real-time performance metrics aggregation
    - Anomaly detection using statistical methods
    - Predictive analysis for capacity planning
    - Historical trend analysis
    - Load balancing optimization insights
    """

    def __init__(self, store: InMemoryConnectionStore):
        self.store = store

        # Analytics storage
        self._performance_history: Dict[ConnectionType, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        self._anomalies: deque = deque(maxlen=1000)
        self._insights: deque = deque(maxlen=500)

        # Statistical models
        self._latency_baselines: Dict[ConnectionType, Dict[str, float]] = defaultdict(
            dict
        )
        self._error_rate_baselines: Dict[ConnectionType, float] = defaultdict(float)
        self._throughput_baselines: Dict[ConnectionType, float] = defaultdict(float)

        # Anomaly detection parameters
        self._anomaly_thresholds = {
            "latency_zscore": 3.0,
            "error_rate_threshold": 0.05,  # 5%
            "throughput_drop_threshold": 0.3,  # 30% drop
            "connection_failure_threshold": 0.1,  # 10%
        }

        # Background tasks
        self._analytics_task: Optional[asyncio.Task] = None
        self._anomaly_detection_task: Optional[asyncio.Task] = None

        # Start background analytics
        self._start_analytics_tasks()

    def _start_analytics_tasks(self):
        """Start background analytics tasks"""

        async def analytics_loop():
            while True:
                try:
                    await asyncio.sleep(60)  # Run every minute
                    await self._update_performance_metrics()
                    await self._update_baselines()
                except Exception as e:
                    print(f"Error in analytics loop: {e}")

        async def anomaly_detection_loop():
            while True:
                try:
                    await asyncio.sleep(30)  # Run every 30 seconds
                    await self._detect_anomalies()
                except Exception as e:
                    print(f"Error in anomaly detection loop: {e}")

        loop = asyncio.get_event_loop()
        self._analytics_task = loop.create_task(analytics_loop())
        self._anomaly_detection_task = loop.create_task(anomaly_detection_loop())

    async def _update_performance_metrics(self):
        """Update aggregated performance metrics"""
        for conn_type in ConnectionType:
            connections = self.store.get_connections_by_type(
                conn_type, active_only=True
            )

            if not connections:
                continue

            # Calculate metrics
            latencies = [
                conn.metrics.latency_ms
                for conn in connections
                if conn.metrics.latency_ms > 0
            ]
            bandwidths = [conn.metrics.bandwidth_bytes for conn in connections]
            error_counts = [conn.metrics.errors_count for conn in connections]
            message_counts = [
                conn.metrics.messages_sent + conn.metrics.messages_received
                for conn in connections
            ]

            # Aggregate metrics
            avg_latency = statistics.mean(latencies) if latencies else 0.0
            avg_bandwidth_mbps = (
                (statistics.mean(bandwidths) * 8 / 1_000_000) if bandwidths else 0.0
            )
            total_errors = sum(error_counts)
            total_messages = sum(message_counts)
            error_rate = total_errors / max(total_messages, 1)

            # Connection success rate (simplified)
            total_connections = self.store.get_connection_stats()["by_type"].get(
                conn_type.value, 0
            )
            active_connections = len(connections)
            connection_success_rate = active_connections / max(total_connections, 1)

            # Message throughput (messages per second)
            message_throughput = total_messages / 60.0  # Assuming 1-minute window

            # Create performance metrics
            metrics = PerformanceMetrics(
                connection_type=conn_type,
                timestamp=datetime.now(),
                avg_latency_ms=avg_latency,
                avg_bandwidth_mbps=avg_bandwidth_mbps,
                error_rate=error_rate,
                connection_success_rate=connection_success_rate,
                message_throughput=message_throughput,
                active_connections=active_connections,
                total_messages=total_messages,
                peak_concurrent_connections=total_connections,
            )

            self._performance_history[conn_type].append(metrics)

    async def _update_baselines(self):
        """Update statistical baselines for anomaly detection"""
        for conn_type in ConnectionType:
            history = self._performance_history[conn_type]

            if len(history) < 10:  # Need minimum data points
                continue

            # Extract recent metrics (last 100 data points)
            recent_metrics = list(history)[-100:]

            # Calculate baselines
            latencies = [
                m.avg_latency_ms for m in recent_metrics if m.avg_latency_ms > 0
            ]
            error_rates = [m.error_rate for m in recent_metrics]
            throughputs = [m.message_throughput for m in recent_metrics]

            if latencies:
                self._latency_baselines[conn_type] = {
                    "mean": statistics.mean(latencies),
                    "std": statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
                }

            if error_rates:
                self._error_rate_baselines[conn_type] = statistics.mean(error_rates)

            if throughputs:
                self._throughput_baselines[conn_type] = statistics.mean(throughputs)

    async def _detect_anomalies(self):
        """Detect anomalies in connection performance"""
        for conn_type in ConnectionType:
            connections = self.store.get_connections_by_type(
                conn_type, active_only=True
            )

            for connection in connections:
                anomalies = []

                # Check latency anomalies
                if conn_type in self._latency_baselines:
                    baseline = self._latency_baselines[conn_type]
                    if baseline["std"] > 0:
                        z_score = (
                            abs(connection.metrics.latency_ms - baseline["mean"])
                            / baseline["std"]
                        )
                        if z_score > self._anomaly_thresholds["latency_zscore"]:
                            anomalies.append(
                                AnomalyDetection(
                                    connection_id=connection.connection_id,
                                    anomaly_type="high_latency",
                                    severity="high" if z_score > 5 else "medium",
                                    timestamp=datetime.now(),
                                    description=f"Latency {connection.metrics.latency_ms:.2f}ms is {z_score:.2f} standard deviations above baseline",
                                    metrics={
                                        "latency_ms": connection.metrics.latency_ms,
                                        "z_score": z_score,
                                    },
                                    confidence=min(z_score / 10.0, 1.0),
                                )
                            )

                # Check error rate anomalies
                if conn_type in self._error_rate_baselines:
                    baseline_error_rate = self._error_rate_baselines[conn_type]
                    current_error_rate = connection.metrics.errors_count / max(
                        connection.metrics.messages_sent
                        + connection.metrics.messages_received,
                        1,
                    )

                    if current_error_rate > baseline_error_rate * 2:  # 2x baseline
                        anomalies.append(
                            AnomalyDetection(
                                connection_id=connection.connection_id,
                                anomaly_type="high_error_rate",
                                severity=(
                                    "high" if current_error_rate > 0.1 else "medium"
                                ),
                                timestamp=datetime.now(),
                                description=f"Error rate {current_error_rate:.2%} is above baseline {baseline_error_rate:.2%}",
                                metrics={
                                    "error_rate": current_error_rate,
                                    "baseline": baseline_error_rate,
                                },
                                confidence=min(current_error_rate / 0.2, 1.0),
                            )
                        )

                # Check connection stability
                if connection.metrics.reconnect_attempts > 3:
                    anomalies.append(
                        AnomalyDetection(
                            connection_id=connection.connection_id,
                            anomaly_type="frequent_reconnects",
                            severity="medium",
                            timestamp=datetime.now(),
                            description=f"Connection has {connection.metrics.reconnect_attempts} reconnect attempts",
                            metrics={
                                "reconnect_attempts": connection.metrics.reconnect_attempts
                            },
                            confidence=0.8,
                        )
                    )

                # Add anomalies to history
                for anomaly in anomalies:
                    self._anomalies.append(anomaly)

    def get_performance_metrics(
        self, connection_type: Optional[ConnectionType] = None, hours: int = 24
    ) -> List[PerformanceMetrics]:
        """Get performance metrics for specified time period"""
        if connection_type:
            history = self._performance_history[connection_type]
        else:
            # Combine all types
            all_metrics = []
            for conn_type in ConnectionType:
                all_metrics.extend(self._performance_history[conn_type])
            history = deque(all_metrics, maxlen=10000)

        # Filter by time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in history if m.timestamp >= cutoff_time]

    def get_anomalies(
        self, severity: Optional[str] = None, hours: int = 24
    ) -> List[AnomalyDetection]:
        """Get anomalies for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        anomalies = [a for a in self._anomalies if a.timestamp >= cutoff_time]

        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]

        return anomalies

    def get_connection_health_score(self, connection_id: str) -> float:
        """Calculate health score for a connection (0-100)"""
        connection = self.store.get_connection(connection_id)
        if not connection:
            return 0.0

        score = 100.0

        # Deduct points for errors
        total_messages = (
            connection.metrics.messages_sent + connection.metrics.messages_received
        )
        if total_messages > 0:
            error_rate = connection.metrics.errors_count / total_messages
            score -= error_rate * 50  # Up to 50 points for errors

        # Deduct points for reconnects
        score -= min(
            connection.metrics.reconnect_attempts * 10, 30
        )  # Up to 30 points for reconnects

        # Deduct points for high latency
        if connection.metrics.latency_ms > 1000:  # 1 second
            score -= 20

        return max(score, 0.0)

    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        stats = self.store.get_connection_stats()

        # Calculate health scores for all connections
        health_scores = []
        for conn_type in ConnectionType:
            connections = self.store.get_connections_by_type(
                conn_type, active_only=True
            )
            for connection in connections:
                health_scores.append(
                    self.get_connection_health_score(connection.connection_id)
                )

        avg_health_score = statistics.mean(health_scores) if health_scores else 0.0

        # Get recent anomalies
        recent_anomalies = self.get_anomalies(hours=1)
        critical_anomalies = [a for a in recent_anomalies if a.severity == "critical"]
        high_anomalies = [a for a in recent_anomalies if a.severity == "high"]

        return {
            "overall_health_score": avg_health_score,
            "active_connections": stats["active_connections"],
            "total_connections": stats["total_connections"],
            "error_rate": stats["errors_count"] / max(stats["total_created"], 1),
            "recent_anomalies": len(recent_anomalies),
            "critical_anomalies": len(critical_anomalies),
            "high_anomalies": len(high_anomalies),
            "health_status": self._get_health_status(
                avg_health_score, len(critical_anomalies)
            ),
        }

    def _get_health_status(self, health_score: float, critical_anomalies: int) -> str:
        """Determine overall health status"""
        if critical_anomalies > 0:
            return "critical"
        elif health_score < 50:
            return "poor"
        elif health_score < 80:
            return "fair"
        else:
            return "good"

    def get_load_balancing_recommendations(self) -> List[Dict[str, Any]]:
        """Get load balancing optimization recommendations"""
        recommendations = []

        for conn_type in ConnectionType:
            connections = self.store.get_connections_by_type(
                conn_type, active_only=True
            )

            if len(connections) < 2:
                continue

            # Analyze load distribution
            message_counts = [conn.metrics.messages_sent for conn in connections]
            avg_messages = statistics.mean(message_counts)
            std_messages = (
                statistics.stdev(message_counts) if len(message_counts) > 1 else 0
            )

            # Check for uneven load distribution
            if std_messages > avg_messages * 0.5:  # More than 50% variation
                recommendations.append(
                    {
                        "type": "load_balancing",
                        "connection_type": conn_type.value,
                        "issue": "uneven_load_distribution",
                        "description": f"Load distribution has {std_messages/avg_messages:.1%} variation",
                        "recommendation": "Consider implementing weighted round-robin or least-connections algorithm",
                        "priority": "medium",
                    }
                )

            # Check for overloaded connections
            max_messages = max(message_counts)
            if max_messages > avg_messages * 2:  # More than 2x average
                recommendations.append(
                    {
                        "type": "capacity_planning",
                        "connection_type": conn_type.value,
                        "issue": "overloaded_connection",
                        "description": f"Peak connection has {max_messages} messages vs {avg_messages:.0f} average",
                        "recommendation": "Consider adding more connections or implementing connection limits",
                        "priority": "high",
                    }
                )

        return recommendations

    def get_capacity_planning_insights(self) -> List[PredictiveInsight]:
        """Generate capacity planning insights"""
        insights = []

        for conn_type in ConnectionType:
            history = self._performance_history[conn_type]

            if len(history) < 20:  # Need sufficient data
                continue

            # Analyze trends
            recent_metrics = list(history)[-20:]
            older_metrics = list(history)[-40:-20]

            if not older_metrics:
                continue

            # Calculate growth rates
            recent_avg_connections = statistics.mean(
                [m.active_connections for m in recent_metrics]
            )
            older_avg_connections = statistics.mean(
                [m.active_connections for m in older_metrics]
            )

            recent_avg_throughput = statistics.mean(
                [m.message_throughput for m in recent_metrics]
            )
            older_avg_throughput = statistics.mean(
                [m.message_throughput for m in older_metrics]
            )

            # Growth analysis
            connection_growth = (recent_avg_connections - older_avg_connections) / max(
                older_avg_connections, 1
            )
            throughput_growth = (recent_avg_throughput - older_avg_throughput) / max(
                older_avg_throughput, 1
            )

            # Generate insights
            if connection_growth > 0.2:  # 20% growth
                insights.append(
                    PredictiveInsight(
                        insight_type="capacity_growth",
                        timestamp=datetime.now(),
                        prediction=f"Connection count growing at {connection_growth:.1%} rate",
                        confidence=min(abs(connection_growth), 0.9),
                        timeframe="1-2 weeks",
                        factors=["increasing user activity", "new features"],
                        recommendations=[
                            "Monitor connection pool capacity",
                            "Consider horizontal scaling",
                            "Implement connection limits",
                        ],
                    )
                )

            if throughput_growth > 0.3:  # 30% growth
                insights.append(
                    PredictiveInsight(
                        insight_type="throughput_growth",
                        timestamp=datetime.now(),
                        prediction=f"Message throughput growing at {throughput_growth:.1%} rate",
                        confidence=min(abs(throughput_growth), 0.9),
                        timeframe="1 week",
                        factors=["increased trading activity", "more real-time data"],
                        recommendations=[
                            "Optimize message processing",
                            "Consider message batching",
                            "Monitor bandwidth usage",
                        ],
                    )
                )

        return insights

    def export_analytics_report(self, hours: int = 24) -> Dict[str, Any]:
        """Export comprehensive analytics report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "time_period_hours": hours,
            "system_health": self.get_system_health_summary(),
            "performance_metrics": {
                conn_type.value: [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "avg_latency_ms": m.avg_latency_ms,
                        "error_rate": m.error_rate,
                        "message_throughput": m.message_throughput,
                        "active_connections": m.active_connections,
                    }
                    for m in self.get_performance_metrics(conn_type, hours)
                ]
                for conn_type in ConnectionType
            },
            "anomalies": [
                {
                    "connection_id": a.connection_id,
                    "anomaly_type": a.anomaly_type,
                    "severity": a.severity,
                    "timestamp": a.timestamp.isoformat(),
                    "description": a.description,
                    "confidence": a.confidence,
                }
                for a in self.get_anomalies(hours=hours)
            ],
            "recommendations": self.get_load_balancing_recommendations(),
            "insights": [
                {
                    "insight_type": i.insight_type,
                    "timestamp": i.timestamp.isoformat(),
                    "prediction": i.prediction,
                    "confidence": i.confidence,
                    "timeframe": i.timeframe,
                    "recommendations": i.recommendations,
                }
                for i in self.get_capacity_planning_insights()
            ],
        }

    async def shutdown(self):
        """Shutdown analytics engine"""
        try:
            if self._analytics_task and not self._analytics_task.done():
                self._analytics_task.cancel()
                try:
                    await self._analytics_task
                except asyncio.CancelledError:
                    pass

            if self._anomaly_detection_task and not self._anomaly_detection_task.done():
                self._anomaly_detection_task.cancel()
                try:
                    await self._anomaly_detection_task
                except asyncio.CancelledError:
                    pass
        except Exception as e:
            # Log error but don't raise to avoid blocking shutdown
            print(f"Error during analytics shutdown: {e}")
