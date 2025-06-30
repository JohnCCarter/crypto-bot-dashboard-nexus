from flask import Blueprint, jsonify

from backend.services.bot_manager import get_bot_status, start_bot, stop_bot
from backend.services.event_logger import (
    event_logger, should_suppress_routine_log, EventType
)

# Intern statusflagga
bot_status = {"running": False}

bot_control_bp = Blueprint('bot_control', __name__)

@bot_control_bp.route('/api/bot/start', methods=['POST'])
def start_bot_endpoint():
    """Start the bot if it is not already running."""
    result = start_bot()
    return jsonify(result), 200 if result['status'] == 'started' else 400

@bot_control_bp.route('/api/bot/stop', methods=['POST'])
def stop_bot_endpoint():
    """Stop the bot if it is running."""
    result = stop_bot()
    return jsonify(result), 200 if result['status'] == 'stopped' else 400

def register(app):
    # Registrera Blueprint för bot-kontroll
    app.register_blueprint(bot_control_bp)
    
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
