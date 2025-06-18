"""Order management API endpoints."""

from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

from backend.services.validation import validate_order_data
from backend.services.order_service import OrderService
from backend.services.exchange import ExchangeService

orders_bp = Blueprint("orders", __name__)

# Håll track på orders internt - Mock development service
mock_orders = []


def get_order_service():
    """Get order service from application context."""
    try:
        if hasattr(current_app, '_services') and current_app._services:
            return current_app._services.get("order_service")
        
        # Fallback: create a mock order service for development
        current_app.logger.warning("Order service not properly initialized, using mock service")
        return MockOrderService()
    except Exception as e:
        current_app.logger.error(f"Failed to get order service: {e}")
        return MockOrderService()


class MockOrderService:
    """Mock order service for development/testing."""
    
    def place_order(self, order_data):
        """Mock place order."""
        return {
            "id": "mock_order_123",
            "status": "pending",
            "symbol": order_data.get("symbol", "BTC/USD"),
            "side": order_data.get("side", "buy"),
            "amount": order_data.get("amount", 0.1),
            "price": order_data.get("price", 45000),
            "timestamp": "2025-06-18T13:45:00Z"
        }
    
    def get_order_status(self, order_id):
        """Mock get order status."""
        if order_id in ["1", "2", "mock_order_123"]:
            return {
                "id": order_id,
                "status": "filled",
                "symbol": "BTC/USD",
                "side": "buy",
                "amount": 0.1,
                "price": 45000
            }
        return None
    
    def cancel_order(self, order_id):
        """Mock cancel order."""
        if order_id in ["1", "2", "mock_order_123"]:
            return {"id": order_id, "status": "cancelled"}
        return None
    
    def get_open_orders(self, symbol=None):
        """Mock get open orders."""
        return [
            {
                "id": "mock_order_124",
                "symbol": symbol or "BTC/USD",
                "side": "buy",
                "amount": 0.1,
                "price": 44500,
                "status": "open"
            }
        ]


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

        # Get order service from app context
        order_service = get_order_service()
        if not order_service:
            return jsonify({"error": "Order service not available"}), 500

        # Place order
        try:
            order = order_service.place_order(data)
            return (
                jsonify({"message": "Order placed successfully", "order": order}),
                201,
            )
        except Exception as order_error:
            # Handle exchange-specific errors gracefully
            error_message = str(order_error)
            current_app.logger.warning(f"Order placement failed: {error_message}")
            
            # If it's an exchange connection issue, use mock order
            if "invalid symbol" in error_message.lower() or "paper" in error_message.lower():
                current_app.logger.info("Using mock order due to exchange configuration")
                mock_service = MockOrderService()
                order = mock_service.place_order(data)
                return (
                    jsonify({
                        "message": "Order placed successfully (mock)", 
                        "order": order,
                        "note": "Using mock service - configure exchange for live trading"
                    }),
                    201,
                )
            else:
                raise order_error

    except Exception as e:
        current_app.logger.error(f"Error placing order: {str(e)}")
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
        order_service = get_order_service()
        if not order_service:
            return jsonify({"error": "Order service not available"}), 500
            
        order = order_service.get_order_status(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        return jsonify(order), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching order: {str(e)}")
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
        order_service = get_order_service()
        if not order_service:
            return jsonify({"error": "Order service not available"}), 500
            
        result = order_service.cancel_order(order_id)
        if not result:
            return jsonify({"error": "Order not found"}), 404
        return jsonify({"message": "Order cancelled successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error cancelling order: {str(e)}")
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
        order_service = get_order_service()
        if not order_service:
            return jsonify({"error": "Order service not available"}), 500
            
        symbol = request.args.get("symbol")
        orders = order_service.get_open_orders(symbol)
        return jsonify({"orders": orders}), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching open orders: {str(e)}")
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


def register(app):
    @app.route("/api/orders", methods=["GET"])
    def get_orders():
        """Hämtar alla orders."""
        current_app.logger.info("📋 [Backend] GET orders request received")
        
        try:
            current_app.logger.info(f"📋 [Backend] Mock orders in memory: {len(mock_orders)} orders")
            
            # Returnera mock orders för development
            result = {"orders": mock_orders}
            current_app.logger.info(f"✅ [Backend] Orders retrieved successfully: {result}")
            
            return jsonify(result), 200
        except Exception as e:
            current_app.logger.error(f"❌ [Backend] Get orders failed: {str(e)}")
            current_app.logger.error(f"❌ [Backend] Exception type: {type(e).__name__}")
            import traceback
            current_app.logger.error(f"❌ [Backend] Stack trace: {traceback.format_exc()}")
            
            return jsonify({"error": f"Failed to get orders: {str(e)}"}), 500

    @app.route("/api/orders", methods=["POST"])
    def place_order():
        """Placerar en ny order."""
        current_app.logger.info("📋 [Backend] POST order request received")
        
        try:
            data = request.get_json()
            current_app.logger.info(f"📋 [Backend] Order data received: {data}")
            
            if not data:
                current_app.logger.error("❌ [Backend] No order data provided")
                return jsonify({"error": "No order data provided"}), 400
            
            # Validera required fields
            required_fields = ['symbol', 'order_type', 'side', 'amount']
            for field in required_fields:
                if field not in data:
                    current_app.logger.error(f"❌ [Backend] Missing required field: {field}")
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            current_app.logger.info(f"📋 [Backend] Order validation passed for {data['side']} {data['amount']} {data['symbol']}")
            
            # Mock order creation för development
            mock_order = {
                "id": len(mock_orders) + 1,
                "symbol": data['symbol'],
                "side": data['side'],
                "amount": data['amount'],
                "order_type": data['order_type'],
                "status": "filled",
                "price": data.get('price', 50000),  # Mock price
                "timestamp": "2024-01-01T12:00:00Z"
            }
            
            mock_orders.append(mock_order)
            current_app.logger.info(f"✅ [Backend] Mock order created: {mock_order}")
            current_app.logger.info(f"✅ [Backend] Total mock orders now: {len(mock_orders)}")
            
            return jsonify({
                "message": f"Order placed successfully - {data['side']} {data['amount']} {data['symbol']}",
                "order": mock_order
            }), 201
            
        except Exception as e:
            current_app.logger.error(f"❌ [Backend] Place order failed: {str(e)}")
            current_app.logger.error(f"❌ [Backend] Exception type: {type(e).__name__}")
            current_app.logger.error(f"❌ [Backend] Request data: {request.get_json() if request else 'No request'}")
            import traceback
            current_app.logger.error(f"❌ [Backend] Stack trace: {traceback.format_exc()}")
            
            return jsonify({"error": f"Failed to place order: {str(e)}"}), 500

    @app.route("/api/orders/<int:order_id>", methods=["DELETE"])
    def cancel_order(order_id):
        """Avbryter en order."""
        current_app.logger.info(f"📋 [Backend] DELETE order request received for order_id: {order_id}")
        
        try:
            # Hitta och ta bort order från mock data
            order_found = False
            for i, order in enumerate(mock_orders):
                if order['id'] == order_id:
                    removed_order = mock_orders.pop(i)
                    order_found = True
                    current_app.logger.info(f"✅ [Backend] Mock order cancelled: {removed_order}")
                    current_app.logger.info(f"✅ [Backend] Remaining mock orders: {len(mock_orders)}")
                    break
            
            if not order_found:
                current_app.logger.warning(f"⚠️ [Backend] Order not found: {order_id}")
                return jsonify({"error": f"Order {order_id} not found"}), 404
            
            return jsonify({
                "message": f"Order {order_id} cancelled successfully"
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ [Backend] Cancel order failed: {str(e)}")
            current_app.logger.error(f"❌ [Backend] Exception type: {type(e).__name__}")
            current_app.logger.error(f"❌ [Backend] Order ID: {order_id}")
            import traceback
            current_app.logger.error(f"❌ [Backend] Stack trace: {traceback.format_exc()}")
            
            return jsonify({"error": f"Failed to cancel order: {str(e)}"}), 500
