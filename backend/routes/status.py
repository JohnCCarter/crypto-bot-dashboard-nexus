from flask import Blueprint, jsonify

def register(app):
    @app.route('/api/status', methods=['GET'])
    def get_status():
        return jsonify({
            "status": "running",
            "balance": {
                "USD": 10500.0,
                "BTC": 0.25
            }
        })
