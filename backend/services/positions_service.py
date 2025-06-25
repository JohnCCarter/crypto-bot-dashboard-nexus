"""Positions service för att hämta RIKTIGA positioner från Bitfinex WebSocket."""

import os
import time
import logging
from typing import List, Dict, Any, Optional

from backend.services.authenticated_websocket_service import get_authenticated_websocket_client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def fetch_live_positions(
    symbols: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Hämta live positioner från Bitfinex via AUTHENTICATED WebSocket.
    
    Args:
        symbols: Optional list of symbols to filter by
        
    Returns:
        List of position dictionaries med live data från Bitfinex WebSocket
        
    Raises:
        ValueError: If WebSocket inte authenticated
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
        logger.info("🔧 [POSITIONS] No real API keys - returning empty positions")
        return []
    
    try:
        logger.info("📊 [POSITIONS] Fetching live positions from authenticated WebSocket...")
        
        # Hämta authenticated WebSocket klient
        client = get_authenticated_websocket_client()
        
        if not client:
            logger.warning("⚠️ [POSITIONS] Authenticated WebSocket client not available")
            return []
        
        if not client.authenticated:
            logger.warning("⚠️ [POSITIONS] WebSocket not authenticated")
            return []
        
        # Hämta positions från authenticated WebSocket
        positions = client.get_positions()
        
        if not positions:
            logger.info("✅ [POSITIONS] No positions found (normal for new account)")
            return []
        
        logger.info(f"✅ [POSITIONS] Successfully fetched {len(positions)} positions from WebSocket")
        
        # Konvertera till format förväntat av trading systemet
        formatted_positions = []
        for position in positions:
            # Filtrera på symbols om angivet
            if symbols and position["symbol"] not in symbols:
                continue
            
            # Konvertera side format (Bitfinex använder positiva/negativa amount)
            amount = float(position["amount"])
            side = "buy" if amount > 0 else "sell"
            
            formatted_position = {
                "id": f"pos_{position['symbol']}_{int(time.time())}",
                "symbol": position["symbol"],
                "side": side,
                "amount": abs(amount),
                "entry_price": float(position["base_price"]),
                "pnl": float(position["pl"]),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "mark_price": 0.0,  # Inte tillgängligt i basic position data
                "pnl_percentage": float(position["pl_perc"]),
                "contracts": abs(amount),  # Samma som amount för spot
                "notional": abs(amount) * float(position["base_price"]),
                "collateral": 0.0,  # Spot trading har ingen collateral
                "margin_mode": "isolated",  # Default för paper trading
                "maintenance_margin": 0.0,  # Spot trading
                "leverage": float(position["leverage"]) if position["leverage"] else 1.0,
                "unrealized_pnl": float(position["pl"]),
                "margin_funding": float(position["margin_funding"]),
                "margin_funding_type": position["margin_funding_type"],
                "price_liq": float(position["price_liq"]) if position["price_liq"] else 0.0,
                "status": position["status"]
            }
            
            formatted_positions.append(formatted_position)
            
            logger.info(f"   📊 {formatted_position['symbol']}: {formatted_position['side']} {formatted_position['amount']} @ {formatted_position['entry_price']} (PnL: {formatted_position['pnl']})")
            
        logger.info(f"✅ [POSITIONS] Processed {len(formatted_positions)} live positions")
        return formatted_positions
        
    except Exception as e:
        logger.error(f"❌ [POSITIONS] Failed to fetch positions from WebSocket: {str(e)}")
        raise ValueError(f"Failed to fetch positions from Bitfinex WebSocket: {str(e)}")


def get_mock_positions():
    """
    DEPRECATED: Returns mock positions for testing.
    This should NOT be used in production!
    """
    logger.warning("⚠️ [POSITIONS] Using MOCK positions - NOT suitable for live trading!")
    return [
        {
            "id": "mock_pos_1",
            "symbol": "tBTCUSD",
            "side": "buy",
            "amount": 0.1,
            "entry_price": 27000.0,
            "pnl": 320.0,
            "timestamp": "2025-05-26T08:30:00Z",  # MOCK FROM FUTURE!
        },
        {
            "id": "mock_pos_2", 
            "symbol": "tETHUSD",
            "side": "buy",
            "amount": 2.0,
            "entry_price": 1800.0,
            "pnl": -45.0,
            "timestamp": "2025-05-26T07:45:00Z",  # MOCK FROM FUTURE!
        },
    ]
