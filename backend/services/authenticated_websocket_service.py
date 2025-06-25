"""
Authenticated WebSocket service för Bitfinex med riktiga API-nycklar.
Baserat på Bitfinex WebSocket dokumentation och WssClient exempel.
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
    Authenticated WebSocket klient för Bitfinex med API-nycklar.
    Följer https://bitfinex.readthedocs.io/en/latest/websocket.html
    """
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.uri = "wss://api.bitfinex.com/ws/2"  # Authenticated endpoint
        self.websocket = None
        self.subscriptions = {}
        self.callbacks = {}
        self.running = False
        self.authenticated = False
        self.nonce_multiplier = 1.0
        
    async def connect(self):
        """Anslut till Bitfinex authenticated WebSocket."""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            logger.info("✅ Authenticated WebSocket ansluten till Bitfinex")
            
            # Starta message handler
            asyncio.create_task(self._handle_messages())
            
            # Autentisera omedelbart
            await self.authenticate()
            
        except Exception as e:
            logger.error(f"❌ Authenticated WebSocket anslutning misslyckades: {e}")
            raise

    async def authenticate(self):
        """
        Autentiserar WebSocket sessionen med API-nycklar.
        Följer Bitfinex dokumentation för authentication.
        """
        try:
            nonce = str(int(time.time() * 1000000 * self.nonce_multiplier))
            auth_payload = f"AUTH{nonce}"
            signature = hmac.new(
                self.api_secret.encode(),
                auth_payload.encode(),
                hashlib.sha384
            ).hexdigest()
            
            auth_message = {
                "event": "auth",
                "apiKey": self.api_key,
                "authSig": signature,
                "authPayload": auth_payload,
                "authNonce": nonce,
                "filter": ["trading", "wallet", "balance"]  # Begränsa till trading data
            }
            
            await self._send_message(auth_message)
            logger.info("🔐 Skickar authentication request...")
            
        except Exception as e:
            logger.error(f"❌ Authentication fel: {e}")
            raise

    async def subscribe_to_ticker(self, symbol: str, callback: Callable):
        """
        Prenumerera på ticker via authenticated channel.
        Detta ger oss både public och private data för symbolen.
        """
        # Bitfinex format
        if not symbol.startswith('t'):
            symbol = f"t{symbol}"
            
        channel_id = f"ticker_{symbol}"
        self.callbacks[channel_id] = callback
        
        subscribe_msg = {
            "event": "subscribe",
            "channel": "ticker",
            "symbol": symbol
        }
        
        await self._send_message(subscribe_msg)
        logger.info(f"📡 Authenticated ticker subscription: {symbol}")

    async def subscribe_to_trades(self, symbol: str, callback: Callable):
        """Prenumerera på trades med authenticated access."""
        if not symbol.startswith('t'):
            symbol = f"t{symbol}"
            
        channel_id = f"trades_{symbol}"
        self.callbacks[channel_id] = callback
        
        subscribe_msg = {
            "event": "subscribe",
            "channel": "trades",
            "symbol": symbol
        }
        
        await self._send_message(subscribe_msg)
        logger.info(f"💱 Authenticated trades subscription: {symbol}")

    async def subscribe_to_orderbook(self, symbol: str, callback: Callable, precision: str = "P0"):
        """Prenumerera på orderbook med authenticated access."""
        if not symbol.startswith('t'):
            symbol = f"t{symbol}"
            
        channel_id = f"book_{symbol}"
        self.callbacks[channel_id] = callback
        
        subscribe_msg = {
            "event": "subscribe",
            "channel": "book",
            "symbol": symbol,
            "prec": precision,
            "freq": "F0",  # Real-time
            "len": "25"    # 25 levels
        }
        
        await self._send_message(subscribe_msg)
        logger.info(f"📚 Authenticated orderbook subscription: {symbol}")

    async def subscribe_to_candles(self, symbol: str, timeframe: str, callback: Callable):
        """
        Prenumerera på OHLC candles med authenticated access.
        Timeframe: 1m, 5m, 15m, 30m, 1h, 3h, 6h, 12h, 1D, 7D, 14D, 1M
        """
        if not symbol.startswith('t'):
            symbol = f"t{symbol}"
            
        key = f"trade:{timeframe}:{symbol}"
        channel_id = f"candles_{symbol}_{timeframe}"
        self.callbacks[channel_id] = callback
        
        subscribe_msg = {
            "event": "subscribe",
            "channel": "candles",
            "key": key
        }
        
        await self._send_message(subscribe_msg)
        logger.info(f"🕯️ Authenticated candles subscription: {symbol} ({timeframe})")

    async def new_order(self, order_type: str, symbol: str, amount: float, price: float = None):
        """
        Placera ny order via WebSocket.
        Följer Bitfinex WssClient.new_order() exempel.
        """
        if not self.authenticated:
            raise Exception("Must be authenticated to place orders")
            
        # Generate client ID (timestamp)
        cid = int(time.time() * 1000)
        
        # Format symbol
        if not symbol.startswith('t'):
            symbol = f"t{symbol}"
            
        order_data = [
            0,  # ID (0 for new orders)
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
        logger.info(f"📋 Placing authenticated order: {order_type} {amount} {symbol} @ {price}")
        
        return cid

    async def cancel_order(self, order_id: int):
        """Avbryt order via WebSocket."""
        if not self.authenticated:
            raise Exception("Must be authenticated to cancel orders")
            
        cancel_message = [0, "oc", None, {"id": order_id}]
        
        await self._send_message(cancel_message)
        logger.info(f"❌ Cancelling authenticated order: {order_id}")

    async def ping(self, channel: str = "auth"):
        """Ping Bitfinex för connection test."""
        ping_message = {
            "event": "ping",
            "cid": int(time.time() * 1000)
        }
        
        await self._send_message(ping_message)
        logger.debug(f"🏓 Ping sent on channel: {channel}")

    async def calc(self, calculations: List[str]):
        """
        Begär specifika beräkningar från Bitfinex.
        calculations kan vara: margin_sym_SYMBOL, funding_sym_SYMBOL, position_SYMBOL, wallet_WALLET_TYPE_CURRENCY
        """
        if not self.authenticated:
            raise Exception("Must be authenticated for calculations")
            
        calc_message = [0, "calc", None, calculations]
        
        await self._send_message(calc_message)
        logger.info(f"🧮 Requesting calculations: {calculations}")

    async def _send_message(self, message):
        """Skicka meddelande till WebSocket."""
        if self.websocket:
            await self.websocket.send(json.dumps(message))

    async def _handle_messages(self):
        """Hantera inkommande meddelanden."""
        try:
            async for message in self.websocket:
                await self._process_message(json.loads(message))
        except Exception as e:
            logger.error(f"❌ Authenticated WebSocket meddelande fel: {e}")
            self.running = False

    async def _process_message(self, data):
        """Processera inkommande meddelanden."""
        try:
            if isinstance(data, dict):
                # Event meddelanden
                if data.get("event") == "auth":
                    if data.get("status") == "OK":
                        self.authenticated = True
                        logger.info("✅ Authentication framgångsrik!")
                    else:
                        logger.error(f"❌ Authentication misslyckades: {data}")
                        
                elif data.get("event") == "subscribed":
                    channel_id = f"{data['channel']}_{data.get('symbol', data.get('key', ''))}"
                    self.subscriptions[data['chanId']] = channel_id
                    logger.info(f"✅ Authenticated subscription aktiv: {channel_id}")
                    
                elif data.get("event") == "pong":
                    logger.debug("🏓 Pong received")
                    
            elif isinstance(data, list):
                # Channel data meddelanden
                if len(data) >= 2:
                    channel_id_num = data[0]
                    
                    if channel_id_num == 0:
                        # Authenticated channel (orders, wallets, positions)
                        await self._handle_authenticated_data(data)
                    elif channel_id_num in self.subscriptions:
                        # Public data channels
                        channel_id = self.subscriptions[channel_id_num]
                        await self._handle_public_data(channel_id, data[1])
                        
        except Exception as e:
            logger.error(f"❌ Fel vid processering av authenticated meddelande: {e}")

    async def _handle_authenticated_data(self, data):
        """Hantera authenticated data (orders, balances, positions)."""
        try:
            if len(data) >= 3:
                msg_type = data[1]
                
                if msg_type == "ws":  # Wallet snapshot
                    logger.info(f"💰 Wallet snapshot: {data[2]}")
                elif msg_type == "wu":  # Wallet update
                    logger.info(f"💰 Wallet update: {data[2]}")
                elif msg_type == "ps":  # Position snapshot
                    logger.info(f"📊 Position snapshot: {data[2]}")
                elif msg_type == "pu":  # Position update
                    logger.info(f"📊 Position update: {data[2]}")
                elif msg_type == "os":  # Order snapshot
                    logger.info(f"📋 Order snapshot: {data[2]}")
                elif msg_type == "ou":  # Order update
                    logger.info(f"📋 Order update: {data[2]}")
                elif msg_type == "on":  # Order new
                    logger.info(f"✅ New order: {data[2]}")
                elif msg_type == "oc":  # Order cancelled
                    logger.info(f"❌ Order cancelled: {data[2]}")
                elif msg_type == "te":  # Trade executed
                    logger.info(f"💱 Trade executed: {data[2]}")
                elif msg_type == "tu":  # Trade update
                    logger.info(f"💱 Trade update: {data[2]}")
                    
        except Exception as e:
            logger.error(f"❌ Authenticated data fel: {e}")

    async def _handle_public_data(self, channel_id: str, data):
        """Hantera public market data."""
        try:
            # Ticker data
            if channel_id.startswith('ticker_'):
                if len(data) >= 10:
                    symbol = channel_id.replace('ticker_t', '')
                    
                    market_data = AuthenticatedMarketData(
                        symbol=symbol,
                        price=float(data[6]),
                        volume=float(data[7]),
                        bid=float(data[0]),
                        ask=float(data[2]),
                        timestamp=datetime.now()
                    )
                    
                    if channel_id in self.callbacks:
                        await self._safe_callback(self.callbacks[channel_id], market_data)
            
            # Orderbook data
            elif channel_id.startswith('book_'):
                # Same as before but with authenticated context
                pass
                
            # Trades data  
            elif channel_id.startswith('trades_'):
                # Same as before but with authenticated context
                pass
                
            # Candles data
            elif channel_id.startswith('candles_'):
                symbol = channel_id.split('_')[1]
                timeframe = channel_id.split('_')[2]
                
                candle_data = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
                
                if channel_id in self.callbacks:
                    await self._safe_callback(self.callbacks[channel_id], candle_data)
                    
        except Exception as e:
            logger.error(f"❌ Public data fel: {e}")

    async def _safe_callback(self, callback, data):
        """Säker callback execution."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"❌ Callback fel: {e}")

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
    """Hämta aktiv authenticated WebSocket klient."""
    return authenticated_ws_client