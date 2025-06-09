from flask import jsonify

from backend.services.orderbook_service import get_mock_orderbook


def register(app):
    @app.route("/api/orderbook/<symbol>", methods=["GET"])
    def get_orderbook(symbol):
        """
        Hämta orderbok för given symbol (mockad data).
        ---
        responses:
            200:
                description: Orderbok (bids och asks)
        """
        try:
            data = get_mock_orderbook(symbol)
            return jsonify(data), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            return jsonify({"error": "Unexpected error"}), 500
