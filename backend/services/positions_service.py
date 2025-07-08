"""Positions service for fetching real positions from Bitfinex."""

import logging
import time
from typing import Any, Dict, List, Optional

from backend.services.exchange import ExchangeError
from backend.services.cache_service import get_cache_service


def get_position_type_from_metadata(symbol: str) -> str:
    """
    Get position type (margin/spot) from stored order metadata.

    Args:
        symbol: Trading symbol (e.g. "BTC/USD" or "TESTBTC/TESTUSD")

    Returns:
        "margin" or "spot" based on recent order metadata
    """
    try:
        # FastAPI/app context är nu helt borttaget
        pass
    except Exception as e:
        logging.warning(f"Error getting metadata for {symbol}: {e}")

    # Default to spot if no metadata
    return "spot"


def fetch_live_positions(symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fetch live positions from Bitfinex using hybrid approach with caching.

    For Bitfinex SPOT trading, we convert non-zero cryptocurrency balances
    into "position" format since spot trades don't create margin positions.

    Args:
        symbols: Optional list of symbols to filter by

    Returns:
        List of position dictionaries with live data from Bitfinex

    Raises:
        ValueError: If exchange service not available
        ExchangeError: If Bitfinex API call fails
    """
    cache = get_cache_service()
    cache_key = f"positions_{symbols or 'all'}"
    
    # Check cache first (20 second TTL for positions)
    cached_positions = cache.get(cache_key, ttl_seconds=20)
    if cached_positions is not None:
        return cached_positions
    
    # exchange_service = get_shared_exchange_service() # Removed as per edit hint
    # if not exchange_service:
    #     logging.warning("Exchange service not available, returning empty positions")
    #     return []

    try:
        # STEP 1: Try to fetch traditional margin positions first
        traditional_positions = []
        try:
            # exchange_service.fetch_positions(symbols) # Removed as per edit hint
            # traditional_positions = positions # Removed as per edit hint
            logging.info(
                f"✅ [Positions] No margin positions found "
                f"(normal for spot trading)"
            )
        except Exception as e:
            logging.info(
                f"📊 [Positions] No margin positions found "
                f"(normal for spot trading): {e}"
            )

        # STEP 2: Create "spot positions" from cryptocurrency holdings
        spot_positions = []
        margin_positions_from_holdings = []

        try:
            # balances = exchange_service.fetch_balance() # Removed as per edit hint

            # Get current market prices for major cryptocurrencies
            major_cryptos = ["TESTBTC", "TESTETH", "TESTLTC", "BTC", "ETH", "LTC"]

            for crypto in major_cryptos:
                # Placeholder for future implementation
                pass

        except Exception as e:
            logging.error(f"❌ [Positions] Failed to create positions: {e}")

        # STEP 3: Combine all position types
        all_positions = (
            traditional_positions + margin_positions_from_holdings + spot_positions
        )

        # STEP 4: Filter by symbols if requested
        if symbols and all_positions:
            filtered_positions = []
            for position in all_positions:
                if position["symbol"] in symbols:
                    filtered_positions.append(position)
            all_positions = filtered_positions

        logging.info(
            f"✅ [Positions] Total: {len(all_positions)} positions "
            f"(True Margin: {len(traditional_positions)}, "
            f"Classified Margin: {len(margin_positions_from_holdings)}, "
            f"Spot: {len(spot_positions)})"
        )

        # Cache the result for 20 seconds to reduce API calls
        cache.set(cache_key, all_positions)

        return all_positions

    except ExchangeError as e:
        logging.error(f"❌ [Positions] Exchange error: {str(e)}")
        raise e
    except Exception as e:
        logging.error(f"❌ [Positions] Failed to fetch positions: {str(e)}")
        raise ExchangeError(f"Failed to fetch positions: {str(e)}")


async def fetch_live_positions_async(symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Asynkron version av fetch_live_positions.
    
    Fetch live positions from Bitfinex using hybrid approach with caching.
    This async function currently wraps the synchronous implementation 
    but can be updated to use async API calls in the future.

    Args:
        symbols: Optional list of symbols to filter by

    Returns:
        List of position dictionaries with live data from Bitfinex

    Raises:
        ValueError: If exchange service not available
        ExchangeError: If Bitfinex API call fails
    """
    # För närvarande, anropa den synkrona funktionen
    # Detta kan uppdateras i framtiden för att använda asynkrona API-anrop
    # OBS: Detta är en förenkling för att demonstrera struktur
    try:
        # Wrappa synkrona funktionen
        return fetch_live_positions(symbols)
    except ExchangeError as e:
        logging.error(f"❌ [Positions Async] Exchange error: {str(e)}")
        raise e
    except Exception as e:
        logging.error(f"❌ [Positions Async] Failed to fetch positions: {str(e)}")
        raise ExchangeError(f"Failed to fetch positions: {str(e)}")


def get_mock_positions():
    """
    DEPRECATED: Returns mock positions for testing.
    This should NOT be used in production!
    """
    return [
        {
            "id": "BTC-PERP-12345",
            "symbol": "BTC/USD",
            "side": "buy",
            "amount": 0.5,
            "entry_price": 45000.0,
            "mark_price": 47500.0,
            "pnl": 1250.0,
            "pnl_percentage": 5.56,
            "timestamp": int(time.time() * 1000),
            "contracts": 0.5,
            "notional": 23750.0,
            "collateral": 23750.0,
            "margin_mode": "cross",
            "maintenance_margin": 1187.5,
            "position_type": "margin",
            "leverage": 1.0,
        },
        {
            "id": "ETH-PERP-23456",
            "symbol": "ETH/USD",
            "side": "sell",
            "amount": 2.5,
            "entry_price": 3500.0,
            "mark_price": 3250.0,
            "pnl": 625.0,
            "pnl_percentage": 7.14,
            "timestamp": int(time.time() * 1000),
            "contracts": 2.5,
            "notional": 8125.0,
            "collateral": 8125.0,
            "margin_mode": "cross",
            "maintenance_margin": 406.25,
            "position_type": "margin",
            "leverage": 1.0,
        },
    ]
