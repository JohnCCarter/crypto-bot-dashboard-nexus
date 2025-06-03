from flask import jsonify
from services.balance_service import fetch_balances

def register(app):
    @app.route('/api/balances', methods=['GET'])
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
            for currency, info in balance_data['total'].items():
                if info is None or info == 0:
                    continue
                result.append({
                    'currency': currency,
                    'total_balance': balance_data['total'][currency],
                    'available': balance_data['free'][currency]
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
