from flask import jsonify

def register(app):
    @app.route('/api/orderbook/<symbol>', methods=['GET'])
    def get_orderbook(symbol):
        # Mockad order book för valfri symbol
        mock_data = {
            "bids": [[27800.5, 1.2], [27795.0, 0.6], [27790.0, 0.8]],
            "asks": [[27810.0, 0.8], [27815.5, 1.0], [27820.0, 0.5]]
        }
        return jsonify(mock_data)
