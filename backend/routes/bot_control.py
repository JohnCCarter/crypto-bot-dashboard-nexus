from flask import jsonify

# Intern statusflagga
bot_status = {"running": False}

def register(app):
    @app.route('/api/start-bot', methods=['POST'])
    def start_bot():
        bot_status["running"] = True
        return jsonify({"message": "Bot started", "status": "running"})

    @app.route('/api/stop-bot', methods=['POST'])
    def stop_bot():
        bot_status["running"] = False
        return jsonify({"message": "Bot stopped", "status": "stopped"})

    @app.route('/api/bot-status', methods=['GET'])
    def get_bot_status():
        return jsonify({"status": "running" if bot_status["running"] else "stopped"})
