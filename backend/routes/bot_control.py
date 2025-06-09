from flask import jsonify

from backend.services.bot_service import get_bot_status, start_bot, stop_bot

# Intern statusflagga
bot_status = {"running": False}


def register(app):
    @app.route("/api/start-bot", methods=["POST"])
    def start_bot_route():
        """Startar tradingboten."""
        try:
            result = start_bot()
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/stop-bot", methods=["POST"])
    def stop_bot_route():
        """Stoppar tradingboten."""
        try:
            result = stop_bot()
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/bot-status", methods=["GET"])
    def get_bot_status_route():
        """Returnerar nuvarande status för tradingboten."""
        try:
            status = get_bot_status()
            return jsonify(status), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
