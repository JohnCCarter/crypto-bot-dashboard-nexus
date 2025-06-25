"""Order management API endpoints med real Bitfinex integration via authenticated WebSocket."""

import os
import time
import logging
from typing import Optional

from flask import current_app, jsonify, request

from backend.services.validation import validate_order_data
from backend.services.exchange import ExchangeService, ExchangeError
from backend.services.authenticated_websocket_service import get_authenticated_websocket_client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available in all environments
    pass

logger = logging.getLogger(__name__)

def get_live_order_service():
    """Get order service från Bitfinex API (stöder paper trading)."""
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    
    # Kolla om vi har placeholder-nycklar
    has_placeholder_keys = (not api_key or not api_secret or 
                          api_key.startswith("your_") or api_secret.startswith("your_") or
                          "placeholder" in api_key or "placeholder" in api_secret)
    
    if has_placeholder_keys:
        logger.info("🔧 [Orders] No real API keys - order service disabled")
        return None
    
    try:
        # Create ExchangeService för Bitfinex Paper Trading
        is_paper_trading = os.getenv("PAPER_TRADING", "false").lower() == "true"
        
        if is_paper_trading:
            logger.info("📄 [Orders] Creating Paper Trading order service")
        else:
            logger.info("💰 [Orders] Creating LIVE Trading order service")
            
        exchange_service = ExchangeService(
            exchange_id="bitfinex", 
            api_key=api_key, 
            api_secret=api_secret
        )
        
        # Note: ccxt kommer automatiskt använda sandbox om API keys är från paper trading account
        return exchange_service
    except Exception as e:
        logger.error(f"❌ [Orders] Failed to create order service: {e}")
        return None


def register(app):
    """Register order endpoints."""
    
    @app.route("/api/orders", methods=["GET"])
    def get_orders():
        """
        Hämta open orders från Bitfinex via authenticated WebSocket (första prioritet)
        eller REST API som fallback.
        
        Returns:
            200: List of open orders från Bitfinex
            500: Server error
        """
        logger.info("📋 [Orders] GET open orders request")
        
        try:
            # Försök hämta från authenticated WebSocket först
            ws_client = get_authenticated_websocket_client()
            if ws_client and ws_client.authenticated:
                logger.info("📋 [WS] Fetching orders from authenticated WebSocket...")
                
                orders = ws_client.get_orders()
                if orders is not None:  # orders kan vara tom lista []
                    # Konvertera WebSocket order format till vårt API format
                    formatted_orders = []
                    
                    for order in orders:
                        # Filtrera endast aktiva orders
                        if order.get("status") in ["ACTIVE", "PARTIALLY FILLED"]:
                            formatted_order = {
                                "id": str(order.get("id", "")),
                                "symbol": order.get("symbol", ""),
                                "type": order.get("type", "").lower(),
                                "side": "buy" if order.get("amount", 0) > 0 else "sell",
                                "amount": abs(order.get("amount", 0.0)),
                                "price": order.get("price", 0.0),
                                "status": order.get("status", "").lower(),
                                "timestamp": order.get("mts_create", int(time.time() * 1000)),
                                "remaining": abs(order.get("amount", 0.0)),  # amount_remaining inte alltid tillgängligt
                                "filled": abs(order.get("amount_orig", 0.0)) - abs(order.get("amount", 0.0)),
                                "fee": 0.0,  # Fees beräknas vid execution
                                "average": order.get("price_avg", 0.0)
                            }
                            formatted_orders.append(formatted_order)
                    
                    logger.info(f"✅ [WS] Retrieved {len(formatted_orders)} open orders")
                    return jsonify({"orders": formatted_orders}), 200
                
                else:
                    logger.info("✅ [WS] WebSocket authenticated - no open orders")
                    return jsonify({"orders": []}), 200
                    
            # Fallback till ExchangeService
            exchange_service = get_live_order_service()
            if not exchange_service:
                logger.warning("⚠️ [Orders] No exchange service available")
                return jsonify({"orders": []}), 200
            
            logger.info("📋 [REST] Falling back to REST API for orders...")
            open_orders = exchange_service.fetch_open_orders()
            
            logger.info(f"✅ [REST] Retrieved {len(open_orders)} open orders")
            return jsonify({"orders": open_orders}), 200
            
        except ExchangeError as e:
            logger.error(f"❌ [Orders] Exchange error: {e}")
            return jsonify({"orders": []}), 200  # Empty rather than error
        except Exception as e:
            logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({"error": "Failed to fetch orders"}), 500

    @app.route("/api/orders", methods=["POST"])
    def place_order():
        """
        Placera ny order på Bitfinex.
        
        Request body:
            {
                "symbol": str,          # Trading pair (e.g. "BTC/USD")
                "order_type": str,      # "market" or "limit"
                "side": str,            # "buy" or "sell"
                "amount": float,        # Order size
                "price": float,         # Required för limit orders
                "leverage": float,      # Optional leverage
                "stop_loss": float,     # Optional stop loss
                "take_profit": float    # Optional take profit
            }
        
        Returns:
            201: Order placed successfully
            400: Invalid input data
            500: Server error
        """
        logger.info("📋 [Orders] POST order request")
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing JSON body"}), 400

            # Validate order data
            validation_result = validate_order_data(data)
            if not validation_result["valid"]:
                return jsonify({
                    "error": "Invalid order data",
                    "details": validation_result["errors"]
                }), 400

            exchange_service = get_live_order_service()
            if not exchange_service:
                logger.error("❌ [Orders] Cannot place order - no exchange service")
                return jsonify({
                    "error": "Order service not available",
                    "details": "Bitfinex API keys not configured"
                }), 503

            # Placera order på Bitfinex
            order = exchange_service.create_order(
                symbol=data["symbol"],
                order_type=data["order_type"],
                side=data["side"],
                amount=float(data["amount"]),
                price=float(data.get("price", 0))
            )
            
            logger.info(f"✅ [Orders] Order placed: {order['id']}")
            
            return jsonify({
                "message": "Order placed successfully",
                "order": order
            }), 201
            
        except ExchangeError as e:
            logger.error(f"❌ [Orders] Exchange error: {e}")
            return jsonify({
                "error": "Failed to place order",
                "details": str(e)
            }), 400
        except Exception as e:
            logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({
                "error": "Failed to place order",
                "details": str(e)
            }), 500

    @app.route("/api/orders/<order_id>", methods=["DELETE"])
    def cancel_order(order_id: str):
        """
        Cancel order på Bitfinex.
        
        Args:
            order_id: Bitfinex order ID
            
        Returns:
            200: Order cancelled successfully  
            404: Order not found
            500: Server error
        """
        logger.info(f"📋 [Orders] DELETE order: {order_id}")
        
        try:
            exchange_service = get_live_order_service()
            if not exchange_service:
                return jsonify({
                    "error": "Order service not available"
                }), 503

            # Cancel order på Bitfinex
            result = exchange_service.cancel_order(order_id)
            
            logger.info(f"✅ [Orders] Order cancelled: {order_id}")
            
            return jsonify({
                "message": f"Order {order_id} cancelled successfully",
                "order": result
            }), 200
            
        except ExchangeError as e:
            if "not found" in str(e).lower():
                return jsonify({"error": "Order not found"}), 404
            logger.error(f"❌ [Orders] Cancel error: {e}")
            return jsonify({
                "error": "Failed to cancel order",
                "details": str(e)
            }), 400
        except Exception as e:
            logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({
                "error": "Failed to cancel order"
            }), 500

    @app.route("/api/orders/history", methods=["GET"])
    def get_order_history():
        """
        Hämta order history från Bitfinex via authenticated WebSocket (första prioritet)
        eller REST API som fallback.
        
        Query parameters:
            symbol: Optional filter by trading pair
            limit: Maximum orders to return (default 50)
            
        Returns:
            200: List of historical orders från Bitfinex
            500: Server error
        """
        logger.info("📋 [Orders] GET order history request")
        
        try:
            # Försök hämta från authenticated WebSocket först
            ws_client = get_authenticated_websocket_client()
            if ws_client and ws_client.authenticated:
                logger.info("📋 [WS] Fetching order history from authenticated WebSocket...")
                
                trade_history = ws_client.get_trade_history()
                if trade_history is not None:  # trade_history kan vara tom lista []
                    # Konvertera WebSocket trade format till order history format
                    symbol_filter = request.args.get("symbol")
                    limit = int(request.args.get("limit", 50))
                    
                    formatted_history = []
                    for trade in trade_history[-limit:]:  # Senaste trades först
                        # Filtrera på symbol om angivet
                        if symbol_filter and trade.get("symbol") != symbol_filter:
                            continue
                            
                        formatted_trade = {
                            "id": str(trade.get("id", "")),
                            "symbol": trade.get("symbol", ""),
                            "type": trade.get("order_type", "").lower(),
                            "side": "buy" if trade.get("exec_amount", 0) > 0 else "sell",
                            "amount": abs(trade.get("exec_amount", 0.0)),
                            "price": trade.get("exec_price", 0.0),
                            "status": "filled",  # Trades är alltid filled
                            "timestamp": trade.get("mts_create", int(time.time() * 1000)),
                            "fee": abs(trade.get("fee", 0.0)),
                            "fee_currency": trade.get("fee_currency", "USD")
                        }
                        formatted_history.append(formatted_trade)
                    
                    logger.info(f"✅ [WS] Retrieved {len(formatted_history)} trade history entries")
                    return jsonify(formatted_history), 200
                
                else:
                    logger.info("✅ [WS] WebSocket authenticated - no trade history")
                    return jsonify([]), 200
                    
            # Fallback till ExchangeService
            exchange_service = get_live_order_service()
            if not exchange_service:
                logger.warning("⚠️ [Orders] No exchange service for history")
                return jsonify([]), 200
            
            logger.info("📋 [REST] Falling back to REST API for order history...")
            
            # Get query parameters
            symbol = request.args.get("symbol")
            limit = int(request.args.get("limit", 50))
            
            # Fetch order history från Bitfinex
            symbols = [symbol] if symbol else None
            order_history = exchange_service.fetch_order_history(
                symbols=symbols, 
                limit=limit
            )
            
            logger.info(f"✅ [REST] Retrieved {len(order_history)} historical orders")
            return jsonify(order_history), 200
            
        except ExchangeError as e:
            logger.error(f"❌ [Orders] Exchange error: {e}")
            # Return empty array rather than error for history
            return jsonify([]), 200  
        except Exception as e:
            logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({
                "error": "Failed to fetch order history"
            }), 500

    @app.route("/api/orders/<order_id>", methods=["GET"])
    def get_order_status(order_id: str):
        """
        Hämta order status från Bitfinex.
        
        Args:
            order_id: Bitfinex order ID
            
        Returns:
            200: Order details
            404: Order not found
            500: Server error
        """
        logger.info(f"📋 [Orders] GET order status: {order_id}")
        
        try:
            exchange_service = get_live_order_service()
            if not exchange_service:
                return jsonify({
                    "error": "Order service not available"
                }), 503

            # Fetch order status från Bitfinex
            order = exchange_service.fetch_order(order_id)
            
            logger.info(f"✅ [Orders] Order status retrieved: {order_id}")
            
            return jsonify(order), 200
            
        except ExchangeError as e:
            if "not found" in str(e).lower():
                return jsonify({"error": "Order not found"}), 404
            logger.error(f"❌ [Orders] Exchange error: {e}")
            return jsonify({
                "error": "Failed to fetch order status"
            }), 400
        except Exception as e:
            logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({
                "error": "Failed to fetch order status"
            }), 500
