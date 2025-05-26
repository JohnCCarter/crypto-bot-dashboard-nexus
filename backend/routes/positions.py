from flask import jsonify

def register(app):
    @app.route('/api/positions', methods=['GET'])
    def get_positions():
        mock_positions = [
            {
                "symbol": "BTC/USD",
                "amount": 0.1,
                "entry_price": 27000.0,
                "pnl": 320.0,
                "timestamp": "2025-05-26T08:30:00Z"
            },
            {
                "symbol": "ETH/USD",
                "amount": 2.0,
                "entry_price": 1800.0,
                "pnl": -45.0,
                "timestamp": "2025-05-26T07:45:00Z"
            }
        ]
        return jsonify(mock_positions)
