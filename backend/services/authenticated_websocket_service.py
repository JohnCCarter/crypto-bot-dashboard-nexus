"""
Authenticated WebSocket service for Bitfinex private data.
Provides real-time updates for balances, positions, orders, etc.
"""

import os
import json
import hmac
import hashlib
import asyncio
import websockets
import logging
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AuthenticatedMessage:
    """Authenticated message from Bitfinex WebSocket."""
    channel: str
    data: Any
    timestamp: datetime


class AuthenticatedWebSocketService:
    """Service for authenticated Bitfinex WebSocket connections."""
    
    def __init__(self):
        self.api_key = os.getenv("BITFINEX_API_KEY")
        self.api_secret = os.getenv("BITFINEX_API_SECRET")
        self.uri = "wss://api.bitfinex.com/ws/2"
        self.websocket = None
        self.authenticated = False
        self.user_id = None
        
        # Callbacks for different message types
        self.balance_callback: Optional[Callable] = None
        self.position_callback: Optional[Callable] = None
        self.order_callback: Optional[Callable] = None
        
        self.logger = logging.getLogger(__name__)
        
    def _build_authentication_message(self) -> str:
        """Build authentication message for Bitfinex WebSocket."""
        if not self.api_key or not self.api_secret:
            raise ValueError("BITFINEX_API_KEY and BITFINEX_API_SECRET must be set")
            
        message = {"event": "auth"}
        message["apiKey"] = self.api_key
        message["authNonce"] = round(datetime.now().timestamp() * 1_000)
        message["authPayload"] = f"AUTH{message['authNonce']}"
        message["authSig"] = hmac.new(
            key=self.api_secret.encode("utf8"),
            msg=message["authPayload"].encode("utf8"),
            digestmod=hashlib.sha384
        ).hexdigest()
        
        return json.dumps(message)
    
    def _subscribe_to_private_channels(self):
        """Subscribe to private data channels after authentication."""
        subscriptions = [
            {"event": "subscribe", "channel": "wallet"},  # Balance updates
            {"event": "subscribe", "channel": "positions"},  # Position updates  
            {"event": "subscribe", "channel": "orders"},  # Order updates
        ]
        
        for sub in subscriptions:
            asyncio.create_task(self.websocket.send(json.dumps(sub)))
            self.logger.info(f"🔐 [Auth WS] Subscribed to {sub['channel']}")
    
    def _handle_auth_response(self, data: Dict[str, Any]):
        """Handle authentication response."""
        if data.get("status") != "OK":
            error_msg = f"Authentication failed: {data.get('message', 'Unknown error')}"
            self.logger.error(f"❌ [Auth WS] {error_msg}")
            raise Exception(error_msg)
            
        self.authenticated = True
        self.user_id = data.get("userId")
        self.logger.info(f"✅ [Auth WS] Authenticated as user {self.user_id}")
        
        # Subscribe to private channels
        self._subscribe_to_private_channels()
    
    def _handle_wallet_update(self, data):
        """Handle wallet (balance) updates."""
        if self.balance_callback and data:
            # Transform Bitfinex wallet format to our balance format
            if isinstance(data, list) and len(data) >= 4:
                wallet_type, currency, balance, available = data[:4]
                
                balance_update = {
                    "currency": currency,
                    "total_balance": float(balance),
                    "available": float(available),
                    "wallet_type": wallet_type,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.balance_callback(balance_update)
                self.logger.info(f"💰 [Auth WS] Balance update: {currency} = {balance}")
    
    def _handle_position_update(self, data):
        """Handle position updates."""
        if self.position_callback and data:
            # Transform Bitfinex position format
            if isinstance(data, list) and len(data) >= 8:
                symbol, status, amount, base_price, margin_funding, margin_funding_type, pl, pl_perc = data[:8]
                
                position_update = {
                    "symbol": symbol,
                    "status": status,
                    "amount": float(amount),
                    "base_price": float(base_price),
                    "pnl": float(pl),
                    "pnl_percentage": float(pl_perc),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.position_callback(position_update)
                self.logger.info(f"📊 [Auth WS] Position update: {symbol} PnL: {pl}")
    
    def _handle_order_update(self, data):
        """Handle order updates."""
        if self.order_callback and data:
            # Transform Bitfinex order format
            if isinstance(data, list) and len(data) >= 12:
                order_id, gid, cid, symbol, created, updated, amount, amount_orig, order_type, type_prev, mtsnTIF, flags = data[:12]
                
                order_update = {
                    "id": str(order_id),
                    "symbol": symbol,
                    "amount": float(amount),
                    "amount_orig": float(amount_orig),
                    "type": order_type,
                    "status": "active" if amount != 0 else "filled",
                    "created": created,
                    "updated": updated,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.order_callback(order_update)
                self.logger.info(f"📋 [Auth WS] Order update: {order_id} {symbol}")
    
    async def _message_handler(self, websocket):
        """Handle incoming WebSocket messages."""
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Handle dict messages (events)
                if isinstance(data, dict):
                    if data.get("event") == "auth":
                        self._handle_auth_response(data)
                    elif data.get("event") == "subscribed":
                        channel = data.get("channel")
                        self.logger.info(f"✅ [Auth WS] Subscribed to {channel}")
                    elif data.get("event") == "error":
                        self.logger.error(f"❌ [Auth WS] Error: {data}")
                
                # Handle array messages (channel data)
                elif isinstance(data, list) and len(data) >= 2:
                    message_data = data[1]
                    
                    # Skip heartbeats
                    if message_data == "hb":
                        continue
                    
                    # Handle different channel types based on structure
                    if isinstance(message_data, list):
                        # Wallet updates [wallet_type, currency, balance, ...]
                        if (len(message_data) >= 4 and
                                isinstance(message_data[1], str)):
                            self._handle_wallet_update(message_data)
                        
                        # Position updates [symbol, status, amount, base_price, ...]
                        elif len(message_data) >= 8 and message_data[0] and ":" in str(message_data[0]):
                            self._handle_position_update(message_data)
                        
                        # Order updates [id, gid, cid, symbol, ...]
                        elif len(message_data) >= 12:
                            self._handle_order_update(message_data)
                
            except json.JSONDecodeError:
                self.logger.error(f"❌ [Auth WS] Invalid JSON: {message}")
            except Exception as e:
                self.logger.error(f"❌ [Auth WS] Message handling error: {e}")
    
    async def connect(self):
        """Connect to authenticated WebSocket."""
        if not self.api_key or not self.api_secret:
            self.logger.warning("⚠️ [Auth WS] No API credentials - authenticated WebSocket disabled")
            return False
            
        try:
            self.logger.info("🔐 [Auth WS] Connecting to authenticated WebSocket...")
            
            self.websocket = await websockets.connect(self.uri)
            
            # Send authentication message
            auth_message = self._build_authentication_message()
            await self.websocket.send(auth_message)
            
            # Start message handler
            await self._message_handler(self.websocket)
            
        except Exception as e:
            self.logger.error(f"❌ [Auth WS] Connection failed: {e}")
            return False
    
    def set_balance_callback(self, callback: Callable):
        """Set callback for balance updates."""
        self.balance_callback = callback
    
    def set_position_callback(self, callback: Callable):
        """Set callback for position updates."""
        self.position_callback = callback
    
    def set_order_callback(self, callback: Callable):
        """Set callback for order updates."""
        self.order_callback = callback
    
    async def disconnect(self):
        """Disconnect from WebSocket."""
        if self.websocket:
            await self.websocket.close()
            self.authenticated = False
            self.logger.info("🔐 [Auth WS] Disconnected")


# Global instance
authenticated_ws_service = AuthenticatedWebSocketService()