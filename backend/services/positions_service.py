"""Positions service for fetching real positions from Bitfinex."""

import os
import time
import logging
from typing import List, Dict, Any, Optional

import ccxt
from dotenv import load_dotenv

from backend.services.exchange import ExchangeService, ExchangeError

load_dotenv()


class MyBitfinex(ccxt.bitfinex):
    """Custom Bitfinex class with nonce handling."""
    _last_nonce = int(time.time() * 1000)
    
    def nonce(self):
        now = int(time.time() * 1000)
        self._last_nonce = max(self._last_nonce + 1, now)
        return self._last_nonce


def fetch_live_positions(
    symbols: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Fetch live positions from Bitfinex.
    
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
        logging.warning(
            "Bitfinex API keys not configured, using empty positions"
        )
        return []
    
    try:
        # Create exchange service
        exchange_service = ExchangeService("bitfinex", api_key, api_secret)
        
        # Fetch live positions
        positions = exchange_service.fetch_positions(symbols)
        
        # Convert to format expected by trading system
        formatted_positions = []
        for position in positions:
            # Convert side format (long/short -> buy/sell for consistency)
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
            
        logging.info(
            f"✅ [Positions] Fetched {len(formatted_positions)} live positions"
        )
        return formatted_positions
        
    except ExchangeError as e:
        logging.error(f"❌ [Positions] Exchange error: {str(e)}")
        raise e
    except Exception as e:
        logging.error(f"❌ [Positions] Failed to fetch positions: {str(e)}")
        raise ExchangeError(f"Failed to fetch positions: {str(e)}")


def get_mock_positions():
    """
    DEPRECATED: Returns mock positions for testing.
    This should NOT be used in production!
    """
    logging.warning(
        "⚠️ [Positions] Using MOCK positions - NOT suitable for live trading!"
    )
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
