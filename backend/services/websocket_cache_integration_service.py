"""
🌐🔐 WebSocket-Cache Integration Service
Kombinerar real-time WebSocket user data med cache-systemet för att minimera nonce-förbrukande REST API calls enligt hybrid-setup planen.

SYFTE:
- Streama balances, orders, positions via WebSocket (nonce-free)
- Cache WebSocket data för offline access
- Provide fallback till REST API endast när nödvändigt
- Drastiskt reducera private API calls som förbrukar nonce
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from backend.services.cache_service import get_cache_service
from backend.services.websocket_user_data_service import (
    BitfinexUserDataClient,
    LiveBalance,
    LiveOrder,
    OrderFill,
    Position
)

logger = logging.getLogger(__name__)


@dataclass
class WebSocketCacheStats:
    """Statistics för WebSocket cache efficiency"""
    websocket_updates_received: int = 0
    cache_updates_from_ws: int = 0
    rest_fallback_calls: int = 0
    nonce_calls_saved: int = 0
    uptime_seconds: float = 0.0
    last_ws_update: Optional[float] = None


class WebSocketCacheIntegrationService:
    """
    🌐 Integrerar WebSocket real-time data med aggressive caching.
    
    FÖRDELAR:
    - Real-time balances utan nonce consumption
    - Live order updates utan REST polling
    - Position changes via WebSocket
    - Smart fallback till REST endast vid behov
    - Dramatisk reduction av private API calls
    
    STRATEGI:
    - Primary: WebSocket streams för real-time data
    - Secondary: Aggressiv cache för offline periods
    - Tertiary: REST API endast som last resort
    """
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.cache = get_cache_service()
        
        # WebSocket client
        self.ws_client: Optional[BitfinexUserDataClient] = None
        self.ws_connected = False
        self.ws_authenticated = False
        
        # Statistics och monitoring
        self.stats = WebSocketCacheStats()
        self.startup_time = time.time()
        self.last_heartbeat = time.time()
        
        # Data freshness tracking
        self.data_freshness = {
            "balances": 0.0,
            "orders": 0.0,
            "positions": 0.0
        }
        
        # Callbacks för real-time updates
        self.balance_callbacks: List[Callable] = []
        self.order_callbacks: List[Callable] = []
        self.position_callbacks: List[Callable] = []
        
        logger.info("🌐 WebSocket-Cache Integration Service initialized")
    
    async def start(self) -> bool:
        """
        Starta WebSocket-cache integration.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            # Initialize WebSocket client
            self.ws_client = BitfinexUserDataClient(self.api_key, self.api_secret)
            
            # Register callbacks för cache updates
            await self._register_websocket_callbacks()
            
            # Connect WebSocket
            await self.ws_client.connect()
            
            # Wait för authentication
            await asyncio.sleep(2)  # Give time för auth
            
            if self.ws_client.authenticated:
                self.ws_connected = True
                self.ws_authenticated = True
                self.stats.websocket_updates_received = 0
                self.stats.cache_updates_from_ws = 0
                
                logger.info("✅ WebSocket-Cache integration started successfully")
                return True
            else:
                logger.error("❌ WebSocket authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start WebSocket-Cache integration: {e}")
            return False
    
    async def stop(self):
        """Stop WebSocket-cache integration gracefully."""
        if self.ws_client:
            await self.ws_client.disconnect()
        
        self.ws_connected = False
        self.ws_authenticated = False
        
        logger.info("🔌 WebSocket-Cache integration stopped")
    
    async def _register_websocket_callbacks(self):
        """Register callbacks för WebSocket data → cache updates."""
        if not self.ws_client:
            return
        
        # Balance updates → cache
        await self.ws_client.subscribe_balances(self._on_balance_update)
        
        # Order updates → cache
        await self.ws_client.subscribe_orders(self._on_order_update)
        
        # Order fills → cache
        await self.ws_client.subscribe_fills(self._on_fill_update)
        
        logger.info("🔗 WebSocket callbacks registered för cache integration")
    
    async def _on_balance_update(self, balance: LiveBalance):
        """Handle live balance update via WebSocket → cache."""
        try:
            # Update cache med WebSocket data (NONCE-FREE!)
            cache_key = f"ws_balance_{balance.currency}"
            self.cache.set_smart(cache_key, {
                "currency": balance.currency,
                "available": balance.available,
                "total": balance.total,
                "timestamp": balance.timestamp.isoformat(),
                "source": "websocket"
            }, data_type="balances")
            
            # Update all balances cache
            balances_cache_key = "balances"
            current_balances = self.cache.get_smart(balances_cache_key, "balances") or {}
            
            # Update the specific currency balance
            if balance.currency not in current_balances:
                current_balances[balance.currency] = {}
            
            current_balances[balance.currency].update({
                "free": balance.available,
                "used": balance.total - balance.available,
                "total": balance.total
            })
            
            # Cache updated balances för 90s (aggressive strategy)
            self.cache.set_smart(balances_cache_key, current_balances, "balances")
            
            # Update statistics
            self.stats.websocket_updates_received += 1
            self.stats.cache_updates_from_ws += 1
            self.stats.nonce_calls_saved += 1  # Each WS update saves one REST call
            self.data_freshness["balances"] = time.time()
            self.stats.last_ws_update = time.time()
            
            logger.info(f"💰 Balance update via WebSocket: {balance.currency} = {balance.available} (NONCE SAVED)")
            
            # Notify balance callbacks
            for callback in self.balance_callbacks:
                await self._safe_callback(callback, balance)
                
        except Exception as e:
            logger.error(f"❌ Error processing balance update: {e}")
    
    async def _on_order_update(self, order: LiveOrder):
        """Handle live order update via WebSocket → cache."""
        try:
            # Update individual order cache
            cache_key = f"ws_order_{order.id}"
            self.cache.set_smart(cache_key, {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "amount": order.amount,
                "price": order.price,
                "filled": order.filled,
                "remaining": order.remaining,
                "status": order.status,
                "timestamp": order.timestamp.isoformat(),
                "source": "websocket"
            }, data_type="open_orders")
            
            # Update open orders cache
            open_orders_key = "open_orders"
            current_orders = self.cache.get_smart(open_orders_key, "open_orders") or []
            
            # Remove existing order med samma ID
            current_orders = [o for o in current_orders if o.get("id") != order.id]
            
            # Add updated order if still active
            if order.status not in ["filled", "cancelled"]:
                current_orders.append({
                    "id": order.id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "amount": order.amount,
                    "price": order.price,
                    "filled": order.filled,
                    "remaining": order.remaining,
                    "status": order.status,
                    "timestamp": order.timestamp.isoformat()
                })
            
            # Cache updated orders för 15s (volatile data)
            self.cache.set_smart(open_orders_key, current_orders, "open_orders")
            
            # Update statistics
            self.stats.websocket_updates_received += 1
            self.stats.cache_updates_from_ws += 1
            self.stats.nonce_calls_saved += 1
            self.data_freshness["orders"] = time.time()
            self.stats.last_ws_update = time.time()
            
            logger.info(f"📋 Order update via WebSocket: {order.symbol} {order.side} (NONCE SAVED)")
            
            # Notify order callbacks
            for callback in self.order_callbacks:
                await self._safe_callback(callback, order)
                
        except Exception as e:
            logger.error(f"❌ Error processing order update: {e}")
    
    async def _on_fill_update(self, fill: OrderFill):
        """Handle order fill via WebSocket → cache."""
        try:
            # Cache order fill
            cache_key = f"ws_fill_{fill.id}"
            self.cache.set_smart(cache_key, {
                "id": fill.id,
                "order_id": fill.order_id,
                "symbol": fill.symbol,
                "side": fill.side,
                "amount": fill.amount,
                "price": fill.price,
                "fee": fill.fee,
                "timestamp": fill.timestamp.isoformat(),
                "source": "websocket"
            }, data_type="order_history")
            
            # Update recent fills cache
            fills_key = "recent_fills"
            recent_fills = self.cache.get_smart(fills_key, "order_history") or []
            
            # Add new fill
            recent_fills.insert(0, {
                "id": fill.id,
                "order_id": fill.order_id,
                "symbol": fill.symbol,
                "side": fill.side,
                "amount": fill.amount,
                "price": fill.price,
                "fee": fill.fee,
                "timestamp": fill.timestamp.isoformat()
            })
            
            # Keep only last 100 fills
            recent_fills = recent_fills[:100]
            
            # Cache för 3 minutes
            self.cache.set_smart(fills_key, recent_fills, "order_history")
            
            # Update statistics
            self.stats.websocket_updates_received += 1
            self.stats.cache_updates_from_ws += 1
            self.stats.nonce_calls_saved += 1
            self.stats.last_ws_update = time.time()
            
            logger.info(f"✅ Order fill via WebSocket: {fill.symbol} {fill.amount} @ {fill.price} (NONCE SAVED)")
            
        except Exception as e:
            logger.error(f"❌ Error processing fill update: {e}")
    
    def get_cached_balances(self, max_age_seconds: int = 90) -> Optional[Dict[str, Any]]:
        """
        Get balances från cache (WebSocket-populated).
        
        Args:
            max_age_seconds: Maximum age of cached data
            
        Returns:
            Balances dict or None if no fresh data
        """
        # Check data freshness
        if self.data_freshness["balances"] == 0:
            return None
        
        age = time.time() - self.data_freshness["balances"]
        if age > max_age_seconds:
            logger.warning(f"⏰ Balance data too old: {age:.1f}s")
            return None
        
        # Return cached balances (populated by WebSocket)
        balances = self.cache.get_smart("balances", "balances")
        if balances:
            logger.info(f"📊 Serving cached balances (age: {age:.1f}s, WebSocket-populated)")
        
        return balances
    
    def get_cached_orders(self, max_age_seconds: int = 15) -> Optional[List[Dict[str, Any]]]:
        """
        Get open orders från cache (WebSocket-populated).
        
        Args:
            max_age_seconds: Maximum age of cached data
            
        Returns:
            Orders list or None if no fresh data
        """
        # Check data freshness
        if self.data_freshness["orders"] == 0:
            return None
        
        age = time.time() - self.data_freshness["orders"]
        if age > max_age_seconds:
            logger.warning(f"⏰ Order data too old: {age:.1f}s")
            return None
        
        # Return cached orders (populated by WebSocket)
        orders = self.cache.get_smart("open_orders", "open_orders")
        if orders:
            logger.info(f"📋 Serving cached orders (age: {age:.1f}s, WebSocket-populated)")
        
        return orders
    
    def should_use_rest_fallback(self, data_type: str, max_age: int = 60) -> bool:
        """
        Determine if REST API fallback should be used.
        
        Args:
            data_type: Type of data (balances, orders, positions)
            max_age: Maximum acceptable age in seconds
            
        Returns:
            True if REST fallback should be used
        """
        # Check WebSocket connection status
        if not self.ws_connected or not self.ws_authenticated:
            logger.warning(f"🔄 WebSocket not connected, REST fallback required för {data_type}")
            return True
        
        # Check data freshness
        last_update = self.data_freshness.get(data_type, 0)
        if last_update == 0:
            logger.info(f"📡 No WebSocket data för {data_type}, REST fallback required")
            return True
        
        age = time.time() - last_update
        if age > max_age:
            logger.warning(f"⏰ WebSocket data för {data_type} too old ({age:.1f}s), REST fallback required")
            return True
        
        return False
    
    def register_balance_callback(self, callback: Callable):
        """Register callback för real-time balance updates."""
        self.balance_callbacks.append(callback)
        logger.info("🔗 Balance callback registered")
    
    def register_order_callback(self, callback: Callable):
        """Register callback för real-time order updates."""
        self.order_callbacks.append(callback)
        logger.info("🔗 Order callback registered")
    
    def register_position_callback(self, callback: Callable):
        """Register callback för real-time position updates."""
        self.position_callbacks.append(callback)
        logger.info("🔗 Position callback registered")
    
    async def _safe_callback(self, callback: Callable, data: Any):
        """Safely execute callback med error handling."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get comprehensive WebSocket-cache integration statistics."""
        current_time = time.time()
        uptime = current_time - self.startup_time
        
        # Calculate efficiency metrics
        total_updates = self.stats.websocket_updates_received
        cache_efficiency = (self.stats.cache_updates_from_ws / max(1, total_updates)) * 100
        
        # Data freshness
        freshness_info = {}
        for data_type, last_update in self.data_freshness.items():
            if last_update > 0:
                age = current_time - last_update
                freshness_info[data_type] = {
                    "last_update_seconds_ago": round(age, 1),
                    "is_fresh": age < 60,
                    "status": "fresh" if age < 30 else "stale" if age < 90 else "expired"
                }
            else:
                freshness_info[data_type] = {
                    "last_update_seconds_ago": None,
                    "is_fresh": False,
                    "status": "no_data"
                }
        
        return {
            "connection_status": {
                "websocket_connected": self.ws_connected,
                "websocket_authenticated": self.ws_authenticated,
                "uptime_seconds": round(uptime, 1),
                "last_heartbeat_seconds_ago": round(current_time - self.last_heartbeat, 1) if self.last_heartbeat else None
            },
            "update_statistics": {
                "total_websocket_updates": total_updates,
                "cache_updates_from_websocket": self.stats.cache_updates_from_ws,
                "rest_fallback_calls": self.stats.rest_fallback_calls,
                "estimated_nonce_calls_saved": self.stats.nonce_calls_saved,
                "cache_efficiency_percent": round(cache_efficiency, 2)
            },
            "data_freshness": freshness_info,
            "nonce_savings": {
                "estimated_api_calls_saved": self.stats.nonce_calls_saved,
                "estimated_savings_percent": min(95, (self.stats.nonce_calls_saved / max(1, self.stats.nonce_calls_saved + self.stats.rest_fallback_calls)) * 100)
            },
            "callbacks_registered": {
                "balance_callbacks": len(self.balance_callbacks),
                "order_callbacks": len(self.order_callbacks),
                "position_callbacks": len(self.position_callbacks)
            }
        }
    
    def mark_rest_fallback_used(self, data_type: str):
        """Mark that REST API fallback was used (för statistics)."""
        self.stats.rest_fallback_calls += 1
        logger.warning(f"🔄 REST fallback used för {data_type} (nonce consumed)")


# Global instance - should be initialized med proper API credentials
_ws_cache_service: Optional[WebSocketCacheIntegrationService] = None


def get_websocket_cache_service(api_key: str = None, api_secret: str = None) -> Optional[WebSocketCacheIntegrationService]:
    """
    Get the global WebSocket-cache integration service.
    
    Args:
        api_key: API key för initialization (if not already initialized)
        api_secret: API secret för initialization (if not already initialized)
        
    Returns:
        WebSocketCacheIntegrationService instance or None
    """
    global _ws_cache_service
    
    if _ws_cache_service is None and api_key and api_secret:
        _ws_cache_service = WebSocketCacheIntegrationService(api_key, api_secret)
    
    return _ws_cache_service 