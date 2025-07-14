"""
In-Memory Store for WebSocket Connection State Management

This module provides an in-memory store for managing WebSocket connection states,
metrics, and clustering information. Designed for high-performance, stateless
connection management.
"""

import asyncio
import json
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from .websocket_connection_interface import (
    ConnectionConfig,
    ConnectionMetrics,
    ConnectionState,
    ConnectionType,
    WebSocketConnectionInterface,
)


@dataclass
class ConnectionRecord:
    """Record for storing connection information"""

    connection_id: str
    connection_type: ConnectionType
    state: ConnectionState
    config: ConnectionConfig
    metrics: ConnectionMetrics
    created_at: datetime
    last_updated: datetime
    cluster_node_id: Optional[str] = None
    is_active: bool = True
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClusterNodeInfo:
    """Information about a cluster node"""

    node_id: str
    host: str
    port: int
    node_type: str
    capabilities: List[str]
    load_factor: float
    last_heartbeat: datetime
    is_active: bool = True
    connection_count: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)


class InMemoryConnectionStore:
    """
    In-memory store for WebSocket connection state management.

    Thread-safe implementation with support for:
    - Connection pooling and load balancing
    - Cluster node management
    - Performance metrics tracking
    - Automatic cleanup of stale connections
    """

    def __init__(self, max_connections: int = 1000, cleanup_interval: int = 300):
        self.max_connections = max_connections
        self.cleanup_interval = cleanup_interval

        # Thread-safe storage
        self._connections: Dict[str, ConnectionRecord] = {}
        self._connections_by_type: Dict[ConnectionType, Set[str]] = defaultdict(set)
        self._connections_by_node: Dict[str, Set[str]] = defaultdict(set)
        self._cluster_nodes: Dict[str, ClusterNodeInfo] = {}

        # Performance tracking
        self._metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self._connection_stats = {
            "total_created": 0,
            "total_closed": 0,
            "active_connections": 0,
            "errors_count": 0,
        }

        # Threading
        self._lock = threading.RLock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._executor = ThreadPoolExecutor(max_workers=4)

        # Start cleanup task
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Start background cleanup task"""

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                    await self._cleanup_stale_connections()
                except Exception as e:
                    print(f"Error in cleanup loop: {e}")

        loop = asyncio.get_event_loop()
        self._cleanup_task = loop.create_task(cleanup_loop())

    async def _cleanup_stale_connections(self):
        """Clean up stale connections"""
        with self._lock:
            current_time = datetime.now()
            stale_threshold = timedelta(minutes=30)

            connections_to_remove = []
            for conn_id, record in self._connections.items():
                if not record.is_active:
                    continue

                # Check if connection is stale
                time_since_update = current_time - record.last_updated
                if time_since_update > stale_threshold:
                    connections_to_remove.append(conn_id)

            # Remove stale connections
            for conn_id in connections_to_remove:
                await self._remove_connection_internal(conn_id, "stale_cleanup")

    async def register_connection(
        self,
        connection_id: str,
        connection_type: ConnectionType,
        config: ConnectionConfig,
        cluster_node_id: Optional[str] = None,
    ) -> bool:
        """Register a new connection"""
        with self._lock:
            if connection_id in self._connections:
                return False

            if len(self._connections) >= self.max_connections:
                # Remove oldest inactive connection
                await self._remove_oldest_inactive_connection()

            # Create connection record
            record = ConnectionRecord(
                connection_id=connection_id,
                connection_type=connection_type,
                state=ConnectionState.DISCONNECTED,
                config=config,
                metrics=ConnectionMetrics(
                    connection_id=connection_id, connection_type=connection_type
                ),
                created_at=datetime.now(),
                last_updated=datetime.now(),
                cluster_node_id=cluster_node_id,
            )

            # Store connection
            self._connections[connection_id] = record
            self._connections_by_type[connection_type].add(connection_id)

            if cluster_node_id:
                self._connections_by_node[cluster_node_id].add(connection_id)

            self._connection_stats["total_created"] += 1
            self._connection_stats["active_connections"] += 1

            return True

    async def update_connection_state(
        self,
        connection_id: str,
        state: ConnectionState,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update connection state"""
        with self._lock:
            if connection_id not in self._connections:
                return False

            record = self._connections[connection_id]
            record.state = state
            record.last_updated = datetime.now()

            if metadata:
                record.metadata.update(metadata)

            # Update metrics
            if state == ConnectionState.ERROR:
                record.metrics.increment_errors()
                self._connection_stats["errors_count"] += 1

            return True

    async def update_connection_metrics(
        self, connection_id: str, metrics_update: Dict[str, Any]
    ) -> bool:
        """Update connection metrics"""
        with self._lock:
            if connection_id not in self._connections:
                return False

            record = self._connections[connection_id]

            # Update metrics
            for key, value in metrics_update.items():
                if hasattr(record.metrics, key):
                    setattr(record.metrics, key, value)

            record.metrics.update_activity()
            record.last_updated = datetime.now()

            # Store in history
            self._metrics_history[connection_id].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "metrics": asdict(record.metrics),
                }
            )

            return True

    async def add_subscription(self, connection_id: str, channel: str) -> bool:
        """Add subscription to connection"""
        with self._lock:
            if connection_id not in self._connections:
                return False

            record = self._connections[connection_id]
            record.subscriptions.add(channel)
            record.last_updated = datetime.now()

            return True

    async def remove_subscription(self, connection_id: str, channel: str) -> bool:
        """Remove subscription from connection"""
        with self._lock:
            if connection_id not in self._connections:
                return False

            record = self._connections[connection_id]
            record.subscriptions.discard(channel)
            record.last_updated = datetime.now()

            return True

    async def deactivate_connection(
        self, connection_id: str, reason: str = "manual"
    ) -> bool:
        """Deactivate a connection"""
        with self._lock:
            if connection_id not in self._connections:
                return False

            record = self._connections[connection_id]
            record.is_active = False
            record.state = ConnectionState.DISCONNECTED
            record.last_updated = datetime.now()

            self._connection_stats["active_connections"] -= 1

            return True

    async def _remove_connection_internal(
        self, connection_id: str, reason: str = "removed"
    ):
        """Internal method to remove connection"""
        if connection_id not in self._connections:
            return

        record = self._connections[connection_id]

        # Remove from type index
        self._connections_by_type[record.connection_type].discard(connection_id)

        # Remove from node index
        if record.cluster_node_id:
            self._connections_by_node[record.cluster_node_id].discard(connection_id)

        # Remove from main storage
        del self._connections[connection_id]

        # Clean up metrics history
        if connection_id in self._metrics_history:
            del self._metrics_history[connection_id]

        self._connection_stats["total_closed"] += 1

    async def _remove_oldest_inactive_connection(self):
        """Remove oldest inactive connection when at capacity"""
        oldest_inactive = None
        oldest_time = None

        for conn_id, record in self._connections.items():
            if not record.is_active:
                if oldest_inactive is None or record.last_updated < oldest_time:
                    oldest_inactive = conn_id
                    oldest_time = record.last_updated

        if oldest_inactive:
            await self._remove_connection_internal(oldest_inactive, "capacity_limit")

    def get_connection(self, connection_id: str) -> Optional[ConnectionRecord]:
        """Get connection record by ID"""
        with self._lock:
            return self._connections.get(connection_id)

    def get_connections_by_type(
        self, connection_type: ConnectionType, active_only: bool = True
    ) -> List[ConnectionRecord]:
        """Get connections by type"""
        with self._lock:
            conn_ids = self._connections_by_type.get(connection_type, set())
            connections = []

            for conn_id in conn_ids:
                record = self._connections.get(conn_id)
                if record and (not active_only or record.is_active):
                    connections.append(record)

            return connections

    def get_connections_by_node(
        self, cluster_node_id: str, active_only: bool = True
    ) -> List[ConnectionRecord]:
        """Get connections by cluster node"""
        with self._lock:
            conn_ids = self._connections_by_node.get(cluster_node_id, set())
            connections = []

            for conn_id in conn_ids:
                record = self._connections.get(conn_id)
                if record and (not active_only or record.is_active):
                    connections.append(record)

            return connections

    def get_active_connections(self) -> List[ConnectionRecord]:
        """Get all active connections"""
        with self._lock:
            return [record for record in self._connections.values() if record.is_active]

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        with self._lock:
            stats = self._connection_stats.copy()

            # Add type-specific stats
            stats["by_type"] = {}
            for conn_type in ConnectionType:
                active_count = len(
                    [
                        conn_id
                        for conn_id in self._connections_by_type[conn_type]
                        if self._connections[conn_id].is_active
                    ]
                )
                stats["by_type"][conn_type.value] = active_count

            # Add cluster stats
            stats["cluster_nodes"] = len(self._cluster_nodes)
            stats["total_connections"] = len(self._connections)

            return stats

    def get_metrics_history(
        self, connection_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get metrics history for connection"""
        with self._lock:
            history = self._metrics_history.get(connection_id, deque())
            return list(history)[-limit:]

    # Cluster management methods
    async def register_cluster_node(
        self, node_id: str, node_info: Dict[str, Any]
    ) -> bool:
        """Register a cluster node"""
        with self._lock:
            if node_id in self._cluster_nodes:
                return False

            cluster_node = ClusterNodeInfo(
                node_id=node_id,
                host=node_info.get("host", ""),
                port=node_info.get("port", 0),
                node_type=node_info.get("node_type", "worker"),
                capabilities=node_info.get("capabilities", []),
                load_factor=node_info.get("load_factor", 1.0),
                last_heartbeat=datetime.now(),
            )

            self._cluster_nodes[node_id] = cluster_node
            return True

    async def unregister_cluster_node(self, node_id: str) -> bool:
        """Unregister a cluster node"""
        with self._lock:
            if node_id not in self._cluster_nodes:
                return False

            # Deactivate all connections for this node
            for conn_id in self._connections_by_node.get(node_id, set()):
                await self.deactivate_connection(conn_id, "node_unregistered")

            del self._cluster_nodes[node_id]
            return True

    async def update_cluster_node_heartbeat(self, node_id: str) -> bool:
        """Update cluster node heartbeat"""
        with self._lock:
            if node_id not in self._cluster_nodes:
                return False

            node = self._cluster_nodes[node_id]
            node.last_heartbeat = datetime.now()
            node.connection_count = len(self._connections_by_node.get(node_id, set()))

            return True

    def get_cluster_nodes(self) -> List[ClusterNodeInfo]:
        """Get all cluster nodes"""
        with self._lock:
            return list(self._cluster_nodes.values())

    def get_cluster_node(self, node_id: str) -> Optional[ClusterNodeInfo]:
        """Get specific cluster node"""
        with self._lock:
            return self._cluster_nodes.get(node_id)

    # Load balancing methods
    def get_best_connection(
        self, connection_type: ConnectionType, strategy: str = "round_robin"
    ) -> Optional[ConnectionRecord]:
        """Get best connection for load balancing"""
        with self._lock:
            active_connections = self.get_connections_by_type(
                connection_type, active_only=True
            )

            if not active_connections:
                return None

            if strategy == "round_robin":
                # Simple round-robin based on creation time
                return min(active_connections, key=lambda x: x.created_at)

            elif strategy == "least_loaded":
                # Choose connection with least messages
                return min(active_connections, key=lambda x: x.metrics.messages_sent)

            elif strategy == "lowest_latency":
                # Choose connection with lowest latency
                return min(active_connections, key=lambda x: x.metrics.latency_ms)

            else:
                # Default to first available
                return active_connections[0]

    def get_load_distribution(self) -> Dict[str, float]:
        """Get load distribution across connections"""
        with self._lock:
            distribution = {}

            for conn_type in ConnectionType:
                connections = self.get_connections_by_type(conn_type, active_only=True)
                total_messages = sum(conn.metrics.messages_sent for conn in connections)
                distribution[conn_type.value] = total_messages

            return distribution

    # Serialization methods
    def to_dict(self) -> Dict[str, Any]:
        """Convert store to dictionary for serialization"""
        with self._lock:
            return {
                "connections": {
                    conn_id: {
                        "connection_id": record.connection_id,
                        "connection_type": record.connection_type.value,
                        "state": record.state.value,
                        "created_at": record.created_at.isoformat(),
                        "last_updated": record.last_updated.isoformat(),
                        "cluster_node_id": record.cluster_node_id,
                        "is_active": record.is_active,
                        "subscriptions": list(record.subscriptions),
                        "metadata": record.metadata,
                        "metrics": asdict(record.metrics),
                    }
                    for conn_id, record in self._connections.items()
                },
                "cluster_nodes": {
                    node_id: {
                        "node_id": node.node_id,
                        "host": node.host,
                        "port": node.port,
                        "node_type": node.node_type,
                        "capabilities": node.capabilities,
                        "load_factor": node.load_factor,
                        "last_heartbeat": node.last_heartbeat.isoformat(),
                        "is_active": node.is_active,
                        "connection_count": node.connection_count,
                        "metrics": node.metrics,
                    }
                    for node_id, node in self._cluster_nodes.items()
                },
                "stats": self.get_connection_stats(),
            }

    def from_dict(self, data: Dict[str, Any]):
        """Load store from dictionary"""
        with self._lock:
            # Clear existing data
            self._connections.clear()
            self._connections_by_type.clear()
            self._connections_by_node.clear()
            self._cluster_nodes.clear()

            # Load connections
            for conn_id, conn_data in data.get("connections", {}).items():
                record = ConnectionRecord(
                    connection_id=conn_data["connection_id"],
                    connection_type=ConnectionType(conn_data["connection_type"]),
                    state=ConnectionState(conn_data["state"]),
                    config=ConnectionConfig(
                        url="",
                        connection_type=ConnectionType(conn_data["connection_type"]),
                    ),
                    metrics=ConnectionMetrics(
                        connection_id=conn_data["connection_id"],
                        connection_type=ConnectionType(conn_data["connection_type"]),
                    ),
                    created_at=datetime.fromisoformat(conn_data["created_at"]),
                    last_updated=datetime.fromisoformat(conn_data["last_updated"]),
                    cluster_node_id=conn_data.get("cluster_node_id"),
                    is_active=conn_data["is_active"],
                    subscriptions=set(conn_data["subscriptions"]),
                    metadata=conn_data["metadata"],
                )

                self._connections[conn_id] = record
                self._connections_by_type[record.connection_type].add(conn_id)

                if record.cluster_node_id:
                    self._connections_by_node[record.cluster_node_id].add(conn_id)

            # Load cluster nodes
            for node_id, node_data in data.get("cluster_nodes", {}).items():
                node = ClusterNodeInfo(
                    node_id=node_data["node_id"],
                    host=node_data["host"],
                    port=node_data["port"],
                    node_type=node_data["node_type"],
                    capabilities=node_data["capabilities"],
                    load_factor=node_data["load_factor"],
                    last_heartbeat=datetime.fromisoformat(node_data["last_heartbeat"]),
                    is_active=node_data["is_active"],
                    connection_count=node_data["connection_count"],
                    metrics=node_data["metrics"],
                )

                self._cluster_nodes[node_id] = node

    async def shutdown(self):
        """Shutdown the store and cleanup resources"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self._executor.shutdown(wait=True)

        # Deactivate all connections
        with self._lock:
            for conn_id in list(self._connections.keys()):
                await self.deactivate_connection(conn_id, "shutdown")
