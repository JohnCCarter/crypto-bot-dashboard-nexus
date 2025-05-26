import os
import ccxt
from flask import jsonify
from dotenv import load_dotenv

load_dotenv()

def register(app):
    @app.route('/api/balances', methods=['GET'])
    def get_balances():
        try:
            api_key = os.getenv('BITFINEX_API_KEY')
            api_secret = os.getenv('BITFINEX_API_SECRET')

            if not api_key or not api_secret:
                print("❌ API-nycklar saknas eller kunde inte laddas från .env")
                return jsonify({'error': 'API keys not configured properly'}), 500

            exchange = ccxt.bitfinex({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })

            print("🔍 Hämtar saldon från Bitfinex...")
            balance_data = exchange.fetch_balance()
            result = []

            for currency, info in balance_data['total'].items():
                if info is None or info == 0:
                    continue
                result.append({
                    'currency': currency,
                    'total_balance': balance_data['total'][currency],
                    'available': balance_data['free'][currency]
                })

            print("✅ Saldon hämtade:", result)
            return jsonify(result)
        except Exception as e:
            print("❌ Fel i get_balances():", str(e))
            return jsonify({'error': str(e)}), 500
