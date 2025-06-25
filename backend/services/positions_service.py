"""Positions service för att hämta real positions från Bitfinex via authenticated WebSocket."""

import os
import time
import logging
from typing import List, Dict, Any, Optional

import ccxt
from dotenv import load_dotenv
from backend.services.authenticated_websocket_service import get_authenticated_websocket_client
from backend.services.exchange import ExchangeService, ExchangeError

load_dotenv()
logger = logging.getLogger(__name__)

class MyBitfinex(ccxt.bitfinex):
    """Custom Bitfinex class with nonce handling."""
    _last_nonce = int(time.time() * 1000)
    
    def nonce(self):
        now = int(time.time() * 1000)
        self._last_nonce = max(self._last_nonce + 1, now)
        return self._last_nonce


def fetch_live_positions(symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Hämta live positions från Bitfinex via authenticated WebSocket (första prioritet)
    eller ExchangeService som fallback.
    
    Args:
        symbols: Optional list of symbols to filter by
        
    Returns:
        List of position dictionaries with live data from Bitfinex
        
    Raises:
        ValueError: If API keys not configured
        ExchangeError: If Bitfinex API call fails
    """
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    
    if not api_key or not api_secret:
        logger.warning("Bitfinex API keys not configured, using empty positions")
        return []
    
    # Kolla om vi har placeholder-nycklar
    has_placeholder_keys = (api_key.startswith("your_") or api_secret.startswith("your_") or
                          "placeholder" in api_key or "placeholder" in api_secret)
    
    if has_placeholder_keys:
        logger.info("🔧 [DEV] Using empty positions (placeholder API keys)")
        return []
    
    # Försök hämta från authenticated WebSocket först
    try:
        ws_client = get_authenticated_websocket_client()
        if ws_client and ws_client.authenticated:
            logger.info("📊 [WS] Fetching positions from authenticated WebSocket...")
            
            positions = ws_client.get_positions()
            if positions is not None:  # positions kan vara tom lista []
                formatted_positions = []
                
                for position in positions:
                    # Filtrera på symbols om angivet
                    if symbols and position.get("symbol") not in symbols:
                        continue
                    
                    # Konvertera WebSocket position format till vårt standardformat
                    amount = position.get("amount", 0.0)
                    if amount == 0.0:
                        continue  # Skippa stängda positioner
                    
                    # Bestäm side baserat på amount (positiv = long/buy, negativ = short/sell)
                    side = "buy" if amount > 0 else "sell"
                    amount = abs(amount)  # Gör amount positivt
                    
                    formatted_position = {
                        "id": f"pos_{position.get('symbol', 'unknown')}_{int(time.time())}",
                        "symbol": position.get("symbol", ""),
                        "side": side,
                        "amount": amount,
                        "entry_price": position.get("base_price", 0.0),
                        "pnl": position.get("pl", 0.0),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "mark_price": 0.0,  # Inte tillgängligt i position data
                        "pnl_percentage": position.get("pl_perc", 0.0),
                        "contracts": amount,  # Samma som amount för Bitfinex
                        "notional": amount * position.get("base_price", 0.0),
                        "collateral": 0.0,  # Beräknas från margin data
                        "margin_mode": "cross",  # Standard för Bitfinex
                        "maintenance_margin": 0.0,  # Inte direkt tillgängligt
                        "leverage": position.get("leverage", 1.0)
                    }
                    
                    formatted_positions.append(formatted_position)
                
                logger.info(f"✅ [WS] Successfully fetched {len(formatted_positions)} live positions")
                return formatted_positions
            
            else:
                logger.info("✅ [WS] WebSocket authenticated - no open positions")
                return []
                
    except Exception as e:
        logger.warning(f"⚠️ [WS] WebSocket position fetch failed: {e}")
    
    # Fallback till ExchangeService (REST API)
    try:
        logger.info("📊 [REST] Falling back to ExchangeService...")
        exchange_service = ExchangeService("bitfinex", api_key, api_secret)
        
        positions = exchange_service.fetch_positions(symbols)
        
        # Konvertera till format förväntat av trading systemet
        formatted_positions = []
        for position in positions:
            # Konvertera side format (long/short -> buy/sell för konsistens)
            side = "buy" if position["side"] == "long" else "sell"
            
            formatted_positions.append({
                "id": position["id"] or f"pos_{int(time.time())}",
                "symbol": position["symbol"],
                "side": side,
                "amount": position["amount"],
                "entry_price": position["entry_price"],
                "pnl": position["pnl"],
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", 
                    time.gmtime(position["timestamp"] / 1000)
                ),
                "mark_price": position["mark_price"],
                "pnl_percentage": position["pnl_percentage"],
                "contracts": position["contracts"],
                "notional": position["notional"],
                "collateral": position["collateral"],
                "margin_mode": position["margin_mode"],
                "maintenance_margin": position["maintenance_margin"]
            })
            
        logger.info(f"✅ [REST] Fetched {len(formatted_positions)} live positions")
        return formatted_positions
        
    except ExchangeError as e:
        logger.error(f"❌ [REST] Exchange error: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"❌ [REST] Failed to fetch positions: {str(e)}")
        raise ExchangeError(f"Failed to fetch positions: {str(e)}")


def get_mock_positions():
    """
    DEPRECATED: Returns mock positions for testing.
    This should NOT be used in production!
    """
    logger.warning("⚠️ [Positions] Using MOCK positions - NOT suitable for live trading!")
    return [
        {
            "id": "mock_pos_1",
            "symbol": "BTC/USD",
            "side": "buy",
            "amount": 0.1,
            "entry_price": 27000.0,
            "pnl": 320.0,
            "timestamp": "2025-05-26T08:30:00Z",  # MOCK FROM FUTURE!
        },
        {
            "id": "mock_pos_2", 
            "symbol": "ETH/USD",
            "side": "buy",
            "amount": 2.0,
            "entry_price": 1800.0,
            "pnl": -45.0,
            "timestamp": "2025-05-26T07:45:00Z",  # MOCK FROM FUTURE!
        },
    ]
