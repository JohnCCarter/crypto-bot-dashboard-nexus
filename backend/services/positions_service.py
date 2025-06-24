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
    Fetch live positions from Bitfinex using hybrid approach.
    
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
    exchange_service = get_shared_exchange_service()
    if not exchange_service:
        logging.warning("Exchange service not available, returning empty positions")
        return []

    try:
        # STEP 1: Try to fetch traditional margin positions first
        traditional_positions = []
        try:
            positions = exchange_service.fetch_positions(symbols)
            traditional_positions = positions
            logging.info(
                f"✅ [Positions] Fetched {len(traditional_positions)} "
                f"margin positions"
            )
        except Exception as e:
            logging.info(
                f"📊 [Positions] No margin positions found "
                f"(normal for spot trading): {e}"
            )

        # STEP 2: Create "spot positions" from cryptocurrency holdings
        spot_positions = []
        try:
            balances = exchange_service.fetch_balance()
            current_prices = {}
            
            # Get current market prices for major cryptocurrencies
            major_cryptos = ['TESTBTC', 'TESTETH', 'TESTLTC', 'BTC', 'ETH', 'LTC']
            
            for crypto in major_cryptos:
                if crypto in balances and balances[crypto] > 0:
                    # Determine symbol for price lookup
                    base_currency = (
                        crypto.replace('TEST', '') 
                        if crypto.startswith('TEST') 
                        else crypto
                    )
                    symbol = f"{base_currency}/USD"
                    
                    try:
                        ticker = exchange_service.fetch_ticker(symbol)
                        current_prices[crypto] = ticker['last']
                        
                        # Calculate position value
                        amount = balances[crypto]
                        entry_price = ticker['last']  # Current price as entry
                        current_value = amount * ticker['last']
                        
                        # Create position-like object from spot holding
                        spot_position = {
                            "id": f"spot_{crypto}_{int(time.time())}",
                            "symbol": symbol,
                            "side": "buy",  # Spot holdings are always long
                            "amount": amount,
                            "entry_price": entry_price,
                            "mark_price": ticker['last'],
                            "pnl": 0.0,  # Can't calculate without entry history
                            "pnl_percentage": 0.0,
                            "timestamp": int(time.time() * 1000),
                            "contracts": amount,
                            "notional": current_value,
                            "collateral": current_value,
                            "margin_mode": "spot",
                            "maintenance_margin": 0.0,
                            "position_type": "spot_holding"  # Identify as spot
                        }
                        
                        spot_positions.append(spot_position)
                        logging.info(
                            f"📊 [Positions] Created spot position: "
                            f"{crypto} = {amount:.6f} @ ${ticker['last']:,.2f}"
                        )
                        
                    except Exception as e:
                        logging.warning(
                            f"❌ [Positions] Failed to get price for "
                            f"{symbol}: {e}"
                        )
                        
        except Exception as e:
            logging.error(f"❌ [Positions] Failed to create spot positions: {e}")

        # STEP 3: Combine traditional margin positions + spot positions
        all_positions = traditional_positions + spot_positions
        
        # STEP 4: Filter by symbols if requested
        if symbols and all_positions:
            filtered_positions = []
            for position in all_positions:
                if position["symbol"] in symbols:
                    filtered_positions.append(position)
            all_positions = filtered_positions

        logging.info(
            f"✅ [Positions] Total positions: {len(all_positions)} "
            f"(Margin: {len(traditional_positions)}, "
            f"Spot: {len(spot_positions)})"
        )
        
        return all_positions

    except ExchangeError as e:
        logging.error(f"❌ [Positions] Exchange error: {str(e)}")
        raise e
    except Exception as e:
        logging.error(f"❌ [Positions] Failed to fetch positions: {str(e)}")
        raise ExchangeError(
            f"Failed to fetch positions: {str(e)}"
        )


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
