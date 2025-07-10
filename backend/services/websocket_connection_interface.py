"""
WebSocket Connection Interface for Stateless Management

This module provides interfaces and base classes for managing WebSocket connections
in a stateless, clusterable manner. Supports connection pooling, load balancing,
and advanced analytics.
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class ConnectionState(Enum):
    """WebSocket connection states"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class ConnectionType(Enum):
    """Types of WebSocket connections"""

    MARKET_DATA = "market_data"
    USER_DATA = "user_data"
    TRADING = "trading"
    SYSTEM = "system"


@dataclass
class ConnectionMetrics:
    """Metrics for connection performance monitoring"""

    connection_id: str
    connection_type: ConnectionType
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    messages_sent: int = 0
    messages_received: int = 0
    errors_count: int = 0
    reconnect_attempts: int = 0
    latency_ms: float = 0.0
    bandwidth_bytes: int = 0

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    def increment_messages_sent(self, count: int = 1):
        """Increment sent message counter"""
        self.messages_sent += count
        self.update_activity()

    def increment_messages_received(self, count: int = 1):
        """Increment received message counter"""
        self.messages_received += count
        self.update_activity()

    def increment_errors(self, count: int = 1):
        """Increment error counter"""
        self.errors_count += count
        self.update_activity()

    def increment_reconnect_attempts(self):
        """Increment reconnect attempts counter"""
        self.reconnect_attempts += 1
        self.update_activity()

    def update_latency(self, latency_ms: float):
        """Update connection latency"""
        self.latency_ms = latency_ms
        self.update_activity()

    def update_bandwidth(self, bytes_transferred: int):
        """Update bandwidth usage"""
        self.bandwidth_bytes += bytes_transferred
        self.update_activity()


@dataclass
class ConnectionConfig:
    """Configuration for WebSocket connections"""

    url: str
    connection_type: ConnectionType
    max_reconnect_attempts: int = 5
    reconnect_delay_seconds: float = 1.0
    heartbeat_interval_seconds: float = 30.0
    connection_timeout_seconds: float = 10.0
    message_timeout_seconds: float = 5.0
    max_message_size_bytes: int = 1024 * 1024  # 1MB
    enable_compression: bool = True
    enable_heartbeat: bool = True
    cluster_node_id: Optional[str] = None
    load_balancing_weight: float = 1.0


class ConnectionEventHandler(ABC):
    """Abstract base class for connection event handlers"""

    @abstractmethod
    async def on_connect(self, connection_id: str, connection_type: ConnectionType):
        """Called when connection is established"""
        pass

    @abstractmethod
    async def on_disconnect(self, connection_id: str, reason: str):
        """Called when connection is disconnected"""
        pass

    @abstractmethod
    async def on_message(self, connection_id: str, message: Any):
        """Called when message is received"""
        pass

    @abstractmethod
    async def on_error(self, connection_id: str, error: Exception):
        """Called when connection error occurs"""
        pass

    @abstractmethod
    async def on_reconnect(self, connection_id: str, attempt: int):
        """Called when reconnection is attempted"""
        pass


class WebSocketConnectionInterface(ABC):
    """Abstract interface for WebSocket connection management"""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connection_id = str(uuid.uuid4())
        self.state = ConnectionState.DISCONNECTED
        self.metrics = ConnectionMetrics(
            connection_id=self.connection_id, connection_type=config.connection_type
        )
        self._event_handlers: List[ConnectionEventHandler] = []
        self._message_handlers: Dict[str, Callable] = {}
        self._last_heartbeat = None
        self._reconnect_task: Optional[asyncio.Task] = None

    @abstractmethod
    async def connect(self) -> bool:
        """Establish WebSocket connection"""
        pass

    @abstractmethod
    async def disconnect(self, reason: str = "manual"):
        """Close WebSocket connection"""
        pass

    @abstractmethod
    async def send_message(self, message: Any) -> bool:
        """Send message through WebSocket"""
        pass

    @abstractmethod
    async def subscribe(self, channel: str, **kwargs) -> bool:
        """Subscribe to WebSocket channel"""
        pass

    @abstractmethod
    async def unsubscribe(self, channel: str) -> bool:
        """Unsubscribe from WebSocket channel"""
        pass

    def add_event_handler(self, handler: ConnectionEventHandler):
        """Add event handler"""
        self._event_handlers.append(handler)

    def remove_event_handler(self, handler: ConnectionEventHandler):
        """Remove event handler"""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    def add_message_handler(self, message_type: str, handler: Callable):
        """Add message type handler"""
        self._message_handlers[message_type] = handler

    async def _notify_event_handlers(self, event: str, *args, **kwargs):
        """Notify all event handlers of an event"""
        for handler in self._event_handlers:
            try:
                if event == "connect":
                    await handler.on_connect(
                        self.connection_id, self.config.connection_type
                    )
                elif event == "disconnect":
                    await handler.on_disconnect(self.connection_id, args[0])
                elif event == "message":
                    await handler.on_message(self.connection_id, args[0])
                elif event == "error":
                    await handler.on_error(self.connection_id, args[0])
                elif event == "reconnect":
                    await handler.on_reconnect(self.connection_id, args[0])
            except Exception as e:
                # Log error but don't break other handlers
                print(f"Error in event handler {handler.__class__.__name__}: {e}")

    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]

    def is_authenticated(self) -> bool:
        """Check if connection is authenticated"""
        return self.state == ConnectionState.AUTHENTICATED

    def get_metrics(self) -> ConnectionMetrics:
        """Get connection metrics"""
        return self.metrics

    async def health_check(self) -> bool:
        """Perform health check on connection"""
        if not self.is_connected():
            return False

        # Check if last heartbeat is within acceptable range
        if self._last_heartbeat:
            time_since_heartbeat = datetime.now() - self._last_heartbeat
            if time_since_heartbeat > timedelta(
                seconds=self.config.heartbeat_interval_seconds * 2
            ):
                return False

        return True


class ConnectionPoolInterface(ABC):
    """Abstract interface for connection pooling"""

    @abstractmethod
    async def get_connection(
        self, connection_type: ConnectionType
    ) -> Optional[WebSocketConnectionInterface]:
        """Get available connection from pool"""
        pass

    @abstractmethod
    async def return_connection(self, connection: WebSocketConnectionInterface):
        """Return connection to pool"""
        pass

    @abstractmethod
    async def create_connection(
        self, config: ConnectionConfig
    ) -> WebSocketConnectionInterface:
        """Create new connection"""
        pass

    @abstractmethod
    async def close_all_connections(self):
        """Close all connections in pool"""
        pass

    @abstractmethod
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        pass


class LoadBalancerInterface(ABC):
    """Abstract interface for load balancing"""

    @abstractmethod
    async def select_connection(
        self, connection_type: ConnectionType
    ) -> Optional[WebSocketConnectionInterface]:
        """Select best connection based on load balancing strategy"""
        pass

    @abstractmethod
    def update_connection_metrics(self, connection_id: str, metrics: ConnectionMetrics):
        """Update connection metrics for load balancing decisions"""
        pass

    @abstractmethod
    def get_load_distribution(self) -> Dict[str, float]:
        """Get current load distribution across connections"""
        pass


class ClusterManagerInterface(ABC):
    """Abstract interface for cluster management"""

    @abstractmethod
    async def register_node(self, node_id: str, node_info: Dict[str, Any]):
        """Register cluster node"""
        pass

    @abstractmethod
    async def unregister_node(self, node_id: str):
        """Unregister cluster node"""
        pass

    @abstractmethod
    async def get_available_nodes(self) -> List[Dict[str, Any]]:
        """Get list of available cluster nodes"""
        pass

    @abstractmethod
    async def elect_leader(self) -> Optional[str]:
        """Elect cluster leader"""
        pass

    @abstractmethod
    def is_leader(self, node_id: str) -> bool:
        """Check if node is cluster leader"""
        pass
