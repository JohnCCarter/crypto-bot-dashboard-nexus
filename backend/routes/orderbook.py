"""Orderbook API endpoints with live Bitfinex data - NO MOCK DATA."""

from flask import jsonify, request, current_app
import pandas as pd

from backend.services.exchange import ExchangeService, ExchangeError
from backend.strategies.indicators import find_fvg_zones


def get_exchange_service():
    """Get exchange service from app context."""
    try:
        if hasattr(current_app, '_services') and current_app._services:
            return current_app._services.get("exchange")
        
        current_app.logger.warning(
            "Exchange service not available, cannot fetch live orderbook"
        )
        return None
    except Exception as e:
        current_app.logger.error(f"Failed to get exchange service: {e}")
        return None


def register(app):
    @app.route("/api/orderbook/<symbol>", methods=["GET"])
    def get_orderbook(symbol):
        """
        Get live orderbook from Bitfinex (NO MOCK DATA).
        
        Query parameters:
        - limit: Number of levels per side (default: 20, max: 100)
        
        Returns:
            200: Live orderbook data from Bitfinex
            503: Exchange service not available
            500: Server error
        """
        current_app.logger.info(f"📋 [Orderbook] Live orderbook request for {symbol}")
        
        try:
            exchange = get_exchange_service()
            if not exchange:
                current_app.logger.error(
                    "❌ [Orderbook] CRITICAL: Exchange service not available. "
                    "NO MOCK ORDERBOOK will be provided for trading safety."
                )
                return jsonify({
                    "error": "Exchange service not available",
                    "message": "Live orderbook required for trading - "
                             "no fallback data"
                }), 503
            
            limit = min(int(request.args.get('limit', 20)), 100)
            
            # Convert symbol format if needed (BTCUSD -> BTC/USD)
            if '/' not in symbol and len(symbol) >= 6:
                if symbol.endswith('USD'):
                    base = symbol[:-3]
                    quote = symbol[-3:]
                    formatted_symbol = f"{base}/{quote}"
                else:
                    formatted_symbol = symbol
            else:
                formatted_symbol = symbol
                
            current_app.logger.info(
                f"📋 [Orderbook] Fetching live orderbook for "
                f"{formatted_symbol} with limit {limit}"
            )
            
            orderbook = exchange.fetch_order_book(formatted_symbol, limit)
            
            current_app.logger.info(
                f"✅ [Orderbook] Successfully fetched orderbook with "
                f"{len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks"
            )
            
            return jsonify(orderbook), 200
            
        except ExchangeError as e:
            current_app.logger.error(
                f"❌ [Orderbook] CRITICAL: Exchange error: {str(e)}. "
                f"NO MOCK DATA will be provided for trading safety."
            )
            return jsonify({
                "error": f"Exchange error: {str(e)}",
                "message": "Live orderbook unavailable - no fallback data"
            }), 503
        except Exception as e:
            current_app.logger.error(f"❌ [Orderbook] Failed to fetch orderbook: {str(e)}")
            import traceback
            current_app.logger.error(
                f"❌ [Orderbook] Stack trace: {traceback.format_exc()}"
            )
            return jsonify({
                "error": f"Failed to fetch orderbook: {str(e)}",
                "message": "Live orderbook unavailable"
            }), 500

    @app.route("/api/indicators/fvg", methods=["POST"])
    def get_fvg_zones():
        """
        Get FVG zones for given OHLCV data.
        
        Request body:
            {
                "data": object,           # OHLCV data
                "min_gap_size": number,   # Optional minimum gap size
                "direction": string       # Optional direction filter
            }
        
        Returns:
            200: List of FVG zones
            400: Invalid input
            500: Server error
        """
        try:
            if not request.is_json:
                return jsonify({
                    "error": "Content-Type must be application/json"
                }), 400
                
            req = request.get_json()
            if "data" not in req:
                return jsonify({"error": "Missing 'data' field"}), 400
                
            try:
                df = pd.DataFrame(req["data"])
            except Exception:
                return jsonify({"error": "Invalid data format"}), 400
                
            min_gap_size = req.get("min_gap_size", 0.0)
            direction = req.get("direction", "both")
            
            zones = find_fvg_zones(
                df, 
                min_gap_size=min_gap_size, 
                direction=direction
            )
            
            return jsonify(zones), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ [FVG] Failed to calculate FVG zones: {e}")
            return jsonify({"error": str(e)}), 500
