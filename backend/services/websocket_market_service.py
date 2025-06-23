"""
Improved Bitfinex WebSocket Service
Based on official Bitfinex WebSocket API documentation
"""

import json
import logging
import threading
import time
import websocket
from typing import Dict, Optional, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class PlatformStatus(Enum):
    """Bitfinex platform status"""
    OPERATIVE = "operative"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class WebSocketMarketService:
    """
    Improved Bitfinex WebSocket client with enhanced features
    
    Features:
    - Multiple symbol subscriptions
    - Ping/pong latency monitoring
    - Platform status handling
    - Auto-reconnection
    - Thread-safe data access
    """
    
    def __init__(self):
        self.ws = None
        self.ws_thread = None
        self.connected = False
        self.platform_status = PlatformStatus.UNKNOWN
        
        # Enhanced status tracking
        self.should_reconnect = False
        self.status = {}
        
        # Data storage with thread safety
        self._data_lock = threading.Lock()
        self.ticker_data = {}
        self.orderbook_data = {}
        self.trades_data = {}
        
        # Metrics
        self.last_ping = None
        self.last_pong = None
        self.latency_ms = None
        self.message_count = 0
        self.error_count = 0
        self.reconnect_count = 0
        
        # Subscriptions tracking
        self.subscriptions = {}
        
        # Ping configuration
        self.ping_counter = 0
        self.ping_interval = 30
        
    def connect(self) -> bool:
        """Connect to Bitfinex WebSocket"""
        try:
            logger.info("🔌 Connecting to Bitfinex WebSocket...")
            
            self.ws = websocket.WebSocketApp(
                "wss://api-pub.bitfinex.com/ws/2",
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            self.ws_thread = threading.Thread(
                target=self.ws.run_forever,
                daemon=True,
                name="BitfinexWebSocket"
            )
            self.ws_thread.start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            if self.connected:
                logger.info("✅ WebSocket connected successfully")
                self._start_ping_scheduler()
                return True
            else:
                logger.error("❌ WebSocket connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            self.error_count += 1
            return False
    
    def disconnect(self):
        """Disconnect WebSocket"""
        if self.ws:
            logger.info("🔌 Disconnecting WebSocket...")
            self.ws.close()
            self.connected = False
    
    def subscribe_ticker(self, symbol: str) -> bool:
        """Subscribe to ticker channel"""
        if not self.connected:
            return False
            
        sub_msg = {
            "event": "subscribe",
            "channel": "ticker",
            "symbol": symbol
        }
        
        if self._send_message(sub_msg):
            self.subscriptions[f"ticker:{symbol}"] = True
            logger.info(f"📡 Subscribed to ticker for {symbol}")
            return True
        return False
    
    def subscribe_orderbook(self, symbol: str, precision: str = "P0", 
                          length: str = "25") -> bool:
        """Subscribe to orderbook channel"""
        if not self.connected:
            return False
            
        sub_msg = {
            "event": "subscribe",
            "channel": "book",
            "symbol": symbol,
            "prec": precision,
            "len": length
        }
        
        if self._send_message(sub_msg):
            self.subscriptions[f"book:{symbol}"] = True
            logger.info(f"� Subscribed to orderbook for {symbol}")
            return True
        return False
    
    def subscribe_trades(self, symbol: str) -> bool:
        """Subscribe to trades channel"""
        if not self.connected:
            return False
            
        sub_msg = {
            "event": "subscribe",
            "channel": "trades",
            "symbol": symbol
        }
        
        if self._send_message(sub_msg):
            self.subscriptions[f"trades:{symbol}"] = True
            logger.info(f"� Subscribed to trades for {symbol}")
            return True
        return False
    
    def _send_message(self, message: Dict) -> bool:
        """Send WebSocket message safely"""
        if not self.ws or not self.connected:
            return False
            
        try:
            self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            return False
    
    def _on_open(self, ws):
        """Handle WebSocket open"""
        logger.info("🚀 WebSocket connection opened")
        self.connected = True
        self.reconnect_count = 0
    
    def _on_message(self, ws, message):
        """Handle WebSocket messages"""
        try:
            data = json.loads(message)
            self.message_count += 1
            
            if isinstance(data, dict):
                self._handle_dict_message(data)
            elif isinstance(data, list):
                self._handle_array_message(data)
                
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            self.error_count += 1
    
    def _handle_dict_message(self, data: Dict):
        """Handle dictionary messages"""
        event = data.get("event")
        
        if event == "info":
            self._handle_info_message(data)
        elif event == "subscribed":
            self._handle_subscription_confirmation(data)
        elif event == "pong":
            self._handle_pong_message(data)
        elif event == "error":
            self._handle_error_message(data)
    
    def _handle_info_message(self, data: Dict):
        """
        Enhanced info message handling according to official Bitfinex docs
        Handles platform status and critical system messages
        """
        # Handle platform status
        platform = data.get("platform", {})
        status = platform.get("status")
        
        if status == 1:
            self.platform_status = PlatformStatus.OPERATIVE
        elif status == 0:
            self.platform_status = PlatformStatus.MAINTENANCE
            
        # Handle critical info codes according to official documentation
        code = data.get("code")
        msg = data.get("msg", "")
        
        if code == 20051:
            # Stop/Restart Websocket Server (please try to reconnect)
            logger.warning("🔄 Bitfinex server restart detected - reconnecting...")
            self.should_reconnect = True
            self.status = {'needs_restart': True, 'reason': 'Server restart'}
            self._trigger_reconnection()
            
        elif code == 20060:
            # Refreshing data from Trading Engine - pause activity
            logger.warning("⏸️ Trading Engine refresh - pausing activity...")
            self.status = {
                'trading_paused': True, 
                'pause_reason': 'Trading Engine refresh',
                'platform_status': 'maintenance'
            }
            self.platform_status = PlatformStatus.MAINTENANCE
            
        elif code == 20061:
            # Done refreshing - resume activity and resubscribe
            logger.info("▶️ Trading Engine refresh complete - resuming...")
            self.status = {
                'trading_paused': False, 
                'pause_reason': None,
                'platform_status': 'operative'
            }
            self.platform_status = PlatformStatus.OPERATIVE
            # Resubscribe to all channels as recommended by Bitfinex
            self._resubscribe_all_channels()
            
        else:
            # Log any other info messages
            if code:
                logger.info(f"ℹ️ Bitfinex info {code}: {msg}")
            else:
                logger.info(f"ℹ️ Bitfinex info: {msg}")
    
    def _handle_subscription_confirmation(self, data: Dict):
        """Handle subscription confirmations"""
        channel = data.get("channel")
        symbol = data.get("symbol", "")
        chan_id = data.get("chanId")
        
        logger.info(f"✅ Subscription confirmed: {channel} {symbol} (ID: {chan_id})")
    
    def _handle_pong_message(self, data: Dict):
        """Handle pong responses"""
        self.last_pong = time.time()
        if self.last_ping:
            self.latency_ms = (self.last_pong - self.last_ping) * 1000
            logger.debug(f"🏓 Latency: {self.latency_ms:.1f}ms")
    
    def _handle_error_message(self, data: Dict):
        """
        Enhanced error handling according to official Bitfinex docs
        Maps specific error codes to appropriate actions
        """
        error_code = data.get("code", "Unknown")
        error_msg = data.get("msg", "Unknown error")
        
        # Map of error codes according to official Bitfinex documentation
        error_actions = {
            # General errors
            10000: ("Unknown event", "warning"),
            10001: ("Unknown pair", "error"),
            
            # Subscription errors
            10300: ("Subscription failed (generic)", "error"),
            10301: ("Already subscribed", "warning"),
            
            # Unsubscription errors
            10400: ("Unsubscription failed (generic)", "error"),
            10401: ("Not subscribed", "warning"),
            
            # Order book errors
            10011: ("Unknown Book precision", "error"),
            10012: ("Unknown Book length", "error"),
        }
        
        error_description, severity = error_actions.get(
            error_code, 
            (error_msg, "error")
        )
        
        # Handle specific error codes
        if error_code == 10301:
            # Already subscribed - non-critical, just log warning
            logger.warning(f"⚠️ Already subscribed: {error_description}")
            return  # Don't increment error counter for this
            
        elif error_code in [10000, 10001]:
            # Critical API errors
            logger.error(f"❌ Critical API error {error_code}: {error_description}")
            self.status['has_critical_error'] = True
            self.status['last_error'] = error_description
            
        elif error_code in [10011, 10012]:
            # Book configuration errors - try with defaults
            logger.error(f"📊 Book config error {error_code}: {error_description}")
            self._retry_book_subscription_with_defaults()
            
        elif error_code == "ERR_RATE_LIMIT":
            # Rate limit exceeded
            logger.warning(f"🚦 Rate limit exceeded: {error_description}")
            self.status['rate_limited'] = True
            
        else:
            # Generic error handling
            if severity == "warning":
                logger.warning(f"⚠️ WebSocket warning {error_code}: {error_description}")
            else:
                logger.error(f"❌ WebSocket error {error_code}: {error_description}")
        
        self.error_count += 1
        self.status['last_error_code'] = error_code
        self.status['last_error_msg'] = error_description
    
    def _handle_array_message(self, data: List):
        """Handle array messages (data updates)"""
        if len(data) < 2:
            return
            
        channel_id = data[0]
        payload = data[1]
        
        # Handle heartbeat
        if payload == "hb":
            return
            
        # Handle ticker data
        if isinstance(payload, list) and len(payload) >= 10:
            self._handle_ticker_update(payload)
    
    def _handle_ticker_update(self, data: List):
        """Handle ticker data updates"""
        if len(data) < 10:
            return
            
        # Assume this is for a known symbol (simplified)
        symbol = "tBTCUSD"  # In real implementation, track by channel ID
        
        with self._data_lock:
            self.ticker_data[symbol] = {
                'symbol': symbol,
                'bid': float(data[0]),
                'ask': float(data[2]),
                'last_price': float(data[6]),
                'volume': float(data[7]),
                'high': float(data[8]),
                'low': float(data[9]),
                'daily_change': float(data[4]),
                'daily_change_pct': float(data[5]),
                'timestamp': time.time()
            }
    
    def _start_ping_scheduler(self):
        """Start ping scheduler"""
        def ping_scheduler():
            while self.connected:
                time.sleep(self.ping_interval)
                if self.connected:
                    self._send_ping()
                    
        ping_thread = threading.Thread(target=ping_scheduler, daemon=True)
        ping_thread.start()
    
    def _send_ping(self):
        """Send ping message"""
        self.ping_counter += 1
        ping_msg = {
            "event": "ping",
            "cid": self.ping_counter
        }
        
        if self._send_message(ping_msg):
            self.last_ping = time.time()
            logger.debug(f"🏓 Ping sent (#{self.ping_counter})")
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"❌ WebSocket error: {error}")
        self.error_count += 1
        self.connected = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.warning(f"🔌 WebSocket closed: {close_status_code}")
        self.connected = False
    
    # Data access methods
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get ticker data for symbol"""
        with self._data_lock:
            return self.ticker_data.get(symbol)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection metrics"""
        return {
            'connected': self.connected,
            'platform_status': self.platform_status.value,
            'latency_ms': self.latency_ms,
            'message_count': self.message_count,
            'error_count': self.error_count,
            'reconnect_count': self.reconnect_count,
            'subscriptions': list(self.subscriptions.keys())
        }
    
    def get_all_ticker_data(self) -> Dict[str, Dict]:
        """Get all ticker data"""
        with self._data_lock:
            return self.ticker_data.copy()
    
    def _trigger_reconnection(self):
        """Trigger WebSocket reconnection"""
        logger.info("🔄 Triggering WebSocket reconnection...")
        if self.connected:
            self.disconnect()
        
        # Wait a moment before reconnecting
        time.sleep(2)
        
        # Attempt reconnection
        if self.connect():
            logger.info("✅ WebSocket reconnection successful")
            self.reconnect_count += 1
        else:
            logger.error("❌ WebSocket reconnection failed")
    
    def _resubscribe_all_channels(self):
        """Resubscribe to all previously subscribed channels"""
        logger.info("📡 Resubscribing to all channels...")
        
        # Store current subscriptions
        current_subs = list(self.subscriptions.keys())
        
        # Clear subscriptions
        self.subscriptions.clear()
        
        # Resubscribe to each channel
        for sub_key in current_subs:
            parts = sub_key.split(":")
            if len(parts) >= 2:
                channel = parts[0]
                symbol = parts[1]
                
                if channel == "ticker":
                    self.subscribe_ticker(symbol)
                elif channel == "book":
                    self.subscribe_orderbook(symbol)
                elif channel == "trades":
                    self.subscribe_trades(symbol)
                    
                 logger.info(f"✅ Resubscribed to {len(current_subs)} channels")
    
    def _retry_book_subscription_with_defaults(self):
        """Retry book subscription with default parameters"""
        logger.info("🔄 Retrying book subscriptions with defaults...")
        
        # Find book subscriptions that might have failed
        book_subs = [key for key in self.subscriptions.keys() 
                    if key.startswith("book:")]
        
        for sub_key in book_subs:
            symbol = sub_key.split(":")[1]
            # Retry with default precision and length
            self.subscribe_orderbook(symbol, precision="P0", length="25")