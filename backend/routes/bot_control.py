from flask import jsonify

from backend.services.bot_manager import get_bot_status, start_bot, stop_bot
from backend.services.event_logger import (
    event_logger, should_suppress_routine_log, EventType
)

# Intern statusflagga
bot_status = {"running": False}


def register(app):
    @app.route("/api/start-bot", methods=["POST"])
    def start_bot_route():
        """Startar tradingboten."""
        # BOT START är en VERKLIG användaraktion - alltid loggas!
        
        try:
            result = start_bot()
            
            # Logga framgångsrik bot start
            event_logger.log_bot_action("start", {
                "success": True,
                "result": str(result)
            })

            return jsonify(result), 200
        except Exception as e:
            # Fel vid bot start ska alltid loggas
            event_logger.log_event(
                EventType.BOT_ERROR,
                f"Failed to start bot: {str(e)}"
            )

            return (
                jsonify({"error": f"Failed to start bot: {str(e)}", "success": False}),
                500,
            )

    @app.route("/api/stop-bot", methods=["POST"])
    def stop_bot_route():
        """Stoppar tradingboten."""
        # BOT STOP är en VERKLIG användaraktion - alltid loggas!
        
        try:
            result = stop_bot()
            
            # Logga framgångsrik bot stop
            event_logger.log_bot_action("stop", {
                "success": True,
                "result": str(result)
            })

            return jsonify(result), 200
        except Exception as e:
            # Fel vid bot stop ska alltid loggas
            event_logger.log_event(
                EventType.BOT_ERROR,
                f"Failed to stop bot: {str(e)}"
            )

            return (
                jsonify({"error": f"Failed to stop bot: {str(e)}", "success": False}),
                500,
            )

    @app.route("/api/bot-status", methods=["GET"])
    def get_bot_status_route():
        """Returnerar nuvarande status för tradingboten."""
        # Detta är routine polling - supprimeras enligt event_logger
        
        try:
            status = get_bot_status()
            
            # Endast logga om det INTE är routine polling
            if not should_suppress_routine_log("/api/bot-status", "GET"):
                event_logger.log_event(
                    EventType.API_ERROR,  # Using available type
                    f"Bot status retrieved: {status.get('status', 'unknown')}"
                )

            return jsonify(status), 200
        except Exception as e:
            # Fel ska alltid loggas
            event_logger.log_api_error("/api/bot-status", str(e))
            return jsonify({"error": f"Failed to get bot status: {str(e)}"}), 500
