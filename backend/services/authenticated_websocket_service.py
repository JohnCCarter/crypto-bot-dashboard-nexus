"""
Authenticated WebSocket service för Bitfinex med KORREKT authentication.
Baserat på fungerande Go-kod och officiell Bitfinex dokumentation.
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
class AuthenticatedMarketData:
    """Container för autentiserad marknadsdata."""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    wallet_balance: Optional[Dict[str, float]] = None
    positions: Optional[List[Dict]] = None

class BitfinexAuthenticatedWebSocket:
    """
    KORREKT Bitfinex Authenticated WebSocket klient.
    Följer exakt samma protokoll som fungerande Go-implementationen.
    """
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.uri = "wss://api.bitfinex.com/ws/2"  # Korrekt authenticated endpoint
        self.websocket = None
        self.subscriptions = {}
        self.callbacks = {}
        self.running = False
        self.authenticated = False
        
        # För att hålla koll på kontoinformation
        self.wallets = {}
        self.positions = []
        self.orders = []
        
    async def connect(self):
        """Anslut till Bitfinex authenticated WebSocket med KORREKT protokoll."""
        try:
            logger.info("🔐 Ansluter till Bitfinex authenticated WebSocket...")
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            
            # Starta message handler
            asyncio.create_task(self._handle_messages())
            
            # Autentisera enligt KORREKT Bitfinex-protokoll
            await self.authenticate()
            
            logger.info("✅ Authenticated WebSocket ansluten till Bitfinex")
            
        except Exception as e:
            logger.error(f"❌ Authenticated WebSocket anslutning misslyckades: {e}")
            raise

    async def authenticate(self):
        """
        KORREKT Bitfinex authentication - exakt som Go-koden.
        """
        try:
            # Skapa nonce (Unix timestamp)
            nonce = str(int(time.time()))
            
            # Skapa payload (exakt som Go-koden)
            auth_payload = f"AUTH{nonce}"
            
            # Skapa signatur med SHA384 (exakt som Go-koden)
            signature = hmac.new(
                self.api_secret.encode(),
                auth_payload.encode(),
                hashlib.sha384
            ).hexdigest()
            
            # Bygg auth-meddelandet (exakt samma struktur som Go-koden)
            auth_message = {
                "event": "auth",
                "apiKey": self.api_key,
                "authSig": signature,
                "authPayload": auth_payload,
                "authNonce": nonce
            }
            
            logger.info("🔐 Skickar authentication med korrekt Bitfinex protokoll...")
            await self._send_message(auth_message)
            
        except Exception as e:
            logger.error(f"❌ Authentication fel: {e}")
            raise

    async def _send_message(self, message):
        """Skicka meddelande till WebSocket."""
        if self.websocket:
            message_str = json.dumps(message)
            await self.websocket.send(message_str)
            logger.debug(f"📤 Skickat: {message_str}")

    async def _handle_messages(self):
        """Hantera inkommande meddelanden från Bitfinex."""
        try:
            async for message in self.websocket:
                await self._process_message(json.loads(message))
        except Exception as e:
            logger.error(f"❌ Message handling fel: {e}")
            self.running = False

    async def _process_message(self, data):
        """Processera inkommande meddelanden enligt Bitfinex protokoll."""
        try:
            logger.debug(f"📥 Mottaget: {data}")
            
            if isinstance(data, dict):
                # Event meddelanden
                if data.get("event") == "auth":
                    if data.get("status") == "OK":
                        self.authenticated = True
                        logger.info("✅ BITFINEX AUTHENTICATION LYCKADES!")
                        
                        # Efter authentication, begär kontoinformation
                        await self.request_account_data()
                    else:
                        logger.error(f"❌ Authentication misslyckades: {data}")
                        
                elif data.get("event") == "info":
                    logger.info(f"ℹ️  Bitfinex info: {data}")
                    
                elif data.get("event") == "error":
                    logger.error(f"❌ Bitfinex error: {data}")
                    
            elif isinstance(data, list):
                # Channel data från authenticated streams
                if len(data) >= 2:
                    channel_id = data[0]
                    
                    if channel_id == 0:  # Authenticated channel
                        await self._handle_authenticated_data(data)
                        
        except Exception as e:
            logger.error(f"❌ Fel vid processering av meddelande: {e}")

    async def _handle_authenticated_data(self, data):
        """Hantera authenticated data (wallets, positions, orders)."""
        try:
            if len(data) >= 3:
                msg_type = data[1]
                msg_data = data[2]
                
                if msg_type == "ws":  # Wallet snapshot
                    logger.info("💰 WALLET SNAPSHOT:")
                    self.wallets = {}
                    if isinstance(msg_data, list):
                        for wallet in msg_data:
                            if len(wallet) >= 4:
                                wallet_type = wallet[0]  # exchange, margin, funding
                                currency = wallet[1]
                                balance = float(wallet[2])
                                available = float(wallet[4]) if len(wallet) > 4 else balance
                                
                                key = f"{wallet_type}_{currency}"
                                self.wallets[key] = {
                                    "type": wallet_type,
                                    "currency": currency,
                                    "balance": balance,
                                    "available": available
                                }
                                logger.info(f"   {wallet_type} {currency}: {balance} (Available: {available})")
                
                elif msg_type == "wu":  # Wallet update
                    logger.info(f"💰 WALLET UPDATE: {msg_data}")
                    if isinstance(msg_data, list) and len(msg_data) >= 4:
                        wallet_type = msg_data[0]
                        currency = msg_data[1] 
                        balance = float(msg_data[2])
                        available = float(msg_data[4]) if len(msg_data) > 4 else balance
                        
                        key = f"{wallet_type}_{currency}"
                        self.wallets[key] = {
                            "type": wallet_type,
                            "currency": currency,
                            "balance": balance,
                            "available": available
                        }
                
                elif msg_type == "ps":  # Position snapshot
                    logger.info("📊 POSITION SNAPSHOT:")
                    self.positions = []
                    if isinstance(msg_data, list):
                        for position in msg_data:
                            if len(position) >= 6:
                                pos_data = {
                                    "symbol": position[0],
                                    "status": position[1],
                                    "amount": float(position[2]),
                                    "base_price": float(position[3]),
                                    "margin_funding": float(position[4]),
                                    "margin_funding_type": position[5],
                                    "pl": float(position[6]) if len(position) > 6 else 0.0,
                                    "pl_perc": float(position[7]) if len(position) > 7 else 0.0,
                                    "price_liq": float(position[8]) if len(position) > 8 else 0.0,
                                    "leverage": float(position[9]) if len(position) > 9 else 0.0
                                }
                                self.positions.append(pos_data)
                                logger.info(f"   {pos_data['symbol']}: {pos_data['amount']} @ {pos_data['base_price']}")
                
                elif msg_type == "pu":  # Position update
                    logger.info(f"📊 POSITION UPDATE: {msg_data}")
                
                elif msg_type == "os":  # Order snapshot
                    logger.info("📋 ORDER SNAPSHOT:")
                    self.orders = []
                    if isinstance(msg_data, list):
                        for order in msg_data:
                            if len(order) >= 10:
                                order_data = {
                                    "id": order[0],
                                    "gid": order[1],
                                    "cid": order[2],
                                    "symbol": order[3],
                                    "created": order[4],
                                    "updated": order[5],
                                    "amount": float(order[6]),
                                    "amount_orig": float(order[7]),
                                    "type": order[8],
                                    "type_prev": order[9],
                                    "flags": order[12] if len(order) > 12 else 0,
                                    "status": order[13] if len(order) > 13 else "",
                                    "price": float(order[16]) if len(order) > 16 else 0.0,
                                    "price_avg": float(order[17]) if len(order) > 17 else 0.0,
                                    "price_trailing": float(order[18]) if len(order) > 18 else 0.0,
                                    "price_aux_limit": float(order[19]) if len(order) > 19 else 0.0
                                }
                                self.orders.append(order_data)
                                logger.info(f"   Order {order_data['id']}: {order_data['type']} {order_data['amount']} {order_data['symbol']} @ {order_data['price']}")
                
                elif msg_type == "ou":  # Order update
                    logger.info(f"� ORDER UPDATE: {msg_data}")
                
                elif msg_type == "on":  # Order new
                    logger.info(f"✅ NEW ORDER: {msg_data}")
                
                elif msg_type == "oc":  # Order cancelled
                    logger.info(f"❌ ORDER CANCELLED: {msg_data}")
                
                elif msg_type == "te":  # Trade executed
                    logger.info(f"💱 TRADE EXECUTED: {msg_data}")
                
                elif msg_type == "tu":  # Trade update
                    logger.info(f"💱 TRADE UPDATE: {msg_data}")
                
                else:
                    logger.info(f"� Okänt authenticated meddelande: {msg_type} - {msg_data}")
                    
        except Exception as e:
            logger.error(f"❌ Authenticated data fel: {e}")

    async def request_account_data(self):
        """Begär all kontoinformation efter authentication."""
        try:
            logger.info("📊 Begär kontoinformation från Bitfinex...")
            
            # Dessa meddelanden begär kontoinformation automatiskt
            # enligt Bitfinex dokumentation
            
        except Exception as e:
            logger.error(f"❌ Fel vid begäran av kontoinformation: {e}")

    async def new_order(self, order_type: str, symbol: str, amount: float, price: float = None):
        """
        Placera ny order via WebSocket (exakt som Bitfinex dokumentation).
        """
        if not self.authenticated:
            raise Exception("Måste vara authenticated för att placera orders")
            
        # Generate client ID (timestamp)
        cid = int(time.time() * 1000)
        
        # Format symbol (lägg till 't' prefix om det saknas)
        if not symbol.startswith('t'):
            symbol = f"t{symbol}"
            
        order_data = [
            0,  # ID (0 för nya orders)
            None,  # Group ID
            cid,  # Client ID
            symbol,
            int(time.time() * 1000),  # Timestamp
            int(time.time() * 1000),  # Timestamp
            float(amount),
            float(price) if price else None,
            order_type.upper(),
            None,  # Type prev
            None,  # Meta
            None,  # Flags
            None,  # Status
            None,  # Price aux limit
            None,  # Price trailing
            None,  # Time in force
        ]
        
        order_message = [0, "on", None, order_data]
        
        await self._send_message(order_message)
        logger.info(f"📋 Placerar order: {order_type} {amount} {symbol} @ {price}")
        
        return cid

    async def cancel_order(self, order_id: int):
        """Avbryt order via WebSocket."""
        if not self.authenticated:
            raise Exception("Måste vara authenticated för att avbryta orders")
            
        cancel_message = [0, "oc", None, {"id": order_id}]
        
        await self._send_message(cancel_message)
        logger.info(f"❌ Avbryter order: {order_id}")

    def get_wallets(self):
        """Hämta nuvarande wallet-information."""
        return self.wallets

    def get_positions(self):
        """Hämta nuvarande positioner."""
        return self.positions

    def get_orders(self):
        """Hämta nuvarande orders."""
        return self.orders

    async def disconnect(self):
        """Koppla från WebSocket."""
        self.running = False
        self.authenticated = False
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Authenticated WebSocket frånkopplad")


# Service management
authenticated_ws_client = None

async def start_authenticated_websocket_service():
    """Starta authenticated WebSocket service med API-nycklar."""
    global authenticated_ws_client
    
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("Bitfinex API keys not configured")
        
    # Kontrollera att det inte är placeholder-nycklar
    if api_key.startswith("your_") or "placeholder" in api_key:
        raise ValueError("Please configure real Bitfinex API keys")
        
    if not authenticated_ws_client:
        authenticated_ws_client = BitfinexAuthenticatedWebSocket(api_key, api_secret)
        await authenticated_ws_client.connect()
        
        # Vänta på authentication
        for i in range(10):  # Vänta max 10 sekunder
            if authenticated_ws_client.authenticated:
                break
            await asyncio.sleep(1)
        
        if not authenticated_ws_client.authenticated:
            raise Exception("Authentication timeout")
            
    return authenticated_ws_client

async def stop_authenticated_websocket_service():
    """Stoppa authenticated WebSocket service."""
    global authenticated_ws_client
    if authenticated_ws_client:
        await authenticated_ws_client.disconnect()
        authenticated_ws_client = None

def get_authenticated_websocket_client():
    """Hämta aktiv authenticated WebSocket klient."""
    return authenticated_ws_client