from flask import request, jsonify
import datetime

# Simulerad ordersamling
order_log = []

def register(app):
    @app.route('/api/order', methods=['POST'])
    def place_order():
        data = request.get_json()
        symbol = data.get("symbol")
        order_type = data.get("order_type")
        side = data.get("side")
        amount = data.get("amount")
        price = data.get("price")

        order = {
            "symbol": symbol,
            "order_type": order_type,
            "side": side,
            "amount": amount,
            "price": price,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

        order_log.append(order)

        return jsonify({"message": "Order received", "order": order}), 201
