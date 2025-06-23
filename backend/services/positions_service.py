"""Positions service for fetching real positions from Bitfinex."""

import time
import logging
from typing import List, Dict, Any, Optional

from flask import current_app

from backend.services.exchange import ExchangeError


def get_shared_exchange_service():
    """Get shared exchange service from app context to avoid conflicts."""
    try:
        if hasattr(current_app, "_services") and current_app._services:
            return current_app._services.get("exchange")

        current_app.logger.warning("Exchange service not available in app context")
        return None
    except Exception as e:
        current_app.logger.error(f"Failed to get shared exchange service: {e}")
        return None


def fetch_live_positions(symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fetch live positions from Bitfinex using shared exchange service.

    Args:
        symbols: Optional list of symbols to filter by

    Returns:
        List of position dictionaries with live data from Bitfinex

    Raises:
        ValueError: If exchange service not available
        ExchangeError: If Bitfinex API call fails
    """
    exchange_service = get_shared_exchange_service()
    if not exchange_service:
        logging.warning("Exchange service not available, returning empty positions")
        return []

    try:
        # Fetch live positions using shared service
        positions = exchange_service.fetch_positions(symbols)

        # Convert to format expected by trading system
        formatted_positions = []
        for position in positions:
            # Convert side format (long/short -> buy/sell for consistency)
            side = "buy" if position["side"] == "long" else "sell"

            formatted_positions.append(
                {
                    "id": position["id"] or f"pos_{int(time.time())}",
                    "symbol": position["symbol"],
                    "side": side,
                    "amount": position["amount"],
                    "entry_price": position["entry_price"],
                    "pnl": position["pnl"],
                    "timestamp": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(position["timestamp"] / 1000)
                    ),
                    "mark_price": position["mark_price"],
                    "pnl_percentage": position["pnl_percentage"],
                    "contracts": position["contracts"],
                    "notional": position["notional"],
                    "collateral": position["collateral"],
                    "margin_mode": position["margin_mode"],
                    "maintenance_margin": position["maintenance_margin"],
                }
            )

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
