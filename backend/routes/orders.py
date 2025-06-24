"""Order management API endpoints with real Bitfinex integration."""

import time
import logging
from typing import Optional

from flask import current_app, jsonify, request

from backend.services.validation import validate_order_data
from backend.services.exchange import ExchangeError
from backend.services.symbol_mapper import SymbolMapper

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not available in all environments
    pass


def get_shared_exchange_service():
    """Get shared exchange service from app context to avoid nonce conflicts."""
    try:
        if hasattr(current_app, "_services") and current_app._services:
            return current_app._services.get("exchange")
        
        current_app.logger.warning(
            "Exchange service not available in app context"
        )
        return None
    except Exception as e:
        current_app.logger.error(
            f"Failed to get shared exchange service: {e}"
        )
        return None


def register(app):
    """Register order endpoints."""

    @app.route("/api/orders", methods=["GET"])
    def get_orders():
        """
        Get open orders from Bitfinex.

        Returns:
            200: List of open orders from Bitfinex
            500: Server error
        """
        current_app.logger.info("📋 [Orders] GET open orders request")

        try:
            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                current_app.logger.warning(
                    "⚠️ [Orders] No exchange service available"
                )
                return jsonify({"orders": []}), 200

            # Fetch open orders from Bitfinex
            open_orders = exchange_service.fetch_open_orders()

            current_app.logger.info(
                f"✅ [Orders] Retrieved {len(open_orders)} open orders"
            )

            return jsonify({"orders": open_orders}), 200

        except ExchangeError as e:
            current_app.logger.error(f"❌ [Orders] Exchange error: {e}")
            return jsonify({"orders": []}), 200  # Empty rather than error
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({"error": "Failed to fetch orders"}), 500

    @app.route("/api/orders", methods=["POST"])
    def place_order():
        """
        Place new order on Bitfinex.

        Request body:
            {
                "symbol": str,          # Trading pair (e.g. "BTC/USD")
                "order_type": str,      # "market" or "limit"
                "side": str,            # "buy" or "sell"
                "amount": float,        # Order size
                "price": float,         # Required for limit orders
                "position_type": str,   # "margin" or "spot"
                "leverage": float,      # Optional leverage
                "stop_loss": float,     # Optional stop loss
                "take_profit": float    # Optional take profit
            }

        Returns:
            201: Order placed successfully
            400: Invalid input data
            500: Server error
        """
        current_app.logger.info("📋 [Orders] POST order request")

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing JSON body"}), 400

            # Validate order data
            validation_result = validate_order_data(data)
            if not validation_result["valid"]:
                return (
                    jsonify(
                        {
                            "error": "Invalid order data",
                            "details": validation_result["errors"],
                        }
                    ),
                    400,
                )

            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                current_app.logger.error(
                    "❌ [Orders] Cannot place order - no exchange service"
                )
                return (
                    jsonify(
                        {
                            "error": "Order service not available",
                            "details": "Exchange service not configured",
                        }
                    ),
                    503,
                )

            # Place order on Bitfinex using shared service (thread-safe nonce)
            # Include position_type for margin/spot differentiation
            position_type = data.get("position_type", "spot")  # Default to spot
            order = exchange_service.create_order(
                symbol=data["symbol"],
                order_type=data["order_type"],
                side=data["side"],
                amount=float(data["amount"]),
                price=float(data.get("price", 0)),
                position_type=position_type,
            )

            # Store order metadata for position classification
            if hasattr(current_app, '_order_metadata'):
                # Normalize symbol for metadata storage
                # (TESTBTC/TESTUSD -> BTC/USD)
                normalized_symbol = (
                    data["symbol"].replace('TEST', '').replace('TESTUSD', 'USD')
                )
                
                current_app._order_metadata[normalized_symbol] = {
                    'position_type': position_type,
                    'timestamp': time.time(),
                    'side': data["side"],
                    'amount': float(data["amount"]),
                    'order_id': order.get('id'),
                    'original_symbol': data["symbol"],
                }
                current_app.logger.info(
                    f"📊 [Order Metadata] Saved {position_type.upper()} order: "
                    f"{data['symbol']} -> {normalized_symbol} {data['side']} {data['amount']}"
                )

            current_app.logger.info(f"✅ [Orders] Order placed: {order['id']}")

            return (
                jsonify({"message": "Order placed successfully", "order": order}),
                201,
            )

        except ExchangeError as e:
            current_app.logger.error(f"❌ [Orders] Exchange error: {e}")
            return jsonify({"error": "Failed to place order", "details": str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({"error": "Failed to place order", "details": str(e)}), 500

    @app.route("/api/orders/<order_id>", methods=["DELETE"])
    def cancel_order(order_id: str):
        """
        Cancel order on Bitfinex.

        Args:
            order_id: Bitfinex order ID

        Returns:
            200: Order cancelled successfully
            404: Order not found
            500: Server error
        """
        current_app.logger.info(f"📋 [Orders] DELETE order: {order_id}")

        try:
            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                return jsonify({"error": "Order service not available"}), 503

            # Cancel order on Bitfinex using shared service
            result = exchange_service.cancel_order(order_id)

            current_app.logger.info(f"✅ [Orders] Order cancelled: {order_id}")

            return (
                jsonify(
                    {
                        "message": f"Order {order_id} cancelled successfully",
                        "order": result,
                    }
                ),
                200,
            )

        except ExchangeError as e:
            if "not found" in str(e).lower():
                return jsonify({"error": "Order not found"}), 404
            current_app.logger.error(f"❌ [Orders] Cancel error: {e}")
            return jsonify({"error": "Failed to cancel order", "details": str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({"error": "Failed to cancel order"}), 500

    @app.route("/api/orders/history", methods=["GET"])
    def get_order_history():
        """
        Get order history from Bitfinex.

        Query parameters:
            symbol: Optional filter by trading pair
            limit: Maximum orders to return (default 50)

        Returns:
            200: List of historical orders from Bitfinex
            500: Server error
        """
        current_app.logger.info("📋 [Orders] GET order history request")

        try:
            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                current_app.logger.warning("⚠️ [Orders] No exchange service for history")
                return jsonify([]), 200

            # Get query parameters
            symbol = request.args.get("symbol")
            limit = int(request.args.get("limit", 50))

            # Fetch order history from Bitfinex using shared service
            symbols = [symbol] if symbol else None
            order_history = exchange_service.fetch_order_history(
                symbols=symbols, limit=limit
            )

            current_app.logger.info(
                f"✅ [Orders] Retrieved {len(order_history)} " f"historical orders"
            )

            return jsonify(order_history), 200

        except ExchangeError as e:
            current_app.logger.error(f"❌ [Orders] Exchange error: {e}")
            # Return empty array rather than error for history
            return jsonify([]), 200
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({"error": "Failed to fetch order history"}), 500

    @app.route("/api/orders/<order_id>", methods=["GET"])
    def get_order_status(order_id: str):
        """
        Get order status from Bitfinex.

        Args:
            order_id: Bitfinex order ID

        Returns:
            200: Order details
            404: Order not found
            500: Server error
        """
        current_app.logger.info(f"📋 [Orders] GET order status: {order_id}")

        try:
            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                return jsonify({"error": "Order service not available"}), 503

            # Fetch order status from Bitfinex using shared service
            order = exchange_service.fetch_order(order_id)

            current_app.logger.info(f"✅ [Orders] Order status retrieved: {order_id}")

            return jsonify(order), 200

        except ExchangeError as e:
            if "not found" in str(e).lower():
                return jsonify({"error": "Order not found"}), 404
            current_app.logger.error(f"❌ [Orders] Exchange error: {e}")
            return jsonify({"error": "Failed to fetch order status"}), 400
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({"error": "Failed to fetch order status"}), 500

    @app.route("/api/symbol-info", methods=["GET"])
    def get_symbol_info():
        """
        Get symbol information including minimum order sizes.

        Query parameters:
            symbol: Optional specific symbol to get info for

        Returns:
            200: Symbol information
            500: Server error
        """
        current_app.logger.info("📋 [Symbol Info] GET symbol info request")

        try:
            symbol = request.args.get("symbol")

            if symbol:
                # Get info for specific symbol
                minimum_size = SymbolMapper.get_minimum_order_size(symbol)
                suggested_minimum = SymbolMapper.suggest_minimum_amount(symbol)
                paper_symbol = SymbolMapper.to_paper_symbol(symbol)
                
                return jsonify({
                    "symbol": symbol,
                    "minimum_order_size": minimum_size,
                    "suggested_minimum": suggested_minimum,
                    "paper_symbol": paper_symbol,
                    "paper_trading_enabled": SymbolMapper.is_paper_trading_enabled()
                }), 200
            else:
                # Get info for all symbols
                mapping_info = SymbolMapper.get_mapping_info()
                
                # Create detailed symbol info for each available symbol
                symbols_info = {}
                for std_symbol in SymbolMapper.get_available_standard_symbols():
                    symbols_info[std_symbol] = {
                        "minimum_order_size": SymbolMapper.get_minimum_order_size(std_symbol),
                        "suggested_minimum": SymbolMapper.suggest_minimum_amount(std_symbol),
                        "paper_symbol": SymbolMapper.to_paper_symbol(std_symbol)
                    }

                return jsonify({
                    "symbols": symbols_info,
                    "paper_trading_enabled": mapping_info["paper_trading_enabled"],
                    "available_symbols": mapping_info["available_symbols"]
                }), 200

        except Exception as e:
            current_app.logger.error(f"❌ [Symbol Info] Unexpected error: {e}")
            return jsonify({"error": "Failed to fetch symbol info"}), 500
