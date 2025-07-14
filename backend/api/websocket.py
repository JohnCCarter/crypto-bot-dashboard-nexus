"""
WebSocket API för FastAPI
Implementerar WebSocket-endpoints för realtidsdata med FastAPI
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from backend.services.websocket_market_service import (
    get_websocket_client,
    start_websocket_service,
)
from backend.services.websocket_user_data_service import BitfinexUserDataClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


# Enhanced connection manager med performance monitoring och error handling
class ConnectionManager:
    def __init__(self, connection_type: str):
        self.active_connections: List[WebSocket] = []
        self.connection_type = connection_type
        self.client_data: Dict[WebSocket, Dict[str, Any]] = {}
        self.performance_metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "errors": 0,
            "last_error": None,
        }
        self.rate_limits = {
            "messages_per_second": 100,
            "connections_per_minute": 60,
        }
        self._connection_timestamps = []
        self._message_timestamps = []

    def _check_connection_rate_limit(self) -> bool:
        """Check if connection rate limit is exceeded."""
        now = asyncio.get_event_loop().time()
        # Remove timestamps older than 1 minute
        self._connection_timestamps = [
            ts for ts in self._connection_timestamps if now - ts < 60
        ]
        return (
            len(self._connection_timestamps)
            < self.rate_limits["connections_per_minute"]
        )

    def _check_message_rate_limit(self) -> bool:
        """Check if message rate limit is exceeded."""
        now = asyncio.get_event_loop().time()
        # Remove timestamps older than 1 second
        self._message_timestamps = [
            ts for ts in self._message_timestamps if now - ts < 1
        ]
        return len(self._message_timestamps) < self.rate_limits["messages_per_second"]

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Enhanced connect with rate limiting and monitoring."""
        try:
            # Rate limiting check
            if not self._check_connection_rate_limit():
                logger.warning(
                    f"Connection rate limit exceeded for {self.connection_type}"
                )
                await websocket.close(code=1008, reason="Rate limit exceeded")
                return False

            await websocket.accept()
            self.active_connections.append(websocket)
            self.client_data[websocket] = {
                "id": client_id,
                "subscriptions": [],
                "connected_at": asyncio.get_event_loop().time(),
                "message_count": 0,
                "last_message": None,
            }

            # Update metrics
            self.performance_metrics["total_connections"] += 1
            self.performance_metrics["active_connections"] = len(
                self.active_connections
            )
            self._connection_timestamps.append(asyncio.get_event_loop().time())

            logger.info(
                f"WebSocket client connected: {client_id or 'anonymous'} ({self.connection_type}) - Total: {self.performance_metrics['active_connections']}"
            )
            return True

        except Exception as e:
            self.performance_metrics["errors"] += 1
            self.performance_metrics["last_error"] = str(e)
            logger.error(f"Error connecting WebSocket client: {e}")
            return False

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_data:
            logger.info(
                f"WebSocket client disconnected: {self.client_data[websocket].get('id', 'anonymous')} ({self.connection_type})"
            )
            del self.client_data[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")

    async def broadcast(self, message: str):
        """Enhanced broadcast with rate limiting and error tracking."""
        if not self._check_message_rate_limit():
            logger.warning(f"Message rate limit exceeded for {self.connection_type}")
            return

        failed_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
                self.performance_metrics["messages_sent"] += 1
                self._message_timestamps.append(asyncio.get_event_loop().time())

                # Update client metrics
                if connection in self.client_data:
                    self.client_data[connection]["message_count"] += 1
                    self.client_data[connection][
                        "last_message"
                    ] = asyncio.get_event_loop().time()

            except Exception as e:
                self.performance_metrics["messages_failed"] += 1
                self.performance_metrics["errors"] += 1
                self.performance_metrics["last_error"] = str(e)
                failed_connections.append(connection)
                logger.error(f"Failed to send message to client: {e}")

        # Remove failed connections
        for connection in failed_connections:
            self.disconnect(connection)

    def add_subscription(self, websocket: WebSocket, subscription: str):
        """Lägg till en prenumeration för en klient."""
        if websocket in self.client_data:
            if subscription not in self.client_data[websocket]["subscriptions"]:
                self.client_data[websocket]["subscriptions"].append(subscription)

    def remove_subscription(self, websocket: WebSocket, subscription: str):
        """Ta bort en prenumeration för en klient."""
        if websocket in self.client_data:
            if subscription in self.client_data[websocket]["subscriptions"]:
                self.client_data[websocket]["subscriptions"].remove(subscription)

    def get_subscriptions(self, websocket: WebSocket) -> List[str]:
        """Hämta alla prenumerationer för en klient."""
        if websocket in self.client_data:
            return self.client_data[websocket]["subscriptions"]
        return []

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Hämta performance metrics för denna connection manager."""
        return {
            **self.performance_metrics,
            "success_rate": (
                (
                    self.performance_metrics["messages_sent"]
                    / (
                        self.performance_metrics["messages_sent"]
                        + self.performance_metrics["messages_failed"]
                    )
                )
                if (
                    self.performance_metrics["messages_sent"]
                    + self.performance_metrics["messages_failed"]
                )
                > 0
                else 0.0
            ),
            "uptime": (
                asyncio.get_event_loop().time() - min(self._connection_timestamps)
                if self._connection_timestamps
                else 0.0
            ),
        }


# Skapa connection managers för olika typer av anslutningar
market_manager = ConnectionManager("market")
ticker_manager = ConnectionManager("ticker")
orderbook_manager = ConnectionManager("orderbook")
trades_manager = ConnectionManager("trades")
user_data_manager = ConnectionManager("user")


@router.websocket("/market/{client_id}")
async def websocket_market_endpoint(
    websocket: WebSocket, client_id: str, symbol: Optional[str] = Query(None)
):
    """
    WebSocket endpoint för marknadsdata (ticker, orderbook, trades)

    Args:
        websocket: WebSocket-anslutning
        client_id: Unik identifierare för klienten
        symbol: Trading pair (t.ex. 'BTCUSD') att prenumerera på
    """
    await market_manager.connect(websocket, client_id)

    # Initiera WebSocket-tjänsten om den inte redan är igång
    ws_client = get_websocket_client()
    if not ws_client or not ws_client.websocket:
        await start_websocket_service()
        ws_client = get_websocket_client()

    try:
        # Om symbol är angiven, prenumerera direkt
        if symbol:
            await handle_market_subscription(websocket, symbol, "ticker")

        # Lyssna efter meddelanden från klienten
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await process_market_message(websocket, message)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
    except WebSocketDisconnect:
        market_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket market endpoint: {e}")
        market_manager.disconnect(websocket)


async def process_market_message(websocket: WebSocket, message: Dict[str, Any]):
    """
    Bearbeta meddelanden från klienter.

    Förväntat format:
    {
        "action": "subscribe"|"unsubscribe",
        "channel": "ticker"|"orderbook"|"trades",
        "symbol": "BTCUSD"
    }
    """
    try:
        action = message.get("action")
        channel = message.get("channel")
        symbol = message.get("symbol")

        if not all([action, channel, symbol]):
            await websocket.send_json(
                {"error": "Missing required fields: action, channel, symbol"}
            )
            return

        if action == "subscribe":
            if symbol and channel:
                await handle_market_subscription(websocket, symbol, channel)
            else:
                await websocket.send_json(
                    {"error": "Missing symbol or channel for subscription"}
                )
        elif action == "unsubscribe":
            if symbol and channel:
                await handle_market_unsubscription(websocket, symbol, channel)
            else:
                await websocket.send_json(
                    {"error": "Missing symbol or channel for unsubscription"}
                )
        else:
            await websocket.send_json({"error": f"Unknown action: {action}"})
    except Exception as e:
        logger.error(f"Error processing market message: {e}")
        await websocket.send_json({"error": str(e)})


async def handle_market_subscription(websocket: WebSocket, symbol: str, channel: str):
    """Hantera prenumeration på marknadsdata."""
    ws_client = get_websocket_client()
    if not ws_client:
        await websocket.send_json({"error": "WebSocket service not available"})
        return

    subscription_id = f"{channel}_{symbol}"

    try:
        if channel == "ticker":
            ticker_manager.add_subscription(websocket, subscription_id)

            async def on_ticker(data):
                if websocket in ticker_manager.active_connections:
                    await websocket.send_json(
                        {
                            "type": "ticker",
                            "symbol": symbol,
                            "data": {
                                "price": data.price,
                                "volume": data.volume,
                                "bid": data.bid,
                                "ask": data.ask,
                                "timestamp": data.timestamp.isoformat(),
                            },
                        }
                    )

            await ws_client.subscribe_ticker(symbol, on_ticker)
            await websocket.send_json(
                {"status": "subscribed", "channel": channel, "symbol": symbol}
            )

        elif channel == "orderbook":
            orderbook_manager.add_subscription(websocket, subscription_id)

            async def on_orderbook(data):
                if websocket in orderbook_manager.active_connections:
                    await websocket.send_json(
                        {"type": "orderbook", "symbol": symbol, "data": data}
                    )

            await ws_client.subscribe_orderbook(symbol, on_orderbook)
            await websocket.send_json(
                {"status": "subscribed", "channel": channel, "symbol": symbol}
            )

        elif channel == "trades":
            trades_manager.add_subscription(websocket, subscription_id)

            async def on_trades(data):
                if websocket in trades_manager.active_connections:
                    await websocket.send_json(
                        {"type": "trades", "symbol": symbol, "data": data}
                    )

            await ws_client.subscribe_trades(symbol, on_trades)
            await websocket.send_json(
                {"status": "subscribed", "channel": channel, "symbol": symbol}
            )

        else:
            await websocket.send_json({"error": f"Unknown channel: {channel}"})

    except Exception as e:
        logger.error(f"Error subscribing to {channel} for {symbol}: {e}")
        await websocket.send_json({"error": f"Subscription failed: {str(e)}"})


async def handle_market_unsubscription(websocket: WebSocket, symbol: str, channel: str):
    """Hantera avprenumeration på marknadsdata."""
    subscription_id = f"{channel}_{symbol}"

    if channel == "ticker":
        ticker_manager.remove_subscription(websocket, subscription_id)
    elif channel == "orderbook":
        orderbook_manager.remove_subscription(websocket, subscription_id)
    elif channel == "trades":
        trades_manager.remove_subscription(websocket, subscription_id)

    await websocket.send_json(
        {"status": "unsubscribed", "channel": channel, "symbol": symbol}
    )


@router.websocket("/user/{client_id}")
async def websocket_user_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint för användardata (balances, orders, positions)
    Kräver autentisering via API-nycklar

    Args:
        websocket: WebSocket-anslutning
        client_id: Unik identifierare för klienten
    """
    await user_data_manager.connect(websocket, client_id)

    try:
        # Lyssna efter autentisering först
        auth_data = await websocket.receive_text()
        try:
            auth_message = json.loads(auth_data)
            api_key = auth_message.get("api_key")
            api_secret = auth_message.get("api_secret")

            if not api_key or not api_secret:
                await websocket.send_json(
                    {"status": "error", "message": "Missing API credentials"}
                )
                return

            # Initiera user data client med API-nycklar
            user_client = BitfinexUserDataClient(api_key, api_secret)
            await user_client.connect()

            # Om anslutningen lyckades, skicka bekräftelse
            await websocket.send_json(
                {"status": "authenticated", "message": "Successfully authenticated"}
            )

            # Registrera callbacks för att skicka data till klienten
            async def on_balance_update(balance):
                await websocket.send_json({"type": "balance", "data": balance})

            async def on_order_update(order):
                await websocket.send_json({"type": "order", "data": order})

            async def on_position_update(position):
                await websocket.send_json({"type": "position", "data": position})

            # Registrera callbacks med rätt struktur
            user_client.balance_callbacks = [on_balance_update]
            user_client.order_callbacks = [on_order_update]
            user_client.position_callbacks = [on_position_update]

            # Lyssna efter meddelanden från klienten
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    # Hantera olika meddelanden från klienten
                    # (för framtida funktionalitet)
                except json.JSONDecodeError:
                    await websocket.send_json({"error": "Invalid JSON"})

        except json.JSONDecodeError:
            await websocket.send_json({"error": "Invalid authentication data"})

    except WebSocketDisconnect:
        user_data_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket user endpoint: {e}")
        user_data_manager.disconnect(websocket)


@router.get("/metrics")
async def get_websocket_metrics():
    """
    Hämta performance metrics för alla WebSocket-anslutningar.

    Returns:
    --------
    Dict[str, Any]: Performance metrics för alla connection managers
    """
    try:
        metrics = {
            "market": market_manager.get_performance_metrics(),
            "ticker": ticker_manager.get_performance_metrics(),
            "orderbook": orderbook_manager.get_performance_metrics(),
            "trades": trades_manager.get_performance_metrics(),
            "user": user_data_manager.get_performance_metrics(),
        }

        # Beräkna totala metrics
        total_connections = sum(m["active_connections"] for m in metrics.values())
        total_messages = sum(m["messages_sent"] for m in metrics.values())
        total_errors = sum(m["errors"] for m in metrics.values())

        overall_metrics = {
            "total_active_connections": total_connections,
            "total_messages_sent": total_messages,
            "total_errors": total_errors,
            "overall_success_rate": (
                (total_messages / (total_messages + total_errors))
                if (total_messages + total_errors) > 0
                else 0.0
            ),
            "managers": metrics,
        }

        return overall_metrics

    except Exception as e:
        logger.error(f"Error getting WebSocket metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get WebSocket metrics: {str(e)}",
        )
