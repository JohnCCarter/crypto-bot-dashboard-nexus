"""Live market data API endpoints using Bitfinex - NO MOCK DATA."""

from flask import jsonify, request, current_app
from backend.services.exchange import ExchangeService, ExchangeError


def register(app):
    """Register live market data routes."""
    
    def get_exchange_service():
        """Get exchange service from app context."""
        try:
            if hasattr(current_app, '_services') and current_app._services:
                return current_app._services.get("exchange")
            
            current_app.logger.warning(
                "Exchange service not available, cannot fetch live data"
            )
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
        
        Returns:
            200: Live OHLCV data from Bitfinex
            503: Exchange service not available (NO MOCK DATA)
            500: Server error
        """
        current_app.logger.info(f"📊 [Market] Live OHLCV request for {symbol}")
        
        try:
            exchange = get_exchange_service()
            if not exchange:
                current_app.logger.error(
                    "❌ [Market] CRITICAL: Exchange service not available. "
                    "NO MOCK DATA will be provided for trading safety."
                )
                return jsonify({
                    "error": "Exchange service not available",
                    "message": "Live data required for trading - "
                             "no fallback data"
                }), 503
            
            timeframe = request.args.get('timeframe', '5m')
            limit = min(int(request.args.get('limit', 100)), 1000)
            
            current_app.logger.info(
                f"📊 [Market] Fetching {limit} {timeframe} "
                f"candles for {symbol}"
            )
            
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
            
            current_app.logger.info(
                f"📊 [Market] Using symbol format: {formatted_symbol}"
            )
            
            ohlcv_data = exchange.fetch_ohlcv(formatted_symbol, timeframe, limit)
            
            current_app.logger.info(
                f"✅ [Market] Successfully fetched {len(ohlcv_data)} candles"
            )
            
            return jsonify(ohlcv_data), 200
            
        except ExchangeError as e:
            current_app.logger.error(f"❌ [Market] Exchange error: {str(e)}")
            return jsonify({
                "error": f"Exchange error: {str(e)}",
                "message": "Live market data unavailable"
            }), 503
        except Exception as e:
            current_app.logger.error(f"❌ [Market] Failed to fetch OHLCV: {str(e)}")
            import traceback
            current_app.logger.error(
                f"❌ [Market] Stack trace: {traceback.format_exc()}"
            )
            return jsonify({
                "error": f"Failed to fetch OHLCV data: {str(e)}"
            }), 500

    @app.route("/api/market/orderbook/<symbol>", methods=["GET"])  
    def get_live_orderbook(symbol):
        """
        Get live order book from Bitfinex.
        
        Query parameters:
        - limit: Number of levels per side (default: 20, max: 100)
        
        Returns:
            200: Live orderbook data from Bitfinex
            503: Exchange service not available (NO MOCK DATA)
            500: Server error
        """
        current_app.logger.info(f"📋 [Market] Live orderbook request for {symbol}")
        
        try:
            exchange = get_exchange_service()
            if not exchange:
                current_app.logger.error(
                    "❌ [Market] CRITICAL: Exchange service not available. "
                    "NO MOCK ORDERBOOK will be provided for trading safety."
                )
                return jsonify({
                    "error": "Exchange service not available",
                    "message": "Live orderbook required for trading - "
                             "no fallback data"
                }), 503
            
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
                
            current_app.logger.info(
                f"📋 [Market] Fetching orderbook for {formatted_symbol} "
                f"with limit {limit}"
            )
            current_app.logger.info(
                f"📋 [Market] Exchange ID: "
                f"{getattr(exchange.exchange, 'id', 'unknown')}"
            )
            
            orderbook = exchange.fetch_order_book(formatted_symbol, limit)
            
            current_app.logger.info(
                f"✅ [Market] Successfully fetched orderbook with "
                f"{len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks"
            )
            
            return jsonify(orderbook), 200
            
        except ExchangeError as e:
            current_app.logger.error(
                f"❌ [Market] CRITICAL: Exchange error for orderbook: "
                f"{str(e)}. NO MOCK DATA will be provided for trading safety."
            )
            return jsonify({
                "error": f"Exchange error: {str(e)}",
                "message": "Live orderbook unavailable - no fallback data"
            }), 503
        except Exception as e:
            current_app.logger.error(
                f"❌ [Market] Failed to fetch orderbook: {str(e)}"
            )
            import traceback
            current_app.logger.error(
                f"❌ [Market] Stack trace: {traceback.format_exc()}"
            )
            return jsonify({
                "error": f"Failed to fetch orderbook: {str(e)}",
                "message": "Live orderbook unavailable"
            }), 500

    @app.route("/api/market/ticker/<symbol>", methods=["GET"])
    def get_live_ticker(symbol):
        """
        Get live ticker data from Bitfinex.
        
        Returns:
            200: Live ticker data from Bitfinex
            503: Exchange service not available (NO MOCK DATA)
            500: Server error
        """
        current_app.logger.info(f"💰 [Market] Live ticker request for {symbol}")
        
        try:
            exchange = get_exchange_service()
            if not exchange:
                current_app.logger.error(
                    "❌ [Market] CRITICAL: Exchange service not available. "
                    "NO MOCK TICKER will be provided for trading safety."
                )
                return jsonify({
                    "error": "Exchange service not available",
                    "message": "Live ticker required for trading - "
                             "no fallback data"
                }), 503
            
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
                
            current_app.logger.info(
                f"💰 [Market] Fetching ticker for {formatted_symbol}"
            )
            
            ticker = exchange.fetch_ticker(formatted_symbol)
            
            current_app.logger.info(
                f"✅ [Market] Successfully fetched ticker: {ticker['last']}"
            )
            
            return jsonify(ticker), 200
            
        except ExchangeError as e:
            current_app.logger.error(f"❌ [Market] Exchange error: {str(e)}")
            return jsonify({
                "error": f"Exchange error: {str(e)}",
                "message": "Live ticker unavailable"
            }), 503
        except Exception as e:
            current_app.logger.error(f"❌ [Market] Failed to fetch ticker: {str(e)}")
            import traceback
            current_app.logger.error(
                f"❌ [Market] Stack trace: {traceback.format_exc()}"
            )
            return jsonify({
                "error": f"Failed to fetch ticker: {str(e)}"
            }), 500

    @app.route("/api/market/markets", methods=["GET"])
    def get_available_markets():
        """
        Get available trading markets from Bitfinex.
        
        Returns:
            200: Available markets from Bitfinex
            503: Exchange service not available
            500: Server error
        """
        current_app.logger.info("🏪 [Market] Available markets request")
        
        try:
            exchange = get_exchange_service()
            if not exchange:
                current_app.logger.warning("Exchange service not available")
                return jsonify({
                    "error": "Exchange service not available",
                    "message": "Cannot fetch available markets"
                }), 503
            
            markets = exchange.get_markets()
            
            current_app.logger.info(
                f"✅ [Market] Successfully fetched "
                f"{len(markets)} markets"
            )
            
            return jsonify(markets), 200
            
        except ExchangeError as e:
            current_app.logger.error(f"❌ [Market] Exchange error: {str(e)}")
            return jsonify({
                "error": f"Exchange error: {str(e)}",
                "message": "Cannot fetch markets"
            }), 503
        except Exception as e:
            current_app.logger.error(f"❌ [Market] Failed to fetch markets: {str(e)}")
            import traceback
            current_app.logger.error(
                f"❌ [Market] Stack trace: {traceback.format_exc()}"
            )
            return jsonify({
                "error": f"Failed to fetch markets: {str(e)}"
            }), 500