"""
WebSocket Integration Routes - Ersätter public market data med authenticated WebSocket.
Använder endast riktiga Bitfinex API-nycklar för alla marknadsdata.
"""

import asyncio
import logging
from flask import Blueprint, jsonify, request, current_app
from backend.services.authenticated_websocket_service import (
    start_authenticated_websocket_service,
    get_authenticated_websocket_client,
    stop_authenticated_websocket_service
)

# Skapa Blueprint
websocket_bp = Blueprint('websocket', __name__)

# Globala variabler för cached data
cached_market_data = {}
authenticated_ws_client = None

logger = logging.getLogger(__name__)

def register(app):
    """Registrera WebSocket routes som ersätter public market data."""
    
    @app.route("/api/ws/start", methods=["POST"])
    def start_websocket_service():
        """Starta authenticated WebSocket service."""
        try:
            # Detta körs i async context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            client = loop.run_until_complete(start_authenticated_websocket_service())
            
            return jsonify({
                "status": "success",
                "message": "Authenticated WebSocket service started",
                "authenticated": client.authenticated if client else False
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ Failed to start WebSocket service: {e}")
            return jsonify({
                "status": "error", 
                "message": str(e)
            }), 500

    @app.route("/api/ws/status", methods=["GET"])
    def get_websocket_service_status():
        """Hämta status för authenticated WebSocket service."""
        try:
            client = get_authenticated_websocket_client()
            
            if client:
                return jsonify({
                    "status": "running",
                    "authenticated": client.authenticated,
                    "running": client.running,
                    "subscriptions": len(client.subscriptions),
                    "callbacks": len(client.callbacks)
                }), 200
            else:
                return jsonify({
                    "status": "stopped",
                    "authenticated": False,
                    "running": False
                }), 200
                
        except Exception as e:
            current_app.logger.error(f"❌ WebSocket status error: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @app.route("/api/market/ws/ticker/<symbol>", methods=["GET"])
    def get_websocket_ticker(symbol):
        """
        Hämta live ticker via authenticated WebSocket - ERSÄTTER public API.
        Endast för användare med riktiga API-nycklar.
        """
        current_app.logger.info(f"💰 [WebSocket] Authenticated ticker request for {symbol}")
        
        try:
            client = get_authenticated_websocket_client()
            if not client or not client.authenticated:
                return jsonify({
                    "error": "Authenticated WebSocket not available",
                    "message": "Requires valid Bitfinex API keys"
                }), 503
            
            # Hämta cached data eller subscribe
            cache_key = f"ticker_{symbol}"
            if cache_key in cached_market_data:
                ticker_data = cached_market_data[cache_key]
                
                return jsonify({
                    "symbol": symbol,
                    "last": ticker_data.price,
                    "bid": ticker_data.bid,
                    "ask": ticker_data.ask,
                    "volume": ticker_data.volume,
                    "timestamp": ticker_data.timestamp.isoformat(),
                    "source": "authenticated_websocket"
                }), 200
            else:
                # Subscribe och returnera placeholder
                def ticker_callback(data):
                    cached_market_data[f"ticker_{data.symbol}"] = data
                
                # Detta behöver köras async
                asyncio.create_task(client.subscribe_to_ticker(symbol, ticker_callback))
                
                return jsonify({
                    "message": "Subscribing to authenticated ticker data",
                    "symbol": symbol,
                    "status": "pending"
                }), 202
                
        except Exception as e:
            current_app.logger.error(f"❌ [WebSocket] Authenticated ticker error: {e}")
            return jsonify({
                "error": "Failed to get authenticated ticker",
                "message": str(e)
            }), 500

    @app.route("/api/market/ws/orderbook/<symbol>", methods=["GET"])
    def get_websocket_orderbook(symbol):
        """
        Hämta live orderbook via authenticated WebSocket - ERSÄTTER public API.
        """
        current_app.logger.info(f"📚 [WebSocket] Authenticated orderbook request for {symbol}")
        
        try:
            client = get_authenticated_websocket_client()
            if not client or not client.authenticated:
                return jsonify({
                    "error": "Authenticated WebSocket not available", 
                    "message": "Requires valid Bitfinex API keys"
                }), 503
            
            limit = int(request.args.get('limit', 25))
            precision = request.args.get('precision', 'P0')
            
            # Hämta cached orderbook
            cache_key = f"orderbook_{symbol}"
            if cache_key in cached_market_data:
                orderbook_data = cached_market_data[cache_key]
                
                return jsonify({
                    "symbol": symbol,
                    "bids": orderbook_data.get('bids', [])[:limit],
                    "asks": orderbook_data.get('asks', [])[:limit], 
                    "timestamp": orderbook_data.get('timestamp'),
                    "source": "authenticated_websocket"
                }), 200
            else:
                # Subscribe till orderbook
                def orderbook_callback(data):
                    cached_market_data[f"orderbook_{data['symbol']}"] = data
                
                asyncio.create_task(client.subscribe_to_orderbook(symbol, orderbook_callback, precision))
                
                return jsonify({
                    "message": "Subscribing to authenticated orderbook",
                    "symbol": symbol,
                    "status": "pending"
                }), 202
                
        except Exception as e:
            current_app.logger.error(f"❌ [WebSocket] Authenticated orderbook error: {e}")
            return jsonify({
                "error": "Failed to get authenticated orderbook",
                "message": str(e)
            }), 500

    @app.route("/api/market/ws/candles/<symbol>", methods=["GET"])
    def get_websocket_candles(symbol):
        """
        Hämta live OHLCV candles via authenticated WebSocket - ERSÄTTER public API.
        """
        current_app.logger.info(f"🕯️ [WebSocket] Authenticated candles request for {symbol}")
        
        try:
            client = get_authenticated_websocket_client()
            if not client or not client.authenticated:
                return jsonify({
                    "error": "Authenticated WebSocket not available",
                    "message": "Requires valid Bitfinex API keys"
                }), 503
            
            timeframe = request.args.get('timeframe', '5m')
            limit = int(request.args.get('limit', 100))
            
            # Validera timeframe
            valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '3h', '6h', '12h', '1D', '7D', '14D', '1M']
            if timeframe not in valid_timeframes:
                return jsonify({
                    "error": "Invalid timeframe",
                    "message": f"Must be one of: {valid_timeframes}"
                }), 400
            
            # Hämta cached candles
            cache_key = f"candles_{symbol}_{timeframe}"
            if cache_key in cached_market_data:
                candle_data = cached_market_data[cache_key]
                
                # Konvertera till OHLCV format
                ohlcv = []
                if 'data' in candle_data and isinstance(candle_data['data'], list):
                    for candle in candle_data['data'][-limit:]:
                        if len(candle) >= 6:
                            ohlcv.append({
                                'timestamp': candle[0],
                                'open': candle[1], 
                                'close': candle[2],
                                'high': candle[3],
                                'low': candle[4],
                                'volume': candle[5]
                            })
                
                return jsonify({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "data": ohlcv,
                    "source": "authenticated_websocket"
                }), 200
            else:
                # Subscribe till candles
                def candle_callback(data):
                    cached_market_data[f"candles_{data['symbol']}_{data['timeframe']}"] = data
                
                asyncio.create_task(client.subscribe_to_candles(symbol, timeframe, candle_callback))
                
                return jsonify({
                    "message": "Subscribing to authenticated candle data",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "status": "pending"
                }), 202
                
        except Exception as e:
            current_app.logger.error(f"❌ [WebSocket] Authenticated candles error: {e}")
            return jsonify({
                "error": "Failed to get authenticated candles",
                "message": str(e)
            }), 500

    @app.route("/api/orders/ws", methods=["POST"])
    def place_websocket_order():
        """
        Placera order via authenticated WebSocket - ERSÄTTER REST order API.
        """
        current_app.logger.info("📋 [WebSocket] Authenticated order placement")
        
        try:
            client = get_authenticated_websocket_client()
            if not client or not client.authenticated:
                return jsonify({
                    "error": "Authenticated WebSocket not available",
                    "message": "Requires valid Bitfinex API keys"
                }), 503
            
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing JSON body"}), 400
            
            # Validera order data
            required_fields = ['symbol', 'order_type', 'side', 'amount']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        "error": f"Missing required field: {field}"
                    }), 400
            
            symbol = data['symbol']
            order_type = data['order_type'].upper()
            amount = float(data['amount'])
            
            # Justera amount för sell orders
            if data['side'].lower() == 'sell':
                amount = -amount
            
            price = float(data.get('price', 0)) if data.get('price') else None
            
            # Placera order via WebSocket
            cid = asyncio.create_task(client.new_order(order_type, symbol, amount, price))
            
            return jsonify({
                "message": "Order placed via authenticated WebSocket",
                "client_id": cid,
                "symbol": symbol,
                "type": order_type,
                "amount": amount,
                "price": price,
                "source": "authenticated_websocket"
            }), 201
            
        except Exception as e:
            current_app.logger.error(f"❌ [WebSocket] Authenticated order error: {e}")
            return jsonify({
                "error": "Failed to place authenticated order",
                "message": str(e)
            }), 500

    @app.route("/api/orders/ws/<int:order_id>", methods=["DELETE"])
    def cancel_websocket_order(order_id: int):
        """
        Avbryt order via authenticated WebSocket - ERSÄTTER REST cancel API.
        """
        current_app.logger.info(f"❌ [WebSocket] Authenticated order cancellation: {order_id}")
        
        try:
            client = get_authenticated_websocket_client()
            if not client or not client.authenticated:
                return jsonify({
                    "error": "Authenticated WebSocket not available",
                    "message": "Requires valid Bitfinex API keys"
                }), 503
            
            # Avbryt order via WebSocket
            asyncio.create_task(client.cancel_order(order_id))
            
            return jsonify({
                "message": f"Order {order_id} cancelled via authenticated WebSocket",
                "order_id": order_id,
                "source": "authenticated_websocket"
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ [WebSocket] Cancel order error: {e}")
            return jsonify({
                "error": "Failed to cancel order via WebSocket",
                "message": str(e)
            }), 500

    @app.route("/api/ws/calculations", methods=["POST"])
    def request_calculations():
        """
        Begär specifika beräkningar via authenticated WebSocket.
        Använder Bitfinex calc() funktionalitet.
        """
        current_app.logger.info("🧮 [WebSocket] Authenticated calculations request")
        
        try:
            client = get_authenticated_websocket_client()
            if not client or not client.authenticated:
                return jsonify({
                    "error": "Authenticated WebSocket not available",
                    "message": "Requires valid Bitfinex API keys"
                }), 503
            
            data = request.get_json()
            if not data or 'calculations' not in data:
                return jsonify({
                    "error": "Missing calculations field",
                    "example": ["margin_sym_tBTCUSD", "wallet_exchange_USD"]
                }), 400
            
            calculations = data['calculations']
            if not isinstance(calculations, list):
                return jsonify({
                    "error": "Calculations must be a list"
                }), 400
            
            # Begär beräkningar
            asyncio.create_task(client.calc(calculations))
            
            return jsonify({
                "message": "Calculations requested via authenticated WebSocket",
                "calculations": calculations,
                "note": "Results will be received via authenticated channel"
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ [WebSocket] Calculations error: {e}")
            return jsonify({
                "error": "Failed to request calculations",
                "message": str(e)
            }), 500