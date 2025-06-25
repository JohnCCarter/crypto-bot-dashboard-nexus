import json
import logging

from flask import current_app, jsonify

from backend.services.balance_service import fetch_balances_list

logger = logging.getLogger(__name__)

def register(app):
    @app.route("/api/balances", methods=["GET"])
    def get_balances():
        """
        Hämta account balances från Bitfinex via authenticated WebSocket (första prioritet)
        eller REST API som fallback.
        
        Returns:
            200: List av balances från Bitfinex
            500: Server error
        """
        logger.info("💰 [Balances] GET balances request")
        
        try:
            # Använd den nya balance service som prioriterar WebSocket
            balances = fetch_balances_list()
            
            logger.info(f"✅ [Balances] Successfully retrieved {len(balances)} balance entries")
            return jsonify(balances), 200
            
        except Exception as e:
            logger.error(f"❌ [Balances] Failed to fetch balances: {str(e)}")
            return jsonify({
                "error": "Failed to fetch balances", 
                "details": str(e)
            }), 500
