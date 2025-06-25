"""Order management API endpoints med KORREKT Bitfinex WebSocket integration."""

import os
import time
import logging
import asyncio
from typing import Optional

from flask import current_app, jsonify, request

from backend.services.validation import validate_order_data
from backend.services.authenticated_websocket_service import get_authenticated_websocket_client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available in all environments
    pass


def get_authenticated_client():
    """Hämta authenticated WebSocket klient för KORREKT Bitfinex integration."""
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    
    # Kolla om vi har placeholder-nycklar
    has_placeholder_keys = (not api_key or not api_secret or 
                          api_key.startswith("your_") or api_secret.startswith("your_") or
                          "placeholder" in api_key or "placeholder" in api_secret)
    
    if has_placeholder_keys:
        current_app.logger.info("🔧 [Orders] No real API keys - order service disabled")
        return None
    
    try:
        # Hämta authenticated WebSocket klient
        client = get_authenticated_websocket_client()
        
        if client and client.authenticated:
            current_app.logger.info("✅ [Orders] Authenticated WebSocket tillgänglig")
            return client
        else:
            current_app.logger.warning("⚠️ [Orders] Authenticated WebSocket inte tillgänglig")
            return None
            
    except Exception as e:
        current_app.logger.error(f"❌ [Orders] Failed to get authenticated client: {e}")
        return None


def register(app):
    """Register order endpoints med KORREKT Bitfinex integration."""
    
    @app.route("/api/orders", methods=["GET"])
    def get_orders():
        """
        Hämta open orders från Bitfinex via AUTHENTICATED WebSocket.
        
        Returns:
            200: List of open orders från Bitfinex WebSocket
            500: Server error
        """
        current_app.logger.info("📋 [Orders] GET open orders request (WebSocket)")
        
        try:
            client = get_authenticated_client()
            if not client:
                current_app.logger.warning("⚠️ [Orders] No authenticated client available")
                return jsonify({"orders": []}), 200
            
            # Hämta orders från authenticated WebSocket
            orders = client.get_orders()
            
            current_app.logger.info(f"✅ [Orders] Retrieved {len(orders)} open orders via WebSocket")
            
            # Konvertera till förväntad format
            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    "id": str(order["id"]),
                    "symbol": order["symbol"],
                    "type": order["type"],
                    "side": "buy" if float(order["amount"]) > 0 else "sell",
                    "amount": abs(float(order["amount"])),
                    "price": float(order["price"]),
                    "status": order["status"],
                    "timestamp": order["created"]
                })
            
            return jsonify({"orders": formatted_orders}), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] Unexpected error: {e}")
            return jsonify({"error": "Failed to fetch orders"}), 500

    @app.route("/api/orders", methods=["POST"])
    def place_order():
        """
        Placera ny order på Bitfinex via AUTHENTICATED WebSocket.
        
        Request body:
            {
                "symbol": str,          # Trading pair (e.g. "TESTBTC/TESTUSD")
                "order_type": str,      # "market" eller "limit"
                "side": str,            # "buy" eller "sell"
                "amount": float,        # Order size
                "price": float,         # Required for limit orders
            }
        
        Returns:
            201: Order placed successfully
            400: Invalid input data
            500: Server error
        """
        current_app.logger.info("📋 [Orders] POST order request (WebSocket)")
        
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

            client = get_authenticated_client()
            if not client:
                current_app.logger.error("❌ [Orders] Cannot place order - no authenticated client")
                return jsonify({
                    "error": "Order service not available",
                    "details": "Bitfinex WebSocket not authenticated"
                }), 503

            # Konvertera paper trading symbol till Bitfinex format
            symbol = data["symbol"]
            if symbol.startswith("TEST"):
                # TESTBTC/TESTUSD → tBTCUSD
                if symbol == "TESTBTC/TESTUSD":
                    symbol = "tBTCUSD"
                elif symbol == "TESTETH/TESTUSD":
                    symbol = "tETHUSD"
                elif symbol == "TESTLTC/TESTUSD":
                    symbol = "tLTCUSD"
            
            # Konvertera amount baserat på side
            amount = float(data["amount"])
            if data["side"] == "sell":
                amount = -amount  # Bitfinex använder negativa värden för sell
                
            price = float(data.get("price", 0)) if data.get("price") else None

            # Placera order via authenticated WebSocket
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            order_id = loop.run_until_complete(
                client.new_order(
                    order_type=data["order_type"].upper(),
                    symbol=symbol,
                    amount=amount,
                    price=price
                )
            )
            
            current_app.logger.info(f"✅ [Orders] Order placed via WebSocket: {order_id}")
            
            return jsonify({
                "message": "Order placed successfully via WebSocket",
                "order_id": order_id,
                "symbol": symbol,
                "amount": data["amount"],
                "price": price,
                "side": data["side"]
            }), 201
            
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] WebSocket order error: {e}")
            return jsonify({
                "error": "Failed to place order via WebSocket",
                "details": str(e)
            }), 500

    @app.route("/api/orders/<order_id>", methods=["DELETE"])
    def cancel_order(order_id: str):
        """
        Avbryt order på Bitfinex via AUTHENTICATED WebSocket.
        
        Args:
            order_id: Bitfinex order ID
            
        Returns:
            200: Order cancelled successfully  
            404: Order not found
            500: Server error
        """
        current_app.logger.info(f"📋 [Orders] DELETE order via WebSocket: {order_id}")
        
        try:
            client = get_authenticated_client()
            if not client:
                return jsonify({
                    "error": "Order service not available"
                }), 503

            # Avbryt order via authenticated WebSocket
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(client.cancel_order(int(order_id)))
            
            current_app.logger.info(f"✅ [Orders] Order cancelled via WebSocket: {order_id}")
            
            return jsonify({
                "message": f"Order {order_id} cancelled successfully via WebSocket"
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] Cancel error: {e}")
            return jsonify({
                "error": "Failed to cancel order via WebSocket",
                "details": str(e)
            }), 400

    @app.route("/api/orders/history", methods=["GET"])
    def get_order_history():
        """
        Hämta order history från Bitfinex via AUTHENTICATED WebSocket.
        
        Returns:
            200: List of historical orders
            500: Server error
        """
        current_app.logger.info("📋 [Orders] GET order history request (WebSocket)")
        
        try:
            client = get_authenticated_client()
            if not client:
                current_app.logger.warning("⚠️ [Orders] No authenticated client for history")
                return jsonify([]), 200
            
            # För nu, returnera orders från WebSocket
            # I framtiden kan vi lägga till historik-funktionalitet
            orders = client.get_orders()
            
            # Konvertera till history format
            history = []
            for order in orders:
                history.append({
                    "id": str(order["id"]),
                    "symbol": order["symbol"],
                    "order_type": order["type"].lower(),
                    "side": "buy" if float(order["amount"]) > 0 else "sell",
                    "amount": abs(float(order["amount"])),
                    "price": float(order["price"]),
                    "fee": 0.0,  # WebSocket data kanske inte har fee ännu
                    "timestamp": order["created"],
                    "status": order["status"]
                })
            
            current_app.logger.info(f"✅ [Orders] Retrieved {len(history)} historical orders via WebSocket")
            
            return jsonify(history), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] History error: {e}")
            return jsonify([]), 200

    @app.route("/api/orders/<order_id>", methods=["GET"])
    def get_order_status(order_id: str):
        """
        Hämta order status från Bitfinex via AUTHENTICATED WebSocket.
        
        Args:
            order_id: Bitfinex order ID
            
        Returns:
            200: Order details
            404: Order not found
            500: Server error
        """
        current_app.logger.info(f"📋 [Orders] GET order status via WebSocket: {order_id}")
        
        try:
            client = get_authenticated_client()
            if not client:
                return jsonify({
                    "error": "Order service not available"
                }), 503

            # Hitta order i authenticated data
            orders = client.get_orders()
            target_order = None
            
            for order in orders:
                if str(order["id"]) == order_id:
                    target_order = order
                    break
            
            if not target_order:
                return jsonify({"error": "Order not found"}), 404
            
            # Konvertera till förväntat format
            order_status = {
                "id": str(target_order["id"]),
                "symbol": target_order["symbol"],
                "type": target_order["type"],
                "side": "buy" if float(target_order["amount"]) > 0 else "sell",
                "amount": abs(float(target_order["amount"])),
                "price": float(target_order["price"]),
                "status": target_order["status"],
                "timestamp": target_order["created"]
            }
            
            current_app.logger.info(f"✅ [Orders] Order status retrieved via WebSocket: {order_id}")
            
            return jsonify(order_status), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ [Orders] Status error: {e}")
            return jsonify({
                "error": "Failed to fetch order status via WebSocket"
            }), 500
