from flask import jsonify
from services.orderbook_service import get_mock_orderbook

def register(app):
    @app.route('/api/orderbook/<symbol>', methods=['GET'])
    def get_orderbook(symbol):
        """
        Hämta orderbok för given symbol (mockad data).
        ---
        responses:
            200:
                description: Orderbok (bids och asks)
        """
        return jsonify(get_mock_orderbook(symbol))
