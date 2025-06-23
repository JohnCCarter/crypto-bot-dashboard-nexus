"""
Enhanced Bitfinex WebSocket Service
Baserat på officiell Bitfinex WebSocket API dokumentation
https://docs.bitfinex.com/docs/ws-reading-the-documentation
"""

import json
import logging
import threading
import time
import websocket
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import hmac
import hashlib

logger = logging.getLogger(__name__)


class ChannelType(Enum):
    """Supported WebSocket channel types enligt Bitfinex docs"""
    TICKER = "ticker"
    BOOK = "book"
    TRADES = "trades"
    CANDLES = "candles"
    # Authenticated channels
    AUTH = "auth"
    ORDERS = "orders"
    POSITIONS = "positions"
    WALLETS = "wallets"

class PlatformStatus(Enum):
    """Bitfinex platform status codes"""
    OPERATIVE = "operative"
    MAINTENANCE = "maintenance" 
    UNKNOWN = "unknown"

@dataclass
class ChannelSubscription:
    """WebSocket channel subscription"""
    channel: ChannelType
    symbol: Optional[str] = None
    precision: Optional[str] = None
    frequency: Optional[str] = None
    length: Optional[str] = None
    channel_id: Optional[int] = None
    active: bool = False

@dataclass
class WebSocketMetrics:
    """WebSocket connection metrics"""
    connected: bool = False
    last_heartbeat: Optional[float] = None
    last_ping: Optional[float] = None
    last_pong: Optional[float] = None
    latency_ms: Optional[float] = None
    reconnect_count: int = 0
    message_count: int = 0
    error_count: int = 0
    platform_status: PlatformStatus = PlatformStatus.UNKNOWN
    
class EnhancedBitfinexWebSocket:
    """
    Enhanced Bitfinex WebSocket client enligt officiell dokumentation
    
    Features:
    - Multiple channel subscriptions
    - Authenticated trading channels  
    - Ping/pong latency monitoring
    - Platform status handling
    - Auto-reconnection med exponential backoff
    - Rate limiting och error handling
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None,
                 use_authenticated: bool = False):
        """
        Initialize WebSocket service
        
        Args:
            api_key: Bitfinex API key för authenticated channels
            api_secret: Bitfinex API secret för authenticated channels  
            use_authenticated: Om authenticated channels ska användas
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_authenticated = use_authenticated
        
        # WebSocket URLs enligt Bitfinex dokumentation
        self.public_url = "wss://api-pub.bitfinex.com/ws/2"
        self.auth_url = "wss://api.bitfinex.com/ws/2"
        
        # State management
        self.ws: Optional[websocket.WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self.subscriptions: Dict[str, ChannelSubscription] = {}
        self.metrics = WebSocketMetrics()
        
        # Data storage - thread-safe med locks
        self._data_lock = threading.Lock()
        self.ticker_data: Dict[str, Dict] = {}
        self.orderbook_data: Dict[str, Dict] = {}
        self.trades_data: Dict[str, List] = {}
        self.wallet_data: Dict[str, Any] = {}
        self.order_data: Dict[str, Any] = {}
        self.position_data: Dict[str, Any] = {}
        
        # Callbacks för real-time updates
        self.callbacks: Dict[ChannelType, List[Callable]] = {
            channel_type: [] for channel_type in ChannelType
        }
        
        # Ping/pong tracking enligt dokumentation
        self.ping_counter = 0
        self.ping_interval = 30  # seconds
        self.heartbeat_interval = 15  # seconds enligt docs
        self.heartbeat_timeout = None
        self.ping_timeout = None
        
        # Reconnection configuration
        self.max_reconnects = 5
        self.reconnect_delay = 1  # Start with 1 second
        self.max_reconnect_delay = 60  # Max 60 seconds
        
    def connect(self) -> bool:
        """
        Establish WebSocket connection
        
        Returns:
            bool: True if connection successful
        """
        try:
            url = self.auth_url if self.use_authenticated else self.public_url
            logger.info(f"🔌 Connecting to Bitfinex WebSocket: {url}")
            
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Starta WebSocket i daemon thread
            self.ws_thread = threading.Thread(
                target=self.ws.run_forever,
                daemon=True,
                name="BitfinexWebSocket"
            )
            self.ws_thread.start()
            
            # Vänta på connection
            timeout = 10
            start_time = time.time()
            while not self.metrics.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            if self.metrics.connected:
                logger.info("✅ WebSocket connected successfully")
                self._start_ping_scheduler()
                return True
            else:
                logger.error("❌ WebSocket connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            self.metrics.error_count += 1
            return False
    
    def disconnect(self):
        """Cleanly disconnect WebSocket"""
        if self.ws:
            logger.info("🔌 Disconnecting WebSocket...")
            self.ws.close()
            self.metrics.connected = False
            
        if self.heartbeat_timeout:
            self.heartbeat_timeout.cancel()
        if self.ping_timeout:
            self.ping_timeout.cancel()
    
    def subscribe_ticker(self, symbol: str) -> bool:
        """
        Subscribe to ticker channel enligt Bitfinex docs
        
        Args:
            symbol: Trading pair (e.g., 'tBTCUSD')
            
        Returns:
            bool: True if subscription sent successfully
        """
        sub_msg = {
            "event": "subscribe",
            "channel": "ticker",
            "symbol": symbol
        }
        
        return self._send_subscription(sub_msg, ChannelType.TICKER, symbol)
    
    def subscribe_orderbook(self, symbol: str, precision: str = "P0", 
                          frequency: str = "F0", length: str = "25") -> bool:
        """
        Subscribe to order book channel
        
        Args:
            symbol: Trading pair (e.g., 'tBTCUSD')
            precision: Price aggregation level (P0-P4)
            frequency: Update frequency (F0-F1) 
            length: Number of price points (25, 100)
        """
        sub_msg = {
            "event": "subscribe", 
            "channel": "book",
            "symbol": symbol,
            "prec": precision,
            "freq": frequency,
            "len": length
        }
        
        return self._send_subscription(sub_msg, ChannelType.BOOK, symbol)
    
    def subscribe_trades(self, symbol: str) -> bool:
        """Subscribe to trades channel"""
        sub_msg = {
            "event": "subscribe",
            "channel": "trades", 
            "symbol": symbol
        }
        
        return self._send_subscription(sub_msg, ChannelType.TRADES, symbol)
    
    def authenticate(self) -> bool:
        """
        Authenticate för trading channels enligt Bitfinex docs
        
        Returns:
            bool: True if auth message sent
        """
        if not self.api_key or not self.api_secret:
            logger.error("API credentials not provided for authentication")
            return False
            
        try:
            nonce = str(int(time.time() * 1000000))
            auth_payload = f"AUTH{nonce}"
            
            signature = hmac.new(
                self.api_secret.encode(),
                auth_payload.encode(),
                hashlib.sha384
            ).hexdigest()
            
            auth_msg = {
                "event": "auth",
                "apiKey": self.api_key,
                "authSig": signature,
                "authPayload": auth_payload,
                "authNonce": nonce,
                "filter": ["trading", "wallet", "algo"]  # Subscribe to trading events
            }
            
            return self._send_message(auth_msg)
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _send_subscription(self, sub_msg: Dict, channel_type: ChannelType, 
                          symbol: Optional[str] = None) -> bool:
        """Send subscription message and track it"""
        if not self.metrics.connected:
            logger.error("Cannot subscribe - WebSocket not connected")
            return False
            
        try:
            # Send subscription
            if self._send_message(sub_msg):
                # Track subscription 
                sub_key = f"{channel_type.value}:{symbol}" if symbol else channel_type.value
                self.subscriptions[sub_key] = ChannelSubscription(
                    channel=channel_type,
                    symbol=symbol,
                    precision=sub_msg.get("prec"),
                    frequency=sub_msg.get("freq"),
                    length=sub_msg.get("len")
                )
                logger.info(f"📡 Subscribed to {channel_type.value} for {symbol}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Subscription failed: {e}")
            return False
    
    def _send_message(self, message: Dict) -> bool:
        """Send WebSocket message safely"""
        if not self.ws or not self.metrics.connected:
            return False
            
        try:
            self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            return False
    
    def _on_open(self, ws):
        """Handle WebSocket connection open"""
        logger.info("🚀 WebSocket connection opened")
        self.metrics.connected = True
        self.metrics.reconnect_count = 0
        self._reset_heartbeat_timer()
        
        # Authenticate if using authenticated channels
        if self.use_authenticated:
            self.authenticate()
    
    def _on_message(self, ws, message):
        """
        Handle incoming WebSocket messages enligt Bitfinex dokumentation
        
        Message types:
        - Info messages: System status, platform status
        - Pong messages: Latency measurement
        - Subscription confirmations
        - Data updates: Ticker, orderbook, trades, etc.
        """
        try:
            data = json.loads(message)
            self.metrics.message_count += 1
            
            # Handle different message types
            if isinstance(data, dict):
                self._handle_dict_message(data)
            elif isinstance(data, list):
                self._handle_array_message(data)
                
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            self.metrics.error_count += 1
    
    def _handle_dict_message(self, data: Dict):
        """Handle dictionary-format messages (events, info, etc.)"""
        event = data.get("event")
        
        if event == "info":
            self._handle_info_message(data)
        elif event == "subscribed":
            self._handle_subscription_confirmation(data)
        elif event == "pong":
            self._handle_pong_message(data)
        elif event == "auth":
            self._handle_auth_confirmation(data)
        elif event == "error":
            self._handle_error_message(data)
    
    def _handle_info_message(self, data: Dict):
        """
        Handle info messages enligt Bitfinex docs
        
        Critical codes:
        - 20051: Server restart
        - 20060: Maintenance start  
        - 20061: Maintenance end
        """
        platform_status = data.get("platform", {}).get("status")
        if platform_status == 1:
            self.metrics.platform_status = PlatformStatus.OPERATIVE
        elif platform_status == 0:
            self.metrics.platform_status = PlatformStatus.MAINTENANCE
            
        # Handle critical system messages
        code = data.get("code")
        if code == 20051:
            logger.warning("🔄 Bitfinex server restart - reconnecting...")
            self._reconnect()
        elif code == 20060:
            logger.warning("🔧 Bitfinex maintenance started")
            self.metrics.platform_status = PlatformStatus.MAINTENANCE
        elif code == 20061:
            logger.info("✅ Bitfinex maintenance ended")
            self.metrics.platform_status = PlatformStatus.OPERATIVE
            
        logger.info(f"ℹ️ Platform status: {self.metrics.platform_status.value}")
    
    def _handle_subscription_confirmation(self, data: Dict):
        """Handle subscription confirmation"""
        channel = data.get("channel")
        symbol = data.get("symbol", "")
        chan_id = data.get("chanId")
        
        # Update subscription with channel ID
        sub_key = f"{channel}:{symbol}" if symbol else channel
        if sub_key in self.subscriptions:
            self.subscriptions[sub_key].channel_id = chan_id
            self.subscriptions[sub_key].active = True
            logger.info(f"✅ Subscription confirmed: {channel} {symbol} (ID: {chan_id})")
    
    def _handle_pong_message(self, data: Dict):
        """Handle pong response för latency measurement"""
        self.metrics.last_pong = time.time()
        if self.metrics.last_ping:
            self.metrics.latency_ms = (self.metrics.last_pong - self.metrics.last_ping) * 1000
            logger.debug(f"🏓 Latency: {self.metrics.latency_ms:.1f}ms")
    
    def _handle_auth_confirmation(self, data: Dict):
        """Handle authentication confirmation"""
        status = data.get("status")
        if status == "OK":
            logger.info("🔐 Authentication successful")
        else:
            logger.error(f"🔐 Authentication failed: {data}")
    
    def _handle_error_message(self, data: Dict):
        """Handle error messages"""
        error_msg = data.get("msg", "Unknown error")
        error_code = data.get("code", "Unknown")
        logger.error(f"❌ WebSocket error {error_code}: {error_msg}")
        self.metrics.error_count += 1
    
    def _handle_array_message(self, data: List):
        """
        Handle array-format messages (data updates)
        
        Format enligt Bitfinex docs:
        [CHANNEL_ID, DATA] eller [CHANNEL_ID, "hb"] för heartbeat
        """
        if len(data) < 2:
            return
            
        channel_id = data[0]
        payload = data[1]
        
        # Handle heartbeat
        if payload == "hb":
            self._handle_heartbeat()
            return
            
        # Find subscription by channel ID
        subscription = self._find_subscription_by_id(channel_id)
        if not subscription:
            return
            
        # Route data to appropriate handler
        if subscription.channel == ChannelType.TICKER:
            self._handle_ticker_data(subscription.symbol, payload)
        elif subscription.channel == ChannelType.BOOK:
            self._handle_orderbook_data(subscription.symbol, payload)
        elif subscription.channel == ChannelType.TRADES:
            self._handle_trades_data(subscription.symbol, payload)
    
    def _handle_heartbeat(self):
        """Handle heartbeat message"""
        self.metrics.last_heartbeat = time.time()
        self._reset_heartbeat_timer()
    
    def _handle_ticker_data(self, symbol: str, data: List):
        """Handle ticker data update"""
        if len(data) < 10:
            return
            
        with self._data_lock:
            self.ticker_data[symbol] = {
                'symbol': symbol,
                'bid': float(data[0]),
                'bid_size': float(data[1]),
                'ask': float(data[2]),
                'ask_size': float(data[3]),
                'daily_change': float(data[4]),
                'daily_change_pct': float(data[5]),
                'last_price': float(data[6]),
                'volume': float(data[7]),
                'high': float(data[8]),
                'low': float(data[9]),
                'timestamp': time.time()
            }
            
        # Trigger callbacks
        self._trigger_callbacks(ChannelType.TICKER, symbol, self.ticker_data[symbol])
    
    def _handle_orderbook_data(self, symbol: str, data):
        """Handle order book data update"""
        with self._data_lock:
            if symbol not in self.orderbook_data:
                self.orderbook_data[symbol] = {'bids': [], 'asks': []}
                
            # Handle full snapshot vs incremental updates
            if isinstance(data[0], list):
                # Full snapshot
                bids = []
                asks = []
                for level in data:
                    if len(level) >= 3:
                        price, count, amount = level[0], level[1], level[2]
                        if amount > 0:
                            bids.append({'price': price, 'amount': amount, 'count': count})
                        else:
                            asks.append({'price': price, 'amount': abs(amount), 'count': count})
                            
                self.orderbook_data[symbol] = {
                    'bids': sorted(bids, key=lambda x: x['price'], reverse=True),
                    'asks': sorted(asks, key=lambda x: x['price'])
                }
            else:
                # Incremental update - implement orderbook maintenance
                pass
                
        self._trigger_callbacks(ChannelType.BOOK, symbol, self.orderbook_data[symbol])
    
    def _handle_trades_data(self, symbol: str, data):
        """Handle trades data update"""
        with self._data_lock:
            if symbol not in self.trades_data:
                self.trades_data[symbol] = []
                
            # Add new trades (limit to last 100)
            if isinstance(data[0], list):
                # Multiple trades
                for trade in data:
                    if len(trade) >= 4:
                        self.trades_data[symbol].append({
                            'id': trade[0],
                            'timestamp': trade[1],
                            'amount': trade[2],
                            'price': trade[3]
                        })
            else:
                # Single trade
                if len(data) >= 4:
                    self.trades_data[symbol].append({
                        'id': data[0],
                        'timestamp': data[1], 
                        'amount': data[2],
                        'price': data[3]
                    })
                    
            # Keep only last 100 trades
            self.trades_data[symbol] = self.trades_data[symbol][-100:]
            
        self._trigger_callbacks(ChannelType.TRADES, symbol, self.trades_data[symbol])
    
    def _find_subscription_by_id(self, channel_id: int) -> Optional[ChannelSubscription]:
        """Find subscription by channel ID"""
        for subscription in self.subscriptions.values():
            if subscription.channel_id == channel_id:
                return subscription
        return None
    
    def _trigger_callbacks(self, channel_type: ChannelType, symbol: str, data: Any):
        """Trigger registered callbacks for data updates"""
        for callback in self.callbacks.get(channel_type, []):
            try:
                callback(symbol, data)
            except Exception as e:
                logger.error(f"Callback error for {channel_type.value}: {e}")
    
    def _start_ping_scheduler(self):
        """Start ping scheduler för latency monitoring"""
        def ping_scheduler():
            while self.metrics.connected:
                time.sleep(self.ping_interval)
                if self.metrics.connected:
                    self._send_ping()
                    
        ping_thread = threading.Thread(target=ping_scheduler, daemon=True)
        ping_thread.start()
    
    def _send_ping(self):
        """Send ping message enligt Bitfinex docs"""
        self.ping_counter += 1
        ping_msg = {
            "event": "ping",
            "cid": self.ping_counter
        }
        
        if self._send_message(ping_msg):
            self.metrics.last_ping = time.time()
            logger.debug(f"🏓 Ping sent (#{self.ping_counter})")
    
    def _reset_heartbeat_timer(self):
        """Reset heartbeat timeout timer"""
        if self.heartbeat_timeout:
            self.heartbeat_timeout.cancel()
            
        def heartbeat_timeout():
            logger.warning("💔 Heartbeat timeout - reconnecting...")
            self._reconnect()
            
        self.heartbeat_timeout = threading.Timer(
            self.heartbeat_interval + 5,  # 5 second grace period
            heartbeat_timeout
        )
        self.heartbeat_timeout.start()
    
    def _reconnect(self):
        """Reconnect WebSocket med exponential backoff"""
        if self.metrics.reconnect_count >= self.max_reconnects:
            logger.error("❌ Max reconnection attempts reached")
            return
            
                 self.metrics.reconnect_count += 1
         delay = min(
             self.reconnect_delay * (2 ** self.metrics.reconnect_count),
             self.max_reconnect_delay
         )
        
        logger.info(f"🔄 Reconnecting in {delay} seconds (attempt {self.metrics.reconnect_count})")
        time.sleep(delay)
        
        self.disconnect()
        self.connect()
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"❌ WebSocket error: {error}")
        self.metrics.error_count += 1
        self.metrics.connected = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.warning(f"🔌 WebSocket closed: {close_status_code} - {close_msg}")
        self.metrics.connected = False
        
        # Auto-reconnect if not intentional close
        if close_status_code != 1000:  # 1000 = normal close
            self._reconnect()
    
    # Public data access methods
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get latest ticker data för symbol"""
        with self._data_lock:
            return self.ticker_data.get(symbol)
    
    def get_orderbook(self, symbol: str) -> Optional[Dict]:
        """Get latest orderbook data för symbol"""
        with self._data_lock:
            return self.orderbook_data.get(symbol)
    
    def get_trades(self, symbol: str) -> Optional[List]:
        """Get latest trades data för symbol"""
        with self._data_lock:
            return self.trades_data.get(symbol, [])
    
    def get_metrics(self) -> WebSocketMetrics:
        """Get WebSocket connection metrics"""
        return self.metrics
    
    def register_callback(self, channel_type: ChannelType, callback: Callable):
        """Register callback för real-time data updates"""
        self.callbacks[channel_type].append(callback)
    
    def get_subscription_status(self) -> Dict[str, bool]:
        """Get status of all subscriptions"""
        return {
            sub_key: sub.active 
            for sub_key, sub in self.subscriptions.items()
        }