"""Positions API endpoints for fetching live positions from Bitfinex."""

import logging
from flask import jsonify, request

from backend.services.positions_service import fetch_live_positions
from backend.services.exchange import ExchangeError

logger = logging.getLogger(__name__)

def register(app):
    @app.route("/api/positions", methods=["GET"])
    def get_positions():
        """
        Hämta live positions från Bitfinex via authenticated WebSocket (första prioritet)
        eller REST API som fallback.
        
        Query parameters:
            symbols: Optional comma-separated list of symbols to filter by
            
        Returns:
            200: List av positions från Bitfinex
            500: Server error
        """
        logger.info("� [Positions] GET positions request")
        
        try:
            # Parse query parameters
            symbols_param = request.args.get('symbols')
            symbols = symbols_param.split(',') if symbols_param else None
            
            # Använd den nya positions service som prioriterar WebSocket
            positions = fetch_live_positions(symbols)
            
            logger.info(f"✅ [Positions] Successfully retrieved {len(positions)} position entries")
            return jsonify(positions), 200
            
        except Exception as e:
            logger.error(f"❌ [Positions] Failed to fetch positions: {str(e)}")
            return jsonify({
                "error": "Failed to fetch positions",
                "details": str(e)
            }), 500
