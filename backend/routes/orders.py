from flask import request, jsonify
from backend.services.order_service import place_order

def register(app):
    @app.route('/api/order', methods=['POST'])
    def place_order_route():
        """
        Skapa och logga en order.
        ---
        requestBody:
            description: Orderparametrar (symbol, order_type, side, amount, price)
        responses:
            201:
                description: Order skapad
            400:
                description: Felaktig indata
        """
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400
        try:
            order = place_order(data)
            return jsonify({"message": "Order received", "order": order}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400
