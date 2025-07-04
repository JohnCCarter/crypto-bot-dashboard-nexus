"""Order management API endpoints with real Bitfinex integration."""

import time

from flask import current_app, jsonify, request

from backend.services.exchange import ExchangeError
from backend.services.symbol_converter import (
    convert_ui_to_trading,
    log_symbol_conversion,
)
from backend.services.validation import validate_order_data
from backend.services.event_logger import (
    event_logger, should_suppress_routine_log, EventType
)

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

        current_app.logger.warning("Exchange service not available in app context")
        return None
    except Exception as e:
        current_app.logger.error(f"Failed to get shared exchange service: {e}")
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
        # Detta är routine polling - supprimeras enligt event_logger
        
        try:
            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                # Varning ska loggas även om supprimerat
                event_logger.log_api_error("/api/orders", "No exchange service available")
                return jsonify({"orders": []}), 200

            # Fetch open orders from Bitfinex
            open_orders = exchange_service.fetch_open_orders()

            # Endast logga om det INTE är routine polling
            if not should_suppress_routine_log("/api/orders", "GET"):
                event_logger.log_event(
                    EventType.API_ERROR,  # Using available type
                    f"Orders fetched: {len(open_orders)} open orders"
                )

            return jsonify({"orders": open_orders}), 200

        except ExchangeError as e:
            # Exchange fel ska alltid loggas
            event_logger.log_exchange_error("fetch_orders", str(e))
            return jsonify({"orders": []}), 200  # Empty rather than error
        except Exception as e:
            # Kritiska fel ska alltid loggas
            event_logger.log_api_error("/api/orders", str(e))
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
        # PLACE ORDER är en VERKLIG användaraktion - ALLTID loggas!
        
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
                event_logger.log_api_error("/api/orders", "Cannot place order - no exchange service")
                return (
                    jsonify(
                        {
                            "error": "Order service not available",
                            "details": "Exchange service not configured",
                        }
                    ),
                    503,
                )

            # Convert symbol to Bitfinex format before sending to API
            ui_symbol = data["symbol"]  # e.g., 'TESTBTC/TESTUSD'
            bitfinex_symbol = convert_ui_to_trading(
                ui_symbol
            )  # e.g., 'tTESTBTC:TESTUSD'

            # Log the symbol conversion for debugging
            log_symbol_conversion(ui_symbol, bitfinex_symbol, "order_placement")

            # Place order on Bitfinex using shared service (thread-safe nonce)
            # Include position_type for margin/spot differentiation
            position_type = data.get("position_type", "spot")  # Default to spot
            order = exchange_service.create_order(
                symbol=bitfinex_symbol,  # Use converted symbol
                order_type=data["order_type"],
                side=data["side"],
                amount=float(data["amount"]),
                price=float(data.get("price", 0)),
                position_type=position_type,
            )

            # Store order metadata for position classification
            if hasattr(current_app, "_order_metadata"):
                # Normalize symbol for metadata storage
                # (TESTBTC/TESTUSD -> BTC/USD)
                normalized_symbol = (
                    data["symbol"].replace("TEST", "").replace("TESTUSD", "USD")
                )

                current_app._order_metadata[normalized_symbol] = {
                    "position_type": position_type,
                    "timestamp": time.time(),
                    "side": data["side"],
                    "amount": float(data["amount"]),
                    "order_id": order.get("id"),
                    "original_symbol": data["symbol"],
                }

            # LOGGA VERKLIG TRADE - detta är en meningsfull händelse!
            event_logger.log_order_creation(
                symbol=data["symbol"],
                side=data["side"],
                amount=float(data["amount"]),
                price=float(data.get("price", 0)),
                order_type=data["order_type"]
            )

            return (
                jsonify({"message": "Order placed successfully", "order": order}),
                201,
            )

        except ExchangeError as e:
            # Exchange fel vid order placering ska alltid loggas
            event_logger.log_exchange_error("place_order", str(e))
            return jsonify({"error": "Failed to place order", "details": str(e)}), 400
        except Exception as e:
            # Kritiska fel ska alltid loggas
            event_logger.log_api_error("/api/orders", str(e))
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
        # Cancel order är en VERKLIG användaraktion - logga med event_logger
        event_logger.log_event(
            EventType.ORDER_CANCELLED,
            f"Cancel order request: {order_id}"
        )

        try:
            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                return jsonify({"error": "Order service not available"}), 503

            # Cancel order on Bitfinex using shared service
            result = exchange_service.cancel_order(order_id)

            # Logga framgångsrik cancellation
            event_logger.log_event(
                EventType.ORDER_CANCELLED,
                f"Order cancelled successfully: {order_id}"
            )

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
        # Order history GET är routine polling - suppress det
        if should_suppress_routine_log("/api/orders/history", "GET"):
            pass  # Suppress routine polling
        else:
            current_app.logger.info("📋 [Orders] GET order history request")

        try:
            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                current_app.logger.warning("⚠️ [Orders] No exchange service for history")
                return jsonify([]), 200

            # Get query parameters
            symbol = request.args.get("symbol")
            limit = int(request.args.get("limit", 50))

            # Convert symbol to Bitfinex format if provided
            symbols = None
            if symbol:
                bitfinex_symbol = convert_ui_to_trading(symbol)
                log_symbol_conversion(symbol, bitfinex_symbol, "order_history")
                symbols = [bitfinex_symbol]

            # Fetch order history from Bitfinex using shared service
            order_history = exchange_service.fetch_order_history(
                symbols=symbols, limit=limit
            )

            # Suppress routine history success logs
            if should_suppress_routine_log("/api/orders/history", "GET"):
                pass  # Suppress routine polling
            else:
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

        Query Parameters:
            symbol: The trading pair symbol (e.g., 'BTC/USD'), required by the exchange.

        Returns:
            200: Order details
            404: Order not found
            500: Server error
        """
        current_app.logger.info(f"📋 [Orders] GET order status: {order_id}")

        try:
            symbol = request.args.get("symbol")
            if not symbol:
                return (
                    jsonify({"error": "Missing required 'symbol' query parameter"}),
                    400,
                )

            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                return jsonify({"error": "Order service not available"}), 503

            # Convert symbol to Bitfinex format before API call
            ui_symbol = symbol  # e.g., 'TESTBTC/TESTUSD'
            bitfinex_symbol = convert_ui_to_trading(
                ui_symbol
            )  # e.g., 'tTESTBTC:TESTUSD'

            # Log the symbol conversion for debugging
            log_symbol_conversion(ui_symbol, bitfinex_symbol, "order_status")

            current_app.logger.info(
                f"📋 [Orders] Symbol converted for status check: {ui_symbol} → {bitfinex_symbol}"
            )

            # Fetch order status from Bitfinex using shared service
            order = exchange_service.fetch_order(order_id, bitfinex_symbol)

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

    @app.route("/api/trading-limitations", methods=["GET"])
    def get_trading_limitations():
        """
        Get trading limitations for current account type.

        Returns:
            200: Trading limitations info
            500: Server error
        """
        current_app.logger.info("📋 [Limitations] GET trading limitations request")

        try:
            exchange_service = get_shared_exchange_service()
            if not exchange_service:
                current_app.logger.warning(
                    "⚠️ [Limitations] No exchange service available"
                )
                # Return safe defaults on error
                return (
                    jsonify(
                        {
                            "is_paper_trading": False,
                            "margin_trading_available": True,
                            "supported_order_types": ["spot", "margin"],
                            "limitations": [],
                        }
                    ),
                    200,
                )

            limitations = exchange_service.get_trading_limitations()

            current_app.logger.info(
                f"✅ [Limitations] Retrieved limitations: {limitations['is_paper_trading']}"
            )
            return jsonify(limitations), 200

        except Exception as e:
            current_app.logger.error(f"❌ [Limitations] Unexpected error: {e}")
            # Return safe defaults on error
            return (
                jsonify(
                    {
                        "is_paper_trading": False,
                        "margin_trading_available": True,
                        "supported_order_types": ["spot", "margin"],
                        "limitations": [],
                    }
                ),
                200,
            )
