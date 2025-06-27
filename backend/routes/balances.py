from flask import jsonify

from backend.services.balance_service import fetch_balances
from backend.services.event_logger import (
    event_logger, should_suppress_routine_log, EventType
)


def register(app):
    @app.route("/api/balances", methods=["GET"])
    def get_balances():
        """
        Hämta saldon från Bitfinex.
        ---
        responses:
            200:
                Beskriver en lista med saldon per valuta.
            500:
                Felmeddelande om något går fel.
        """
        try:
            balance_data = fetch_balances()
            result = []
            for currency, info in balance_data["total"].items():
                if info is None or info == 0:
                    continue
                result.append(
                    {
                        "currency": currency,
                        "total_balance": balance_data["total"][currency],
                        "available": balance_data["free"][currency],
                    }
                )
            
            # Balance GET requests är routine polling - suppress dem
            if should_suppress_routine_log("/api/balances", "GET"):
                pass  # Suppress routine balance polling
            else:
                # Om det skulle loggas, använd rätt event type
                event_logger.log_event(
                    EventType.PARAMETER_CHANGED,  
                    f"Balance fetched: {len(result)} currencies"
                )
                
            return jsonify(result), 200
        except Exception as e:
            # FEL ska alltid loggas - de är meningsfulla
            event_logger.log_api_error("/api/balances", str(e))
            return jsonify({"error": str(e)}), 500
