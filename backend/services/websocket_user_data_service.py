#!/usr/bin/env python3
"""
🔐 Bitfinex User Data WebSocket Service
Hanterar autentiserade streams för order executions, balances och positioner

Detta kompletterar websocket_market_service.py med user-specifik data.
"""

import asyncio
import websockets
import json
import logging
import hmac
import hashlib
import time
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class OrderFill:
    """Order execution data"""
    id: str
    order_id: str
    symbol: str
    side: str
    amount: float
    price: float
    fee: float
    timestamp: datetime

@dataclass
class LiveOrder:
    """Live order status"""
    id: str
    symbol: str
    side: str
    amount: float
    price: float
    filled: float
    remaining: float
    status: str
    timestamp: datetime

@dataclass
class LiveBalance:
    """Live balance update"""
    currency: str
    available: float
    total: float
    timestamp: datetime

class BitfinexUserDataClient:
    """
    Bitfinex WebSocket client för authenticated user data streams.
    
    Hanterar:
    - Order executions (fills)
    - Live order status updates
    - Real-time balance changes
    - Position updates
    """
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws = None
        self.authenticated = False
        self.callbacks = {
            'fills': [],
            'orders': [],
            'balances': []
        }
        
    async def connect(self):
        """Connect and authenticate WebSocket"""
        try:
            self.ws = await websockets.connect('wss://api-pub.bitfinex.com/ws/2')
            
            # Authenticate connection
            await self._authenticate()
            
            # Start message handler
            asyncio.create_task(self._handle_messages())
            
            logger.info("✅ User data WebSocket connected and authenticated")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect user data WebSocket: {e}")
            
    async def disconnect(self):
        """Disconnect WebSocket"""
        if self.ws:
            await self.ws.close()
            self.authenticated = False
            logger.info("🔌 User data WebSocket disconnected")
            
    async def _authenticate(self):
        """Authenticate WebSocket connection"""
        try:
            # Generate authentication payload
            nonce = str(int(time.time() * 1000000))
            auth_payload = f'AUTH{nonce}'
            signature = hmac.new(
                self.api_secret.encode(),
                auth_payload.encode(),
                hashlib.sha384
            ).hexdigest()
            
            auth_message = {
                'event': 'auth',
                'apiKey': self.api_key,
                'authSig': signature,
                'authPayload': auth_payload,
                'authNonce': nonce
            }
            
            await self.ws.send(json.dumps(auth_message))
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            
    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 User data WebSocket connection closed")
        except Exception as e:
            logger.error(f"❌ Message handler error: {e}")
            
    async def _process_message(self, data):
        """Process incoming message and route to appropriate handler"""
        
        if isinstance(data, dict):
            # Handle authentication response
            if data.get('event') == 'auth':
                if data.get('status') == 'OK':
                    self.authenticated = True
                    logger.info("✅ WebSocket authentication successful")
                else:
                    logger.error(f"❌ Authentication failed: {data}")
                return
                
        if isinstance(data, list) and len(data) >= 2:
            channel_id, message_data = data[0], data[1]
            
            # Handle different message types
            if message_data == 'hb':
                # Heartbeat
                return
                
            # Order executions (fills)
            if isinstance(message_data, list) and len(message_data) > 0:
                msg_type = message_data[0] if isinstance(message_data[0], str) else None
                
                if msg_type == 'te':  # Trade execution
                    await self._handle_trade_execution(message_data[1])
                elif msg_type == 'on':  # Order new
                    await self._handle_order_new(message_data[1])
                elif msg_type == 'ou':  # Order update
                    await self._handle_order_update(message_data[1])
                elif msg_type == 'oc':  # Order cancel
                    await self._handle_order_cancel(message_data[1])
                elif msg_type == 'ws':  # Wallet snapshot
                    await self._handle_wallet_snapshot(message_data[1])
                elif msg_type == 'wu':  # Wallet update
                    await self._handle_wallet_update(message_data[1])
                    
    async def _handle_trade_execution(self, execution_data):
        """Handle trade execution (fill) data"""
        try:
            # Bitfinex trade execution format: [ID, PAIR, MTS_CREATE, ORDER_ID, EXEC_AMOUNT, EXEC_PRICE, ...]
            if len(execution_data) >= 6:
                fill = OrderFill(
                    id=str(execution_data[0]),
                    order_id=str(execution_data[3]),
                    symbol=execution_data[1],
                    side='buy' if execution_data[4] > 0 else 'sell',
                    amount=abs(float(execution_data[4])),
                    price=float(execution_data[5]),
                    fee=float(execution_data[9]) if len(execution_data) > 9 else 0.0,
                    timestamp=datetime.fromtimestamp(execution_data[2] / 1000)
                )
                
                # Notify all fill callbacks
                for callback in self.callbacks['fills']:
                    await self._safe_callback(callback, fill)
                    
        except Exception as e:
            logger.error(f"❌ Error processing trade execution: {e}")
            
    async def _handle_order_update(self, order_data):
        """Handle live order status update"""
        try:
            # Bitfinex order format: [ID, GID, CID, SYMBOL, MTS_CREATE, MTS_UPDATE, AMOUNT, AMOUNT_ORIG, TYPE, ...]
            if len(order_data) >= 16:
                order = LiveOrder(
                    id=str(order_data[0]),
                    symbol=order_data[3],
                    side='buy' if float(order_data[7]) > 0 else 'sell',
                    amount=abs(float(order_data[7])),
                    price=float(order_data[16]) if order_data[16] else 0.0,
                    filled=abs(float(order_data[7])) - abs(float(order_data[6])),
                    remaining=abs(float(order_data[6])),
                    status=self._parse_order_status(order_data[13]),
                    timestamp=datetime.fromtimestamp(order_data[5] / 1000)
                )
                
                # Notify all order callbacks
                for callback in self.callbacks['orders']:
                    await self._safe_callback(callback, order)
                    
        except Exception as e:
            logger.error(f"❌ Error processing order update: {e}")
            
    async def _handle_wallet_update(self, wallet_data):
        """Handle live balance update"""
        try:
            # Bitfinex wallet format: [WALLET_TYPE, CURRENCY, BALANCE, UNSETTLED_INTEREST, BALANCE_AVAILABLE]
            if len(wallet_data) >= 5:
                balance = LiveBalance(
                    currency=wallet_data[1],
                    available=float(wallet_data[4]) if wallet_data[4] else 0.0,
                    total=float(wallet_data[2]) if wallet_data[2] else 0.0,
                    timestamp=datetime.now()
                )
                
                # Notify all balance callbacks
                for callback in self.callbacks['balances']:
                    await self._safe_callback(callback, balance)
                    
        except Exception as e:
            logger.error(f"❌ Error processing wallet update: {e}")
            
    def _parse_order_status(self, status_info):
        """Parse Bitfinex order status"""
        if not status_info:
            return 'open'
            
        status_str = str(status_info)
        if 'EXECUTED' in status_str:
            return 'filled'
        elif 'CANCELED' in status_str:
            return 'cancelled'
        elif 'PARTIALLY FILLED' in status_str:
            return 'partial'
        else:
            return 'open'
            
    async def subscribe_fills(self, callback: Callable):
        """Subscribe to order execution updates"""
        self.callbacks['fills'].append(callback)
        logger.info("✅ Subscribed to order fills")
        
    async def subscribe_orders(self, callback: Callable):
        """Subscribe to live order status updates"""
        self.callbacks['orders'].append(callback)
        logger.info("✅ Subscribed to order updates")
        
    async def subscribe_balances(self, callback: Callable):
        """Subscribe to live balance updates"""
        self.callbacks['balances'].append(callback)
        logger.info("✅ Subscribed to balance updates")
        
    async def _safe_callback(self, callback, data):
        """Safely execute callback with error handling"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")

# Global instance för user data client
_user_data_client = None

async def get_user_data_client(api_key: str, api_secret: str) -> BitfinexUserDataClient:
    """Get or create global user data client"""
    global _user_data_client
    
    if _user_data_client is None:
        _user_data_client = BitfinexUserDataClient(api_key, api_secret)
        await _user_data_client.connect()
        
    return _user_data_client

async def stop_user_data_client():
    """Stop global user data client"""
    global _user_data_client
    
    if _user_data_client:
        await _user_data_client.disconnect()
        _user_data_client = None