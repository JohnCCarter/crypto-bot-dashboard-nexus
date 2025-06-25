"""
Authenticated WebSocket service för Bitfinex enligt officiell dokumentation.
Baserat på: https://bitfinex.readthedocs.io/en/latest/websocket.html
"""

import os
import json
import asyncio
import websockets
import logging
import hmac
import hashlib
import time
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class AuthenticatedData:
    """Container för autentiserad account data."""
    timestamp: datetime
    channel: str
    data: Any

class BitfinexAuthenticatedWebSocket:
    """
    Authenticated WebSocket klient för Bitfinex med riktiga API-nycklar.
    Implementerad enligt official Bitfinex WebSocket v2 dokumentation.
    """
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.uri = "wss://api.bitfinex.com/ws/2"
        self.websocket = None
        self.authenticated = False
        self.running = False
        
        # Account data storage
        self.wallets = {}
        self.positions = []
        self.orders = []
        self.order_history = []
        self.trade_history = []
        
        # Callbacks for real-time updates
        self.wallet_callback = None
        self.position_callback = None
        self.order_callback = None
        self.trade_callback = None

    async def connect(self):
        """Anslut till Bitfinex authenticated WebSocket."""
        try:
            logger.info("🔐 Connecting to Bitfinex authenticated WebSocket...")
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            
            # Starta message handler
            asyncio.create_task(self._handle_messages())
            
            # Autentisera omedelbart
            await self.authenticate()
            
            logger.info("✅ Connected to Bitfinex authenticated WebSocket")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            raise

    async def authenticate(self):
        """
        Autentiserar WebSocket enligt Bitfinex dokumentation.
        Exakt som din Go-kod men i Python.
        """
        try:
            # Skapa nonce (timestamp i sekunder)
            nonce = str(int(time.time()))
            
            # Skapa payload för signering
            auth_payload = f"AUTH{nonce}"
            
            # Skapa HMAC SHA384 signatur (samma som Go-koden)
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                auth_payload.encode('utf-8'),
                hashlib.sha384
            ).hexdigest()
            
            # Skapa auth message (exakt som Go-koden)
            auth_message = {
                "event": "auth",
                "apiKey": self.api_key,
                "authSig": signature,
                "authPayload": auth_payload,
                "authNonce": nonce
            }
            
            await self._send_message(auth_message)
            logger.info("🔐 Sent authentication request...")
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise

    async def _send_message(self, message):
        """Skicka meddelande till WebSocket."""
        if self.websocket:
            message_str = json.dumps(message)
            await self.websocket.send(message_str)
            logger.debug(f"📤 Sent: {message_str}")

    async def _handle_messages(self):
        """Hantera alla inkommande meddelanden."""
        try:
            async for message in self.websocket:
                await self._process_message(json.loads(message))
        except Exception as e:
            logger.error(f"❌ Message handling error: {e}")
            self.running = False

    async def _process_message(self, data):
        """
        Processera inkommande meddelanden enligt Bitfinex format.
        Implementerat enligt officiell dokumentation.
        """
        try:
            logger.debug(f"📥 Received: {data}")
            
            # Hantera event meddelanden
            if isinstance(data, dict):
                if data.get("event") == "auth":
                    if data.get("status") == "OK":
                        self.authenticated = True
                        logger.info("✅ Authentication successful!")
                        
                        # Efter autentisering, begär account data
                        await self._request_account_data()
                    else:
                        logger.error(f"❌ Authentication failed: {data}")
                        
                elif data.get("event") == "error":
                    logger.error(f"❌ WebSocket error: {data}")
                    
                return
            
            # Hantera array meddelanden [CHANNEL_ID, MESSAGE_TYPE, DATA]
            if isinstance(data, list) and len(data) >= 3:
                channel_id = data[0]
                
                # Channel 0 = Authenticated channel
                if channel_id == 0:
                    await self._handle_authenticated_data(data[1], data[2])
                    
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")

    async def _handle_authenticated_data(self, message_type: str, data):
        """
        Hantera authenticated data enligt Bitfinex dokumentation.
        Implementerar alla account-specifika meddelanden.
        """
        try:
            if message_type == "ws":  # Wallet snapshot
                logger.info(f"💰 Wallet snapshot received: {len(data) if isinstance(data, list) else 'single'} wallets")
                self.wallets = {}
                
                if isinstance(data, list):
                    for wallet in data:
                        if len(wallet) >= 4:
                            wallet_type, currency, balance, available = wallet[:4]
                            self.wallets[f"{wallet_type}_{currency}"] = {
                                "type": wallet_type,
                                "currency": currency,
                                "balance": float(balance) if balance else 0.0,
                                "available": float(available) if available else 0.0
                            }
                
                if self.wallet_callback:
                    await self._safe_callback(self.wallet_callback, self.wallets)
                    
            elif message_type == "wu":  # Wallet update
                logger.info(f"� Wallet update: {data}")
                if len(data) >= 4:
                    wallet_type, currency, balance, available = data[:4]
                    key = f"{wallet_type}_{currency}"
                    self.wallets[key] = {
                        "type": wallet_type,
                        "currency": currency, 
                        "balance": float(balance) if balance else 0.0,
                        "available": float(available) if available else 0.0
                    }
                    
                if self.wallet_callback:
                    await self._safe_callback(self.wallet_callback, self.wallets)
                    
            elif message_type == "ps":  # Position snapshot
                logger.info(f"📊 Position snapshot: {len(data) if isinstance(data, list) else 'single'} positions")
                self.positions = []
                
                if isinstance(data, list):
                    for position in data:
                        if len(position) >= 11:
                            self.positions.append({
                                "symbol": position[0],
                                "status": position[1],
                                "amount": float(position[2]) if position[2] else 0.0,
                                "base_price": float(position[3]) if position[3] else 0.0,
                                "margin_funding": float(position[4]) if position[4] else 0.0,
                                "margin_funding_type": position[5],
                                "pl": float(position[6]) if position[6] else 0.0,
                                "pl_perc": float(position[7]) if position[7] else 0.0,
                                "price_liq": float(position[8]) if position[8] else 0.0,
                                "leverage": float(position[9]) if position[9] else 0.0,
                                "placeholder": position[10]
                            })
                
                if self.position_callback:
                    await self._safe_callback(self.position_callback, self.positions)
                    
            elif message_type == "pn" or message_type == "pu":  # Position new/update
                logger.info(f"📊 Position {message_type}: {data}")
                # Update individual position
                if self.position_callback:
                    await self._safe_callback(self.position_callback, self.positions)
                    
            elif message_type == "os":  # Order snapshot
                logger.info(f"📋 Order snapshot: {len(data) if isinstance(data, list) else 'single'} orders")
                self.orders = []
                
                if isinstance(data, list):
                    for order in data:
                        if len(order) >= 19:
                            self.orders.append({
                                "id": order[0],
                                "gid": order[1], 
                                "cid": order[2],
                                "symbol": order[3],
                                "mts_create": order[4],
                                "mts_update": order[5],
                                "amount": float(order[6]) if order[6] else 0.0,
                                "amount_orig": float(order[7]) if order[7] else 0.0,
                                "type": order[8],
                                "type_prev": order[9],
                                "flags": order[12],
                                "status": order[13],
                                "price": float(order[16]) if order[16] else 0.0,
                                "price_avg": float(order[17]) if order[17] else 0.0,
                                "price_trailing": float(order[18]) if order[18] else 0.0
                            })
                
                if self.order_callback:
                    await self._safe_callback(self.order_callback, self.orders)
                    
            elif message_type in ["on", "ou", "oc"]:  # Order new/update/cancel
                logger.info(f"📋 Order {message_type}: {data}")
                # Handle individual order updates
                if self.order_callback:
                    await self._safe_callback(self.order_callback, self.orders)
                    
            elif message_type == "te":  # Trade executed
                logger.info(f"💱 Trade executed: {data}")
                if len(data) >= 11:
                    trade = {
                        "id": data[0],
                        "symbol": data[1],
                        "mts_create": data[2],
                        "order_id": data[3],
                        "exec_amount": float(data[4]) if data[4] else 0.0,
                        "exec_price": float(data[5]) if data[5] else 0.0,
                        "order_type": data[6],
                        "order_price": float(data[7]) if data[7] else 0.0,
                        "maker": data[8],
                        "fee": float(data[9]) if data[9] else 0.0,
                        "fee_currency": data[10]
                    }
                    self.trade_history.append(trade)
                    
                if self.trade_callback:
                    await self._safe_callback(self.trade_callback, self.trade_history)
                    
            else:
                logger.debug(f"📥 Unhandled message type: {message_type}")
                
        except Exception as e:
            logger.error(f"❌ Error handling authenticated data: {e}")

    async def _request_account_data(self):
        """Begär initial account data efter autentisering."""
        try:
            logger.info("📊 Requesting initial account data...")
            
            # Account data begärs automatiskt vid autentisering för authenticated channels
            # Enligt dokumentationen kommer ws (wallet), ps (position), os (order) automatiskt
            
        except Exception as e:
            logger.error(f"❌ Failed to request account data: {e}")

    async def _safe_callback(self, callback, data):
        """Säker callback execution."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")

    def set_wallet_callback(self, callback: Callable):
        """Sätt callback för wallet updates."""
        self.wallet_callback = callback

    def set_position_callback(self, callback: Callable):
        """Sätt callback för position updates.""" 
        self.position_callback = callback

    def set_order_callback(self, callback: Callable):
        """Sätt callback för order updates."""
        self.order_callback = callback

    def set_trade_callback(self, callback: Callable):
        """Sätt callback för trade updates."""
        self.trade_callback = callback

    async def disconnect(self):
        """Koppla från WebSocket."""
        self.running = False
        self.authenticated = False
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Disconnected from authenticated WebSocket")

    # Public methods för att hämta data
    def get_wallets(self) -> Dict:
        """Hämta aktuella wallet balances."""
        return self.wallets

    def get_positions(self) -> List:
        """Hämta aktuella positions."""
        return self.positions

    def get_orders(self) -> List:
        """Hämta aktuella orders."""
        return self.orders

    def get_trade_history(self) -> List:
        """Hämta trade history."""
        return self.trade_history


# Service management för integration med Flask app
authenticated_ws_client = None

async def start_authenticated_websocket_service():
    """Starta authenticated WebSocket service."""
    global authenticated_ws_client
    
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("Bitfinex API keys not configured")
        
    if "placeholder" in api_key or "your_" in api_key:
        raise ValueError("Please configure real Bitfinex API keys")
        
    if not authenticated_ws_client:
        authenticated_ws_client = BitfinexAuthenticatedWebSocket(api_key, api_secret)
        await authenticated_ws_client.connect()
        
    return authenticated_ws_client

async def stop_authenticated_websocket_service():
    """Stoppa authenticated WebSocket service."""
    global authenticated_ws_client
    if authenticated_ws_client:
        await authenticated_ws_client.disconnect()
        authenticated_ws_client = None

def get_authenticated_websocket_client():
    """Hämta authenticated WebSocket klient."""
    return authenticated_ws_client