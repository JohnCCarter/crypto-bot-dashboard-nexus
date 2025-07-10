"""
WebSocket Integration Manager

This module provides a unified interface for managing all WebSocket finalization
components including connection management, load balancing, analytics, and alerts.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from .websocket_alerts import NotificationConfig, WebSocketAlertManager
from .websocket_analytics import WebSocketAnalytics
from .websocket_connection_interface import (
    ConnectionConfig,
    ConnectionEventHandler,
    ConnectionState,
    ConnectionType,
    WebSocketConnectionInterface,
)
from .websocket_in_memory_store import InMemoryConnectionStore
from .websocket_load_balancer import LoadBalancingStrategy, WebSocketLoadBalancer


@dataclass
class IntegrationConfig:
    """Configuration for WebSocket integration manager"""

    max_connections: int = 1000
    health_check_interval: int = 30
    analytics_interval: int = 60
    alert_check_interval: int = 30
    default_load_balancing_strategy: LoadBalancingStrategy = (
        LoadBalancingStrategy.ROUND_ROBIN
    )
    enable_analytics: bool = True
    enable_alerts: bool = True
    enable_load_balancing: bool = True
    notification_config: Optional[NotificationConfig] = None
    cluster_node_id: Optional[str] = None


class WebSocketIntegrationEventHandler(ConnectionEventHandler):
    """Event handler for WebSocket integration manager"""

    def __init__(self, manager: "WebSocketIntegrationManager"):
        self.manager = manager

    async def on_connect(self, connection_id: str, connection_type: ConnectionType):
        """Handle connection event"""
        await self.manager._handle_connection_event(
            "connect", connection_id, connection_type
        )

    async def on_disconnect(self, connection_id: str, reason: str):
        """Handle disconnection event"""
        await self.manager._handle_connection_event(
            "disconnect", connection_id, reason=reason
        )

    async def on_message(self, connection_id: str, message: Any):
        """Handle message event"""
        await self.manager._handle_connection_event(
            "message", connection_id, message=message
        )

    async def on_error(self, connection_id: str, error: Exception):
        """Handle error event"""
        await self.manager._handle_connection_event("error", connection_id, error=error)

    async def on_reconnect(self, connection_id: str, attempt: int):
        """Handle reconnection event"""
        await self.manager._handle_connection_event(
            "reconnect", connection_id, attempt=attempt
        )


class WebSocketIntegrationManager:
    """
    Unified WebSocket integration manager.

    This class provides a single interface for managing all WebSocket finalization
    components including:
    - Connection state management
    - Load balancing
    - Performance analytics
    - Real-time alerts
    - Cluster coordination
    """

    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize core components
        self.store = InMemoryConnectionStore(
            max_connections=config.max_connections, cleanup_interval=300
        )

        self.analytics = (
            WebSocketAnalytics(self.store) if config.enable_analytics else None
        )
        self.load_balancer = (
            WebSocketLoadBalancer(
                self.store,
                default_strategy=config.default_load_balancing_strategy,
                health_check_interval=config.health_check_interval,
            )
            if config.enable_load_balancing
            else None
        )
        self.alert_manager = (
            WebSocketAlertManager(
                self.store, notification_config=config.notification_config
            )
            if config.enable_alerts
            else None
        )

        # Event handler
        self.event_handler = WebSocketIntegrationEventHandler(self)

        # Connection registry
        self._connections: Dict[str, WebSocketConnectionInterface] = {}
        self._connection_configs: Dict[str, ConnectionConfig] = {}

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._reporting_task: Optional[asyncio.Task] = None

        # Performance tracking
        self._start_time = datetime.now()
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0

        self.logger.info("WebSocket Integration Manager initialized")

    async def start(self):
        """Start the integration manager"""
        try:
            # Start background monitoring
            self._start_background_tasks()

            # Register cluster node if configured
            if self.config.cluster_node_id:
                await self._register_cluster_node()

            self.logger.info("WebSocket Integration Manager started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start WebSocket Integration Manager: {e}")
            raise

    def _start_background_tasks(self):
        """Start background monitoring and reporting tasks"""

        async def monitoring_loop():
            while True:
                try:
                    await asyncio.sleep(60)  # Run every minute
                    await self._perform_system_monitoring()
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")

        async def reporting_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # Run every 5 minutes
                    await self._generate_system_report()
                except Exception as e:
                    self.logger.error(f"Error in reporting loop: {e}")

        loop = asyncio.get_event_loop()
        self._monitoring_task = loop.create_task(monitoring_loop())
        self._reporting_task = loop.create_task(reporting_loop())

    async def _register_cluster_node(self):
        """Register this node in the cluster"""
        node_info = {
            "host": "localhost",  # TODO: Get actual host
            "port": 8001,  # TODO: Get actual port
            "node_type": "websocket_manager",
            "capabilities": [
                "connection_management",
                "load_balancing",
                "analytics",
                "alerts",
            ],
            "load_factor": 1.0,
        }

        if self.config.cluster_node_id:
            await self.store.register_cluster_node(
                self.config.cluster_node_id, node_info
            )
        self.logger.info(f"Registered cluster node: {self.config.cluster_node_id}")

    async def register_connection(
        self, connection: WebSocketConnectionInterface, config: ConnectionConfig
    ) -> bool:
        """Register a new WebSocket connection"""
        try:
            # Add event handler to connection
            connection.add_event_handler(self.event_handler)

            # Register in store
            success = await self.store.register_connection(
                connection.connection_id,
                config.connection_type,
                config,
                self.config.cluster_node_id,
            )

            if success:
                # Store connection reference
                self._connections[connection.connection_id] = connection
                self._connection_configs[connection.connection_id] = config

                # Set load balancer weight if configured
                if self.load_balancer and config.load_balancing_weight != 1.0:
                    self.load_balancer.set_connection_weight(
                        connection.connection_id, config.load_balancing_weight
                    )

                self.logger.info(f"Registered connection: {connection.connection_id}")
                return True
            else:
                self.logger.error(
                    f"Failed to register connection: {connection.connection_id}"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Error registering connection {connection.connection_id}: {e}"
            )
            return False

    async def unregister_connection(self, connection_id: str) -> bool:
        """Unregister a WebSocket connection"""
        try:
            # Remove from store
            await self.store.deactivate_connection(connection_id, "unregistered")

            # Remove from local registry
            if connection_id in self._connections:
                del self._connections[connection_id]

            if connection_id in self._connection_configs:
                del self._connection_configs[connection_id]

            self.logger.info(f"Unregistered connection: {connection_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error unregistering connection {connection_id}: {e}")
            return False

    async def get_connection(
        self,
        connection_type: ConnectionType,
        strategy: Optional[LoadBalancingStrategy] = None,
    ) -> Optional[WebSocketConnectionInterface]:
        """Get best connection using load balancing"""
        try:
            if not self.load_balancer:
                # Fallback to simple selection
                connections = self.store.get_connections_by_type(
                    connection_type, active_only=True
                )
                return (
                    self._connections.get(connections[0].connection_id)
                    if connections
                    else None
                )

            # Use load balancer
            selected_record = await self.load_balancer.select_connection(
                connection_type, strategy
            )
            if selected_record:
                return self._connections.get(selected_record.connection_id)

            return None

        except Exception as e:
            self.logger.error(
                f"Error getting connection for type {connection_type.value}: {e}"
            )
            return None

    async def broadcast_message(
        self, message: Any, connection_type: Optional[ConnectionType] = None
    ) -> Dict[str, bool]:
        """Broadcast message to all connections of specified type"""
        results = {}

        try:
            connections = self._connections.values()

            if connection_type:
                connections = [
                    conn
                    for conn in connections
                    if self._connection_configs[conn.connection_id].connection_type
                    == connection_type
                ]

            for connection in connections:
                try:
                    success = await connection.send_message(message)
                    results[connection.connection_id] = success
                except Exception as e:
                    self.logger.error(
                        f"Error broadcasting to {connection.connection_id}: {e}"
                    )
                    results[connection.connection_id] = False

            return results

        except Exception as e:
            self.logger.error(f"Error in broadcast_message: {e}")
            return results

    async def _handle_connection_event(
        self, event_type: str, connection_id: str, **kwargs
    ):
        """Handle connection events"""
        try:
            # Update connection state in store
            if event_type == "connect":
                await self.store.update_connection_state(
                    connection_id, ConnectionState.CONNECTED
                )
            elif event_type == "disconnect":
                await self.store.update_connection_state(
                    connection_id, ConnectionState.DISCONNECTED
                )
            elif event_type == "error":
                await self.store.update_connection_state(
                    connection_id, ConnectionState.ERROR
                )

            # Update metrics
            connection = self._connections.get(connection_id)
            if connection:
                metrics_update = {}

                if event_type == "message":
                    metrics_update["messages_received"] = (
                        connection.metrics.messages_received + 1
                    )
                elif event_type == "error":
                    metrics_update["errors_count"] = connection.metrics.errors_count + 1
                elif event_type == "reconnect":
                    metrics_update["reconnect_attempts"] = (
                        connection.metrics.reconnect_attempts + 1
                    )

                if metrics_update:
                    await self.store.update_connection_metrics(
                        connection_id, metrics_update
                    )

            self.logger.debug(
                f"Handled {event_type} event for connection {connection_id}"
            )

        except Exception as e:
            self.logger.error(
                f"Error handling {event_type} event for {connection_id}: {e}"
            )

    async def _perform_system_monitoring(self):
        """Perform system-wide monitoring"""
        try:
            # Update cluster node heartbeat
            if self.config.cluster_node_id:
                await self.store.update_cluster_node_heartbeat(
                    self.config.cluster_node_id
                )

            # Check system health
            health_summary = self._get_system_health()

            # Trigger alerts for critical issues
            if health_summary["overall_health_score"] < 50 and self.alert_manager:
                # This would trigger an alert through the alert manager
                pass

            self.logger.debug("System monitoring completed")

        except Exception as e:
            self.logger.error(f"Error in system monitoring: {e}")

    async def _generate_system_report(self):
        """Generate comprehensive system report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
                "system_health": self._get_system_health(),
                "connection_stats": self.store.get_connection_stats(),
                "cluster_info": {
                    "node_id": self.config.cluster_node_id,
                    "total_nodes": len(self.store.get_cluster_nodes()),
                    "is_leader": False,  # TODO: Implement leader election
                },
            }

            # Add analytics if enabled
            if self.analytics:
                report["analytics"] = {
                    "performance_metrics": len(
                        self.analytics.get_performance_metrics()
                    ),
                    "anomalies": len(self.analytics.get_anomalies()),
                    "insights": len(self.analytics.get_capacity_planning_insights()),
                }

            # Add load balancer info if enabled
            if self.load_balancer:
                report["load_balancer"] = {
                    "strategy": self.load_balancer.default_strategy.value,
                    "performance": self.load_balancer.get_strategy_performance(),
                    "health_summary": self.load_balancer.get_health_summary(),
                }

            # Add alert info if enabled
            if self.alert_manager:
                report["alerts"] = self.alert_manager.get_alert_summary()

            # Log report summary
            self.logger.info(
                f"System Report: {report['system_health']['overall_health_score']:.1f}% health, "
                f"{report['connection_stats']['active_connections']} active connections"
            )

            return report

        except Exception as e:
            self.logger.error(f"Error generating system report: {e}")
            return None

    def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        try:
            if self.analytics:
                return self.analytics.get_system_health_summary()
            else:
                # Basic health calculation
                stats = self.store.get_connection_stats()
                active_connections = stats["active_connections"]
                total_connections = stats["total_connections"]

                health_score = (active_connections / max(total_connections, 1)) * 100

                return {
                    "overall_health_score": health_score,
                    "active_connections": active_connections,
                    "total_connections": total_connections,
                    "health_status": (
                        "good"
                        if health_score > 80
                        else "fair" if health_score > 50 else "poor"
                    ),
                }

        except Exception as e:
            self.logger.error(f"Error calculating system health: {e}")
            return {
                "overall_health_score": 0,
                "active_connections": 0,
                "total_connections": 0,
                "health_status": "unknown",
            }

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a connection"""
        try:
            connection = self._connections.get(connection_id)
            if not connection:
                return None

            record = self.store.get_connection(connection_id)
            if not record:
                return None

            info = {
                "connection_id": connection_id,
                "connection_type": record.connection_type.value,
                "state": record.state.value,
                "created_at": record.created_at.isoformat(),
                "last_updated": record.last_updated.isoformat(),
                "is_active": record.is_active,
                "cluster_node_id": record.cluster_node_id,
                "subscriptions": list(record.subscriptions),
                "metrics": {
                    "messages_sent": record.metrics.messages_sent,
                    "messages_received": record.metrics.messages_received,
                    "errors_count": record.metrics.errors_count,
                    "reconnect_attempts": record.metrics.reconnect_attempts,
                    "latency_ms": record.metrics.latency_ms,
                    "bandwidth_bytes": record.metrics.bandwidth_bytes,
                },
            }

            # Add health score if analytics enabled
            if self.analytics:
                info["health_score"] = self.analytics.get_connection_health_score(
                    connection_id
                )

            return info

        except Exception as e:
            self.logger.error(f"Error getting connection info for {connection_id}: {e}")
            return None

    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview for dashboard"""
        try:
            stats = self.store.get_connection_stats()

            overview = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
                "connections": {
                    "total": stats["total_connections"],
                    "active": stats["active_connections"],
                    "by_type": stats.get("by_type", {}),
                },
                "performance": {
                    "total_requests": self._total_requests,
                    "successful_requests": self._successful_requests,
                    "failed_requests": self._failed_requests,
                    "success_rate": self._successful_requests
                    / max(self._total_requests, 1),
                },
            }

            # Add health information
            health = self._get_system_health()
            overview["health"] = health

            # Add cluster information
            cluster_nodes = self.store.get_cluster_nodes()
            overview["cluster"] = {
                "node_id": self.config.cluster_node_id,
                "total_nodes": len(cluster_nodes),
                "nodes": [
                    {
                        "node_id": node.node_id,
                        "node_type": node.node_type,
                        "is_active": node.is_active,
                        "connection_count": node.connection_count,
                        "last_heartbeat": node.last_heartbeat.isoformat(),
                    }
                    for node in cluster_nodes
                ],
            }

            return overview

        except Exception as e:
            self.logger.error(f"Error getting system overview: {e}")
            return {}

    async def shutdown(self):
        """Shutdown the integration manager"""
        try:
            self.logger.info("Shutting down WebSocket Integration Manager...")

            # Cancel background tasks
            if self._monitoring_task and not self._monitoring_task.done():
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass

            if self._reporting_task and not self._reporting_task.done():
                self._reporting_task.cancel()
                try:
                    await self._reporting_task
                except asyncio.CancelledError:
                    pass

            # Shutdown components
            if self.analytics:
                try:
                    await self.analytics.shutdown()
                except Exception as e:
                    self.logger.error(f"Error shutting down analytics: {e}")

            if self.load_balancer:
                try:
                    await self.load_balancer.shutdown()
                except Exception as e:
                    self.logger.error(f"Error shutting down load balancer: {e}")

            if self.alert_manager:
                try:
                    await self.alert_manager.shutdown()
                except Exception as e:
                    self.logger.error(f"Error shutting down alert manager: {e}")

            # Shutdown store
            try:
                await self.store.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down store: {e}")

            # Close all connections
            for connection in self._connections.values():
                try:
                    await connection.disconnect("shutdown")
                except Exception as e:
                    self.logger.error(
                        f"Error disconnecting {connection.connection_id}: {e}"
                    )

            self.logger.info("WebSocket Integration Manager shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            # Don't raise to avoid blocking test shutdown
