"""Live market data API endpoints using Bitfinex."""

from flask import jsonify, request, current_app
from backend.services.exchange import ExchangeService, ExchangeError


def register(app):
    """Register live market data routes."""
    
    def get_exchange_service():
        """Get exchange service from app context."""
        try:
            if hasattr(current_app, '_services') and current_app._services:
                return current_app._services.get("exchange")
            
            current_app.logger.warning("Exchange service not available, cannot fetch live data")
            return None
        except Exception as e:
            current_app.logger.error(f"Failed to get exchange service: {e}")
            return None

    @app.route("/api/market/ohlcv/<symbol>", methods=["GET"])
    def get_live_ohlcv(symbol):
        """
        Get live OHLCV data from Bitfinex.
        
        Query parameters:
        - timeframe: '1m', '5m', '15m', '1h', '1d' (default: '5m')
        - limit: Number of candles (default: 100, max: 1000)
        """
        current_app.logger.info(f"📊 [Market] Live OHLCV request for {symbol}")
        
        try:
            exchange = get_exchange_service()
            if not exchange:
                # Fallback to mock data if exchange not available
                current_app.logger.warning("Exchange service not available, using mock data")
                return get_mock_ohlcv(symbol)
            
            timeframe = request.args.get('timeframe', '5m')
            limit = min(int(request.args.get('limit', 100)), 1000)
            
            current_app.logger.info(f"📊 [Market] Fetching {limit} {timeframe} candles for {symbol}")
            
            # Convert symbol format if needed (BTCUSD -> BTC/USD)
            if '/' not in symbol and len(symbol) >= 6:
                # Convert BTCUSD to BTC/USD format for Bitfinex
                if symbol.endswith('USD'):
                    base = symbol[:-3]
                    quote = symbol[-3:]
                    formatted_symbol = f"{base}/{quote}"
                else:
                    formatted_symbol = symbol
            else:
                formatted_symbol = symbol
            
            current_app.logger.info(f"📊 [Market] Using symbol format: {formatted_symbol}")
            
            ohlcv_data = exchange.fetch_ohlcv(formatted_symbol, timeframe, limit)
            
            current_app.logger.info(f"✅ [Market] Successfully fetched {len(ohlcv_data)} candles")
            
            return jsonify(ohlcv_data), 200
            
        except ExchangeError as e:
            current_app.logger.error(f"❌ [Market] Exchange error: {str(e)}")
            return jsonify({"error": f"Exchange error: {str(e)}"}), 503
        except Exception as e:
            current_app.logger.error(f"❌ [Market] Failed to fetch OHLCV: {str(e)}")
            import traceback
            current_app.logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
            return jsonify({"error": f"Failed to fetch OHLCV data: {str(e)}"}), 500

    @app.route("/api/market/orderbook/<symbol>", methods=["GET"])  
    def get_live_orderbook(symbol):
        """
        Get live order book from Bitfinex.
        
        Query parameters:
        - limit: Number of levels per side (default: 20, max: 100)
        """
        current_app.logger.info(f"📋 [Market] Live orderbook request for {symbol}")
        
        try:
            exchange = get_exchange_service()
            if not exchange:
                current_app.logger.warning("Exchange service not available, using mock data")
                return get_mock_orderbook(symbol)
            
            limit = min(int(request.args.get('limit', 20)), 100)
            
            # Convert symbol format if needed
            if '/' not in symbol and len(symbol) >= 6:
                if symbol.endswith('USD'):
                    base = symbol[:-3]
                    quote = symbol[-3:]
                    formatted_symbol = f"{base}/{quote}"
                else:
                    formatted_symbol = symbol
            else:
                formatted_symbol = symbol
                
            current_app.logger.info(f"📋 [Market] Fetching orderbook for {formatted_symbol}")
            
            orderbook = exchange.fetch_order_book(formatted_symbol, limit)
            
            current_app.logger.info(f"✅ [Market] Successfully fetched orderbook with {len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks")
            
            return jsonify(orderbook), 200
            
        except ExchangeError as e:
            current_app.logger.error(f"❌ [Market] Exchange error: {str(e)}")
            return jsonify({"error": f"Exchange error: {str(e)}"}), 503
        except Exception as e:
            current_app.logger.error(f"❌ [Market] Failed to fetch orderbook: {str(e)}")
            import traceback
            current_app.logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
            return jsonify({"error": f"Failed to fetch orderbook: {str(e)}"}), 500

    @app.route("/api/market/ticker/<symbol>", methods=["GET"])
    def get_live_ticker(symbol):
        """Get live ticker data from Bitfinex."""
        current_app.logger.info(f"💰 [Market] Live ticker request for {symbol}")
        
        try:
            exchange = get_exchange_service()
            if not exchange:
                current_app.logger.warning("Exchange service not available, using mock data")
                return get_mock_ticker(symbol)
            
            # Convert symbol format if needed
            if '/' not in symbol and len(symbol) >= 6:
                if symbol.endswith('USD'):
                    base = symbol[:-3]
                    quote = symbol[-3:]
                    formatted_symbol = f"{base}/{quote}"
                else:
                    formatted_symbol = symbol
            else:
                formatted_symbol = symbol
                
            current_app.logger.info(f"💰 [Market] Fetching ticker for {formatted_symbol}")
            
            ticker = exchange.fetch_ticker(formatted_symbol)
            
            current_app.logger.info(f"✅ [Market] Successfully fetched ticker: {ticker['last']}")
            
            return jsonify(ticker), 200
            
        except ExchangeError as e:
            current_app.logger.error(f"❌ [Market] Exchange error: {str(e)}")
            return jsonify({"error": f"Exchange error: {str(e)}"}), 503
        except Exception as e:
            current_app.logger.error(f"❌ [Market] Failed to fetch ticker: {str(e)}")
            import traceback
            current_app.logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
            return jsonify({"error": f"Failed to fetch ticker: {str(e)}"}), 500

    @app.route("/api/market/markets", methods=["GET"])
    def get_available_markets():
        """Get available trading markets from Bitfinex."""
        current_app.logger.info("🏪 [Market] Available markets request")
        
        try:
            exchange = get_exchange_service()
            if not exchange:
                current_app.logger.warning("Exchange service not available")
                return jsonify({"error": "Exchange service not available"}), 503
            
            markets = exchange.get_markets()
            
            current_app.logger.info(f"✅ [Market] Successfully fetched {len(markets)} markets")
            
            return jsonify(markets), 200
            
        except ExchangeError as e:
            current_app.logger.error(f"❌ [Market] Exchange error: {str(e)}")
            return jsonify({"error": f"Exchange error: {str(e)}"}), 503
        except Exception as e:
            current_app.logger.error(f"❌ [Market] Failed to fetch markets: {str(e)}")
            import traceback
            current_app.logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
            return jsonify({"error": f"Failed to fetch markets: {str(e)}"}), 500


def get_mock_ohlcv(symbol):
    """Fallback mock OHLCV data."""
    import time
    import random
    
    current_time = int(time.time() * 1000)
    base_price = 45000
    data = []
    
    for i in range(100):
        timestamp = current_time - (99 - i) * 5 * 60 * 1000  # 5 minute intervals
        change = (random.random() - 0.5) * 0.02  # 2% max change
        
        open_price = base_price
        close_price = open_price * (1 + change)
        high_price = max(open_price, close_price) * (1 + random.random() * 0.01)
        low_price = min(open_price, close_price) * (1 - random.random() * 0.01)
        volume = random.random() * 100
        
        data.append({
            "timestamp": timestamp,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume
        })
        
        base_price = close_price
    
    return jsonify(data), 200


def get_mock_orderbook(symbol):
    """Fallback mock orderbook."""
    return jsonify({
        "symbol": symbol,
        "bids": [
            {"price": 44950, "amount": 1.5},
            {"price": 44940, "amount": 2.1},
            {"price": 44930, "amount": 0.8}
        ],
        "asks": [
            {"price": 45050, "amount": 1.2},
            {"price": 45060, "amount": 0.9},
            {"price": 45070, "amount": 2.3}
        ],
        "timestamp": int(time.time() * 1000)
    }), 200


def get_mock_ticker(symbol):
    """Fallback mock ticker."""
    import time
    return jsonify({
        "symbol": symbol,
        "last": 45000,
        "bid": 44995,
        "ask": 45005,
        "volume": 123.45,
        "timestamp": int(time.time() * 1000)
    }), 200