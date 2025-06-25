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


def get_position_type_from_metadata(symbol: str) -> str:
    """
    Get position type (margin/spot) from stored order metadata.

    Args:
        symbol: Trading symbol (e.g. "BTC/USD" or "TESTBTC/TESTUSD")

    Returns:
        "margin" or "spot" based on recent order metadata
    """
    try:
        if hasattr(current_app, "_order_metadata"):
            # Check both original symbol and normalized symbol
            symbols_to_check = [symbol]

            # Add normalized version (BTC/USD from TESTBTC/TESTUSD)
            if symbol.startswith("TEST"):
                normalized = symbol.replace("TEST", "").replace("TESTUSD", "USD")
                symbols_to_check.append(normalized)

            # Also check reverse (TESTBTC/TESTUSD from BTC/USD)
            if not symbol.startswith("TEST"):
                test_version = symbol
                test_version = test_version.replace("BTC", "TESTBTC")
                test_version = test_version.replace("ETH", "TESTETH")
                test_version = test_version.replace("LTC", "TESTLTC")
                test_version = test_version.replace("/USD", "/TESTUSD")
                symbols_to_check.append(test_version)

            for check_symbol in symbols_to_check:
                if check_symbol in current_app._order_metadata:
                    order_meta = current_app._order_metadata[check_symbol]
                    # Check if metadata is recent (within 24 hours)
                    if time.time() - order_meta["timestamp"] < 86400:
                        position_type = order_meta["position_type"]
                        logging.info(
                            f"📊 [Positions] Using metadata for {symbol}: "
                            f"{position_type.upper()} (found via {check_symbol})"
                        )
                        return position_type
                    else:
                        # Clean up old metadata
                        del current_app._order_metadata[check_symbol]
                        logging.info(
                            f"🧹 [Positions] Cleaned old metadata for "
                            f"{check_symbol}"
                        )
    except Exception as e:
        logging.warning(f"Error getting metadata for {symbol}: {e}")

    # Default to spot if no metadata
    return "spot"


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
        margin_positions_from_holdings = []

        try:
            balances = exchange_service.fetch_balance()

            # Get current market prices for major cryptocurrencies
            major_cryptos = ["TESTBTC", "TESTETH", "TESTLTC", "BTC", "ETH", "LTC"]

            for crypto in major_cryptos:
                if crypto in balances and balances[crypto] > 0:
                    # Determine symbol for price lookup
                    base_currency = (
                        crypto.replace("TEST", "")
                        if crypto.startswith("TEST")
                        else crypto
                    )
                    symbol = f"{base_currency}/USD"

                    try:
                        ticker = exchange_service.fetch_ticker(symbol)
                        amount = balances[crypto]
                        current_price = ticker["last"]
                        current_value = amount * current_price

                        # Check if this should be margin or spot position
                        position_type = get_position_type_from_metadata(symbol)

                        if position_type == "margin":
                            # Create margin-classified position
                            margin_position = {
                                "id": f"margin_{crypto}_{int(time.time())}",
                                "symbol": symbol,
                                "side": "buy",  # Holdings are always long
                                "amount": amount,
                                "entry_price": current_price,
                                "mark_price": current_price,
                                "pnl": 0.0,  # Would need historical entry data
                                "pnl_percentage": 0.0,
                                "timestamp": int(time.time() * 1000),
                                "contracts": amount,
                                "notional": current_value,
                                "collateral": current_value,
                                "margin_mode": "cross",
                                "maintenance_margin": current_value * 0.1,  # 10%
                                "position_type": "margin",  # From margin trading
                                "leverage": 1.0,  # Conservative estimate
                            }
                            margin_positions_from_holdings.append(margin_position)
                            logging.info(
                                f"📊 [Positions] Created MARGIN position: "
                                f"{crypto} = {amount:.6f} @ ${current_price:,.2f}"
                            )
                        else:
                            # Create spot position from crypto holding
                            spot_position = {
                                "id": f"spot_{crypto}_{int(time.time())}",
                                "symbol": symbol,
                                "side": "buy",  # Spot holdings are always long
                                "amount": amount,
                                "entry_price": current_price,
                                "mark_price": current_price,
                                "pnl": 0.0,  # Spot positions show no P&L
                                "pnl_percentage": 0.0,
                                "timestamp": int(time.time() * 1000),
                                "contracts": amount,
                                "notional": current_value,
                                "collateral": current_value,
                                "margin_mode": "spot",
                                "maintenance_margin": 0.0,
                                "position_type": position_type,  # From meta
                                "leverage": 1.0,  # Spot is always 1:1
                            }
                            spot_positions.append(spot_position)
                            logging.info(
                                f"📊 [Positions] Created SPOT position: "
                                f"{crypto} = {amount:.6f} @ ${current_price:,.2f}"
                            )

                    except Exception as e:
                        logging.warning(
                            f"❌ [Positions] Failed to get price for " f"{symbol}: {e}"
                        )

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

        return all_positions

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
