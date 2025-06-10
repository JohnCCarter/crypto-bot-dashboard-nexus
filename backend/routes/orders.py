"""Order management API endpoints."""

from typing import Any, Dict

from flask import Blueprint, jsonify, request

from backend.services.exchange import ExchangeService
from backend.services.order_service import OrderService
from backend.services.validation import validate_order_data

# Skapa en ExchangeService-instans (dummy-nycklar för test)
exchange_service = ExchangeService(exchange_id="binance", api_key="", api_secret="")
order_service = OrderService(exchange_service)

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/api/orders", methods=["POST"])
def place_order_route():
    """
    Create and log a new order.

    Request body:
        {
            "symbol": str,          # Trading pair (e.g. "BTC/USD")
            "order_type": str,      # "market" or "limit"
            "side": str,            # "buy" or "sell"
            "amount": float,        # Order size
            "price": float,         # Required for limit orders
            "leverage": float,      # Optional leverage for margin trading
            "stop_loss": float,     # Optional stop loss price
            "take_profit": float    # Optional take profit price
        }

    Returns:
        201: Order created successfully
        400: Invalid input data
        500: Server error
    """
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

        # Place order
        order = order_service.place_order(data)
        return (
            jsonify({"message": "Order placed successfully", "order": order}),
            201,
        )

    except Exception as e:
        orders_bp.logger.error(f"Error placing order: {str(e)}")
        return jsonify({"error": "Failed to place order", "details": str(e)}), 500


@orders_bp.route("/api/orders/<order_id>", methods=["GET"])
def get_order_route(order_id: str):
    """
    Get order status by ID.

    Args:
        order_id: Unique order identifier

    Returns:
        200: Order details
        404: Order not found
        500: Server error
    """
    try:
        order = order_service.get_order_status(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        return jsonify(order), 200
    except Exception as e:
        orders_bp.logger.error(f"Error fetching order: {str(e)}")
        return jsonify({"error": "Failed to fetch order"}), 500


@orders_bp.route("/api/orders/<order_id>", methods=["DELETE"])
def cancel_order_route(order_id: str):
    """
    Cancel an existing order.

    Args:
        order_id: Unique order identifier

    Returns:
        200: Order cancelled successfully
        404: Order not found
        500: Server error
    """
    try:
        result = order_service.cancel_order(order_id)
        if not result:
            return jsonify({"error": "Order not found"}), 404
        return jsonify({"message": "Order cancelled successfully"}), 200
    except Exception as e:
        orders_bp.logger.error(f"Error cancelling order: {str(e)}")
        return jsonify({"error": "Failed to cancel order"}), 500


@orders_bp.route("/api/orders", methods=["GET"])
def get_open_orders_route():
    """
    Get all open orders.

    Query parameters:
        symbol: Optional filter by trading pair

    Returns:
        200: List of open orders
        500: Server error
    """
    try:
        symbol = request.args.get("symbol")
        orders = order_service.get_open_orders(symbol)
        return jsonify({"orders": orders}), 200
    except Exception as e:
        orders_bp.logger.error(f"Error fetching open orders: {str(e)}")
        return jsonify({"error": "Failed to fetch open orders"}), 500


@orders_bp.route("/api/orders/history", methods=["GET"])
def get_order_history():
    """
    Returnerar mockad orderhistorik.
    """
    mock_orders = [
        {
            "id": "1",
            "symbol": "BTC/USD",
            "order_type": "limit",
            "side": "buy",
            "amount": 0.1,
            "price": 27000,
            "fee": 1.5,
            "status": "filled"
        },
        {
            "id": "2",
            "symbol": "ETH/USD",
            "order_type": "market",
            "side": "sell",
            "amount": 2.0,
            "price": 1800,
            "fee": 0.8,
            "status": "pending"
        }
    ]
    return jsonify(mock_orders), 200
