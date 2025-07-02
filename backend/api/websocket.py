"""
WebSocket API för FastAPI
Implementerar WebSocket-endpoints för realtidsdata med FastAPI
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from backend.services.websocket_market_service import (
    start_websocket_service, get_websocket_client
)
from backend.services.websocket_user_data_service import BitfinexUserDataClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])

# Connection manager för att hålla reda på alla klienter
class ConnectionManager:
    def __init__(self, connection_type: str):
        self.active_connections: List[WebSocket] = []
        self.connection_type = connection_type
        self.client_data: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_data[websocket] = {"id": client_id, "subscriptions": []}
        logger.info(f"WebSocket client connected: {client_id or 'anonymous'} ({self.connection_type})")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_data:
            logger.info(f"WebSocket client disconnected: {self.client_data[websocket].get('id', 'anonymous')} ({self.connection_type})")
            del self.client_data[websocket]
            
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Om vi inte kan skicka till en klient, fortsätt med nästa
                pass

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

# Skapa connection managers för olika typer av anslutningar
market_manager = ConnectionManager("market")
ticker_manager = ConnectionManager("ticker")
orderbook_manager = ConnectionManager("orderbook")
trades_manager = ConnectionManager("trades")
user_data_manager = ConnectionManager("user")

@router.websocket("/market/{client_id}")
async def websocket_market_endpoint(
    websocket: WebSocket, 
    client_id: str,
    symbol: Optional[str] = Query(None)
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
            await websocket.send_json({"error": "Missing required fields: action, channel, symbol"})
            return
            
        if action == "subscribe":
            await handle_market_subscription(websocket, symbol, channel)
        elif action == "unsubscribe":
            await handle_market_unsubscription(websocket, symbol, channel)
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
                    await websocket.send_json({
                        "type": "ticker",
                        "symbol": symbol,
                        "data": {
                            "price": data.price,
                            "volume": data.volume,
                            "bid": data.bid,
                            "ask": data.ask,
                            "timestamp": data.timestamp.isoformat()
                        }
                    })
            
            await ws_client.subscribe_ticker(symbol, on_ticker)
            await websocket.send_json({
                "status": "subscribed", 
                "channel": channel,
                "symbol": symbol
            })
            
        elif channel == "orderbook":
            orderbook_manager.add_subscription(websocket, subscription_id)
            
            async def on_orderbook(data):
                if websocket in orderbook_manager.active_connections:
                    await websocket.send_json({
                        "type": "orderbook",
                        "symbol": symbol,
                        "data": data
                    })
            
            await ws_client.subscribe_orderbook(symbol, on_orderbook)
            await websocket.send_json({
                "status": "subscribed", 
                "channel": channel,
                "symbol": symbol
            })
            
        elif channel == "trades":
            trades_manager.add_subscription(websocket, subscription_id)
            
            async def on_trades(data):
                if websocket in trades_manager.active_connections:
                    await websocket.send_json({
                        "type": "trades",
                        "symbol": symbol,
                        "data": data
                    })
            
            await ws_client.subscribe_trades(symbol, on_trades)
            await websocket.send_json({
                "status": "subscribed", 
                "channel": channel,
                "symbol": symbol
            })
        
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
    
    await websocket.send_json({
        "status": "unsubscribed", 
        "channel": channel,
        "symbol": symbol
    })

@router.websocket("/user/{client_id}")
async def websocket_user_endpoint(
    websocket: WebSocket, 
    client_id: str
):
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
                await websocket.send_json({
                    "status": "error", 
                    "message": "Missing API credentials"
                })
                return
                
            # Initiera user data client med API-nycklar
            user_client = BitfinexUserDataClient(api_key, api_secret)
            await user_client.connect()
            
            # Om anslutningen lyckades, skicka bekräftelse
            await websocket.send_json({
                "status": "authenticated", 
                "message": "Successfully authenticated"
            })
            
            # Registrera callbacks för att skicka data till klienten
            async def on_balance_update(balance):
                await websocket.send_json({
                    "type": "balance",
                    "data": balance
                })
                
            async def on_order_update(order):
                await websocket.send_json({
                    "type": "order",
                    "data": order
                })
                
            async def on_position_update(position):
                await websocket.send_json({
                    "type": "position",
                    "data": position
                })
                
            # Registrera callbacks
            user_client.on_balance_update(on_balance_update)
            user_client.on_order_update(on_order_update)
            user_client.on_position_update(on_position_update)
            
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