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


def get_order_metadata_for_symbol(exchange_service, symbol: str) -> Dict[str, Any]:
    """
    Get recent order metadata to detect if trades were margin or spot.
    This helps classify current positions correctly.
    """
    try:
        # Fetch recent orders for this symbol
        orders = exchange_service.fetch_orders(symbol, limit=10)
        
        margin_orders = 0
        spot_orders = 0
        total_margin_amount = 0.0
        total_spot_amount = 0.0
        
        for order in orders:
            # Check if order was filled (has an amount that was filled)
            filled_amount = order.get('filled', 0)
            if filled_amount > 0:
                # Check order type/info for margin indicators
                order_info = order.get('info', {})
                order_type = order_info.get('type', '').upper()
                
                # Bitfinex margin orders have specific type signatures
                if 'MARGIN' in order_type or order_info.get('isMargin', False):
                    margin_orders += 1
                    total_margin_amount += filled_amount
                    logging.info(
                        f"📊 [Orders] Found MARGIN order: {symbol} "
                        f"amount={filled_amount:.6f}"
                    )
                else:
                    spot_orders += 1
                    total_spot_amount += filled_amount
                    logging.info(
                        f"📊 [Orders] Found SPOT order: {symbol} "
                        f"amount={filled_amount:.6f}"
                    )
        
        return {
            'margin_orders': margin_orders,
            'spot_orders': spot_orders,
            'total_margin_amount': total_margin_amount,
            'total_spot_amount': total_spot_amount,
            'predominantly_margin': total_margin_amount > total_spot_amount
        }
        
    except Exception as e:
        logging.warning(f"❌ [Orders] Failed to get metadata for {symbol}: {e}")
        return {
            'margin_orders': 0,
            'spot_orders': 0,
            'total_margin_amount': 0.0,
            'total_spot_amount': 0.0,
            'predominantly_margin': False
        }


def fetch_live_positions(symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fetch live positions from Bitfinex using enhanced margin/spot detection.
    
    This implementation:
    1. Fetches traditional margin positions 
    2. Analyzes order history to classify crypto holdings
    3. Creates separate margin/spot positions based on actual trading history

    Args:
        symbols: Optional list of symbols to filter by

    Returns:
        List of position dictionaries with correct margin/spot classification

    Raises:
        ValueError: If exchange service not available
        ExchangeError: If Bitfinex API call fails
    """
    exchange_service = get_shared_exchange_service()
    if not exchange_service:
        logging.warning("Exchange service not available, returning empty positions")
        return []

    try:
        # STEP 1: Fetch traditional margin positions first
        margin_positions = []
        try:
            positions = exchange_service.fetch_positions(symbols)
            for position in positions:
                # Only include active margin positions
                size = position.get("size") or position.get("amount") or 0
                if abs(float(size)) > 0:
                    position_data = {
                        "id": f"margin_{position.get('id', int(time.time()))}",
                        "symbol": position["symbol"],
                        "side": "buy" if float(size) > 0 else "sell",
                        "amount": abs(float(size)),
                        "entry_price": float(position.get("entryPrice", 0)),
                        "mark_price": float(
                            position.get("markPrice") or 
                            position.get("lastPrice", 0)
                        ),
                        "pnl": float(position.get("unrealizedPnl", 0)),
                        "pnl_percentage": float(position.get("percentage", 0)),
                        "timestamp": int(time.time() * 1000),
                        "contracts": float(size),
                        "notional": float(position.get("notional", 0)),
                        "collateral": float(position.get("collateral", 0)),
                        "margin_mode": position.get("marginMode", "isolated"),
                        "maintenance_margin": float(
                            position.get("maintenanceMargin", 0)
                        ),
                        "position_type": "margin",  # True margin position
                        "leverage": float(position.get("leverage", 1.0)),
                    }
                    margin_positions.append(position_data)
                    
            logging.info(
                f"✅ [Positions] Fetched {len(margin_positions)} margin positions"
            )
        except Exception as e:
            logging.info(
                f"📊 [Positions] No margin positions found "
                f"(normal for spot trading): {e}"
            )

        # STEP 2: Analyze crypto holdings and classify as margin/spot
        spot_positions = []
        classified_margin_positions = []
        
        try:
            balances = exchange_service.fetch_balance()
            
            # Process major cryptocurrencies 
            major_cryptos = ['TESTBTC', 'TESTETH', 'TESTLTC', 'BTC', 'ETH', 'LTC']
            
            for crypto in major_cryptos:
                if crypto in balances and balances[crypto] > 0:
                    # Determine symbol for analysis
                    if crypto.startswith('TEST'):
                        base_currency = crypto.replace('TEST', '')
                    else:
                        base_currency = crypto
                    symbol = f"{base_currency}/USD"
                    
                    try:
                        ticker = exchange_service.fetch_ticker(symbol)
                        amount = balances[crypto]
                        current_price = ticker['last']
                        current_value = amount * current_price
                        
                        # Analyze order history for this symbol
                        order_meta = get_order_metadata_for_symbol(
                            exchange_service, symbol
                        )
                        
                        # Classify based on order history
                        if order_meta['predominantly_margin'] and order_meta['margin_orders'] > 0:
                            # Create margin position from crypto holding
                            margin_position = {
                                "id": f"margin_{crypto}_{int(time.time())}",
                                "symbol": symbol,
                                "side": "buy",  # Holdings are long
                                "amount": amount,
                                "entry_price": current_price,  # Approximate
                                "mark_price": current_price,
                                "pnl": 0.0,  # Would need historical data
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
                            classified_margin_positions.append(margin_position)
                            logging.info(
                                f"📊 [Positions] Classified as MARGIN: {crypto} = "
                                f"{amount:.6f} (based on order history)"
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
                                "position_type": "spot",  # Pure spot holding
                                "leverage": 1.0,  # Spot is always 1:1
                            }
                            spot_positions.append(spot_position)
                            logging.info(
                                f"📊 [Positions] Classified as SPOT: {crypto} = "
                                f"{amount:.6f} (based on order history)"
                            )
                        
                    except Exception as e:
                        logging.warning(
                            f"❌ [Positions] Failed to process {symbol}: {e}"
                        )
                        
        except Exception as e:
            logging.error(f"❌ [Positions] Failed to analyze holdings: {e}")

        # STEP 3: Combine all position types
        all_positions = (
            margin_positions + 
            classified_margin_positions + 
            spot_positions
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
            f"(True Margin: {len(margin_positions)}, "
            f"Classified Margin: {len(classified_margin_positions)}, "
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
