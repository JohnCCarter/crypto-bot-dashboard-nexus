from flask import jsonify
from services.bot_service import start_bot, stop_bot, get_bot_status

# Intern statusflagga
bot_status = {"running": False}

def register(app):
    @app.route('/api/start-bot', methods=['POST'])
    def start_bot_route():
        """Startar tradingboten."""
        return jsonify(start_bot())

    @app.route('/api/stop-bot', methods=['POST'])
    def stop_bot_route():
        """Stoppar tradingboten."""
        return jsonify(stop_bot())

    @app.route('/api/bot-status', methods=['GET'])
    def get_bot_status_route():
        """Returnerar nuvarande status för tradingboten."""
        return jsonify(get_bot_status())
