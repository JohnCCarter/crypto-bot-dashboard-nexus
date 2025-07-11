"""
Load Balancer for WebSocket Connections

This module provides intelligent load balancing for WebSocket connections
with multiple strategies, health checking, and automatic failover.
"""

import asyncio
import random
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .websocket_connection_interface import (ConnectionConfig,
                                             ConnectionMetrics,
                                             ConnectionState, ConnectionType,
                                             WebSocketConnectionInterface)
from .websocket_in_memory_store import (ConnectionRecord,
                                        InMemoryConnectionStore)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_LOAD = "least_load"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_LATENCY = "least_latency"
    HEALTH_BASED = "health_based"
    ADAPTIVE = "adaptive"


@dataclass
class LoadBalancerMetrics:
    """Metrics for load balancer performance"""

    strategy: LoadBalancingStrategy
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def update_success(self, response_time_ms: float):
        """Update metrics for successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self._update_avg_response_time(response_time_ms)
        self.last_updated = datetime.now()

    def update_failure(self, response_time_ms: float):
        """Update metrics for failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self._update_avg_response_time(response_time_ms)
        self.last_updated = datetime.now()

    def _update_avg_response_time(self, response_time_ms: float):
        """Update average response time"""
        if self.total_requests == 1:
            self.avg_response_time_ms = response_time_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self.avg_response_time_ms = (
                alpha * response_time_ms + (1 - alpha) * self.avg_response_time_ms
            )

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        return self.successful_requests / max(self.total_requests, 1)

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        return self.failed_requests / max(self.total_requests, 1)


@dataclass
class HealthCheckResult:
    """Result of health check"""

    connection_id: str
    is_healthy: bool
    response_time_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    checks_performed: int = 0
    consecutive_failures: int = 0


class WebSocketLoadBalancer:
    """
    Intelligent load balancer for WebSocket connections.

    Features:
    - Multiple load balancing strategies
    - Automatic health checking
    - Connection failover
    - Performance monitoring
    - Adaptive strategy selection
    """

    def __init__(
        self,
        store: InMemoryConnectionStore,
        default_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
        health_check_interval: int = 30,
        health_check_timeout: int = 5,
    ):
        self.store = store
        self.default_strategy = default_strategy
        self.health_check_interval = health_check_interval
        self.health_check_timeout = health_check_timeout

        # Load balancing state
        self._current_indices: Dict[ConnectionType, int] = defaultdict(int)
        self._connection_weights: Dict[str, float] = {}
        self._health_check_results: Dict[str, HealthCheckResult] = {}
        self._strategy_metrics: Dict[LoadBalancingStrategy, LoadBalancerMetrics] = {}

        # Performance tracking
        self._request_history: deque = deque(maxlen=10000)
        self._strategy_performance: Dict[LoadBalancingStrategy, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )

        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._adaptive_strategy_task: Optional[asyncio.Task] = None

        # Initialize strategy metrics
        for strategy in LoadBalancingStrategy:
            self._strategy_metrics[strategy] = LoadBalancerMetrics(strategy=strategy)

        # Start background tasks
        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background health checking and adaptive strategy tasks"""

        async def health_check_loop():
            while True:
                try:
                    await asyncio.sleep(self.health_check_interval)
                    await self._perform_health_checks()
                except Exception as e:
                    print(f"Error in health check loop: {e}")

        async def adaptive_strategy_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # Run every 5 minutes
                    await self._update_adaptive_strategy()
                except Exception as e:
                    print(f"Error in adaptive strategy loop: {e}")

        loop = asyncio.get_event_loop()
        self._health_check_task = loop.create_task(health_check_loop())
        self._adaptive_strategy_task = loop.create_task(adaptive_strategy_loop())

    async def select_connection(
        self,
        connection_type: ConnectionType,
        strategy: Optional[LoadBalancingStrategy] = None,
        **kwargs,
    ) -> Optional[ConnectionRecord]:
        """Select best connection based on load balancing strategy"""
        if strategy is None:
            strategy = self.default_strategy

        connections = self.store.get_connections_by_type(
            connection_type, active_only=True
        )

        if not connections:
            return None

        # Filter out unhealthy connections
        healthy_connections = [
            conn
            for conn in connections
            if self._is_connection_healthy(conn.connection_id)
        ]

        if not healthy_connections:
            # Fallback to all connections if no healthy ones
            healthy_connections = connections

        start_time = time.time()

        try:
            if strategy == LoadBalancingStrategy.ROUND_ROBIN:
                selected = self._round_robin_select(
                    healthy_connections, connection_type
                )
            elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                selected = self._least_connections_select(healthy_connections)
            elif strategy == LoadBalancingStrategy.LEAST_LOAD:
                selected = self._least_load_select(healthy_connections)
            elif strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                selected = self._weighted_round_robin_select(healthy_connections)
            elif strategy == LoadBalancingStrategy.LEAST_LATENCY:
                selected = self._least_latency_select(healthy_connections)
            elif strategy == LoadBalancingStrategy.HEALTH_BASED:
                selected = self._health_based_select(healthy_connections)
            elif strategy == LoadBalancingStrategy.ADAPTIVE:
                selected = await self._adaptive_select(
                    healthy_connections, connection_type
                )
            else:
                selected = healthy_connections[0]  # Default fallback

            # Update metrics
            response_time = (time.time() - start_time) * 1000
            self._strategy_metrics[strategy].update_success(response_time)

            # Record request
            self._record_request(strategy, selected.connection_id, response_time, True)

            return selected

        except Exception as e:
            # Update failure metrics
            response_time = (time.time() - start_time) * 1000
            self._strategy_metrics[strategy].update_failure(response_time)

            # Record failed request
            self._record_request(strategy, None, response_time, False, str(e))

            # Fallback to simple round-robin
            return healthy_connections[0] if healthy_connections else None

    def _round_robin_select(
        self, connections: List[ConnectionRecord], connection_type: ConnectionType
    ) -> ConnectionRecord:
        """Round-robin selection"""
        if not connections:
            return None

        index = self._current_indices[connection_type] % len(connections)
        self._current_indices[connection_type] += 1

        return connections[index]

    def _least_connections_select(
        self, connections: List[ConnectionRecord]
    ) -> ConnectionRecord:
        """Select connection with least active connections"""
        if not connections:
            return None

        return min(
            connections,
            key=lambda c: c.metrics.messages_sent + c.metrics.messages_received,
        )

    def _least_load_select(
        self, connections: List[ConnectionRecord]
    ) -> ConnectionRecord:
        """Select connection with least load (messages sent)"""
        if not connections:
            return None

        return min(connections, key=lambda c: c.metrics.messages_sent)

    def _weighted_round_robin_select(
        self, connections: List[ConnectionRecord]
    ) -> ConnectionRecord:
        """Weighted round-robin selection based on connection weights"""
        if not connections:
            return None

        # Calculate total weight
        total_weight = sum(
            self._connection_weights.get(conn.connection_id, 1.0)
            for conn in connections
        )

        if total_weight <= 0:
            return connections[0]

        # Select based on weights
        random_value = random.uniform(0, total_weight)
        current_weight = 0

        for conn in connections:
            weight = self._connection_weights.get(conn.connection_id, 1.0)
            current_weight += weight

            if random_value <= current_weight:
                return conn

        return connections[0]  # Fallback

    def _least_latency_select(
        self, connections: List[ConnectionRecord]
    ) -> ConnectionRecord:
        """Select connection with lowest latency"""
        if not connections:
            return None

        # Filter connections with valid latency data
        valid_connections = [
            conn for conn in connections if conn.metrics.latency_ms > 0
        ]

        if not valid_connections:
            return connections[0]  # Fallback to first connection

        return min(valid_connections, key=lambda c: c.metrics.latency_ms)

    def _health_based_select(
        self, connections: List[ConnectionRecord]
    ) -> ConnectionRecord:
        """Select connection based on health scores"""
        if not connections:
            return None

        # Calculate health scores
        health_scores = []
        for conn in connections:
            health_result = self._health_check_results.get(conn.connection_id)
            if health_result and health_result.is_healthy:
                # Prefer connections with lower consecutive failures
                score = 100 - (health_result.consecutive_failures * 10)
                health_scores.append((conn, max(score, 0)))
            else:
                health_scores.append((conn, 0))

        # Select connection with highest health score
        return max(health_scores, key=lambda x: x[1])[0]

    async def _adaptive_select(
        self, connections: List[ConnectionRecord], connection_type: ConnectionType
    ) -> ConnectionRecord:
        """Adaptive selection based on performance history"""
        if not connections:
            return None

        # Analyze recent performance for each strategy
        strategy_performance = {}

        for strategy in LoadBalancingStrategy:
            if strategy == LoadBalancingStrategy.ADAPTIVE:
                continue

            metrics = self._strategy_metrics[strategy]
            if metrics.total_requests > 10:  # Need minimum data
                strategy_performance[strategy] = {
                    "success_rate": metrics.success_rate,
                    "avg_response_time": metrics.avg_response_time_ms,
                    "total_requests": metrics.total_requests,
                }

        if not strategy_performance:
            # Fallback to round-robin if no performance data
            return self._round_robin_select(connections, connection_type)

        # Select best performing strategy
        best_strategy = max(
            strategy_performance.items(),
            key=lambda x: x[1]["success_rate"]
            * (1 / max(x[1]["avg_response_time"], 1)),
        )[0]

        # Use the best strategy to select connection
        if best_strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(connections, connection_type)
        elif best_strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(connections)
        elif best_strategy == LoadBalancingStrategy.LEAST_LOAD:
            return self._least_load_select(connections)
        elif best_strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(connections)
        elif best_strategy == LoadBalancingStrategy.LEAST_LATENCY:
            return self._least_latency_select(connections)
        elif best_strategy == LoadBalancingStrategy.HEALTH_BASED:
            return self._health_based_select(connections)
        else:
            return connections[0]

    def _is_connection_healthy(self, connection_id: str) -> bool:
        """Check if connection is healthy"""
        health_result = self._health_check_results.get(connection_id)
        if not health_result:
            return True  # Assume healthy if no health check data

        # Consider unhealthy if too many consecutive failures
        if health_result.consecutive_failures >= 3:
            return False

        # Consider unhealthy if last check was too long ago
        time_since_check = datetime.now() - health_result.timestamp
        if time_since_check > timedelta(minutes=5):
            return False

        return health_result.is_healthy

    async def _perform_health_checks(self):
        """Perform health checks on all active connections"""
        active_connections = self.store.get_active_connections()

        for connection in active_connections:
            try:
                # Simple health check - verify connection is still active
                is_healthy = connection.state in [
                    ConnectionState.CONNECTED,
                    ConnectionState.AUTHENTICATED,
                ]

                # Check if connection has recent activity
                time_since_activity = datetime.now() - connection.metrics.last_activity
                if time_since_activity > timedelta(minutes=10):
                    is_healthy = False

                # Update health check result
                previous_result = self._health_check_results.get(
                    connection.connection_id
                )
                consecutive_failures = 0

                if previous_result:
                    consecutive_failures = previous_result.consecutive_failures
                    if not is_healthy:
                        consecutive_failures += 1
                    else:
                        consecutive_failures = 0

                health_result = HealthCheckResult(
                    connection_id=connection.connection_id,
                    is_healthy=is_healthy,
                    response_time_ms=connection.metrics.latency_ms,
                    timestamp=datetime.now(),
                    checks_performed=1,
                    consecutive_failures=consecutive_failures,
                )

                self._health_check_results[connection.connection_id] = health_result

            except Exception as e:
                # Mark as unhealthy on error
                health_result = HealthCheckResult(
                    connection_id=connection.connection_id,
                    is_healthy=False,
                    response_time_ms=0.0,
                    error_message=str(e),
                    timestamp=datetime.now(),
                    checks_performed=1,
                    consecutive_failures=1,
                )

                self._health_check_results[connection.connection_id] = health_result

    async def _update_adaptive_strategy(self):
        """Update adaptive strategy based on performance history"""
        # Analyze performance of each strategy
        strategy_scores = {}

        for strategy, metrics in self._strategy_metrics.items():
            if metrics.total_requests < 10:
                continue

            # Calculate composite score
            success_weight = 0.6
            response_time_weight = 0.4

            success_score = metrics.success_rate
            response_time_score = 1.0 / max(metrics.avg_response_time_ms, 1.0)

            composite_score = (
                success_weight * success_score
                + response_time_weight * response_time_score
            )

            strategy_scores[strategy] = composite_score

        # Update default strategy if better one found
        if strategy_scores:
            best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]
            if best_strategy != self.default_strategy:
                print(
                    f"Adaptive strategy: switching from {self.default_strategy.value} to {best_strategy.value}"
                )
                self.default_strategy = best_strategy

    def _record_request(
        self,
        strategy: LoadBalancingStrategy,
        connection_id: Optional[str],
        response_time_ms: float,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """Record request for performance tracking"""
        request_record = {
            "timestamp": datetime.now(),
            "strategy": strategy.value,
            "connection_id": connection_id,
            "response_time_ms": response_time_ms,
            "success": success,
            "error_message": error_message,
        }

        self._request_history.append(request_record)
        self._strategy_performance[strategy].append(request_record)

    def set_connection_weight(self, connection_id: str, weight: float):
        """Set weight for weighted round-robin"""
        self._connection_weights[connection_id] = max(weight, 0.1)

    def get_connection_weight(self, connection_id: str) -> float:
        """Get weight for connection"""
        return self._connection_weights.get(connection_id, 1.0)

    def get_load_distribution(self) -> Dict[str, float]:
        """Get current load distribution across connections"""
        distribution = {}

        for conn_type in ConnectionType:
            connections = self.store.get_connections_by_type(
                conn_type, active_only=True
            )

            if not connections:
                distribution[conn_type.value] = 0.0
                continue

            total_messages = sum(conn.metrics.messages_sent for conn in connections)
            distribution[conn_type.value] = total_messages

        return distribution

    def get_strategy_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all strategies"""
        performance = {}

        for strategy, metrics in self._strategy_metrics.items():
            performance[strategy.value] = {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.success_rate,
                "failure_rate": metrics.failure_rate,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "last_updated": metrics.last_updated.isoformat(),
            }

        return performance

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all connections"""
        active_connections = self.store.get_active_connections()

        total_connections = len(active_connections)
        healthy_connections = sum(
            1
            for conn in active_connections
            if self._is_connection_healthy(conn.connection_id)
        )

        health_results = []
        for conn in active_connections:
            health_result = self._health_check_results.get(conn.connection_id)
            if health_result:
                health_results.append(
                    {
                        "connection_id": conn.connection_id,
                        "is_healthy": health_result.is_healthy,
                        "consecutive_failures": health_result.consecutive_failures,
                        "last_check": health_result.timestamp.isoformat(),
                        "response_time_ms": health_result.response_time_ms,
                    }
                )

        return {
            "total_connections": total_connections,
            "healthy_connections": healthy_connections,
            "unhealthy_connections": total_connections - healthy_connections,
            "health_rate": healthy_connections / max(total_connections, 1),
            "health_results": health_results,
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get load balancing recommendations"""
        recommendations = []

        # Check for unhealthy connections
        health_summary = self.get_health_summary()
        if health_summary["health_rate"] < 0.8:
            recommendations.append(
                {
                    "type": "health_warning",
                    "priority": "high",
                    "description": f"Only {health_summary['health_rate']:.1%} of connections are healthy",
                    "recommendation": "Investigate connection health issues and implement failover",
                }
            )

        # Check strategy performance
        strategy_performance = self.get_strategy_performance()
        for strategy, metrics in strategy_performance.items():
            if metrics["total_requests"] > 50 and metrics["success_rate"] < 0.9:
                recommendations.append(
                    {
                        "type": "strategy_performance",
                        "priority": "medium",
                        "description": f"Strategy {strategy} has {metrics['success_rate']:.1%} success rate",
                        "recommendation": f"Consider switching from {strategy} strategy",
                    }
                )

        # Check load distribution
        load_distribution = self.get_load_distribution()
        for conn_type, load in load_distribution.items():
            if load == 0:
                recommendations.append(
                    {
                        "type": "load_distribution",
                        "priority": "low",
                        "description": f"No load on {conn_type} connections",
                        "recommendation": "Consider consolidating or removing unused connections",
                    }
                )

        return recommendations

    async def shutdown(self):
        """Shutdown load balancer"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self._adaptive_strategy_task:
            self._adaptive_strategy_task.cancel()
            try:
                await self._adaptive_strategy_task
            except asyncio.CancelledError:
                pass
