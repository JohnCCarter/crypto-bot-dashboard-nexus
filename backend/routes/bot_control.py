from flask import jsonify, current_app

from backend.services.bot_service import get_bot_status, start_bot, stop_bot

# Intern statusflagga
bot_status = {"running": False}


def register(app):
    @app.route("/api/start-bot", methods=["POST"])
    def start_bot_route():
        """Startar tradingboten."""
        current_app.logger.info("🤖 [Backend] START bot request received")
        current_app.logger.info(
            f"🤖 [Backend] Current bot status before start: {bot_status}"
        )

        try:
            current_app.logger.info("🤖 [Backend] Calling start_bot() service...")
            result = start_bot()

            current_app.logger.info(f"✅ [Backend] Bot started successfully: {result}")
            current_app.logger.info(f"✅ [Backend] New bot status: {bot_status}")

            return jsonify(result), 200
        except Exception as e:
            current_app.logger.error(f"❌ [Backend] Start bot failed: {str(e)}")
            current_app.logger.error(f"❌ [Backend] Exception type: {type(e).__name__}")
            current_app.logger.error(
                f"❌ [Backend] Bot status after error: {bot_status}"
            )
            import traceback

            current_app.logger.error(
                f"❌ [Backend] Stack trace: {traceback.format_exc()}"
            )

            return (
                jsonify({"error": f"Failed to start bot: {str(e)}", "success": False}),
                500,
            )

    @app.route("/api/stop-bot", methods=["POST"])
    def stop_bot_route():
        """Stoppar tradingboten."""
        current_app.logger.info("🤖 [Backend] STOP bot request received")
        current_app.logger.info(
            f"🤖 [Backend] Current bot status before stop: {bot_status}"
        )

        try:
            current_app.logger.info("🤖 [Backend] Calling stop_bot() service...")
            result = stop_bot()

            current_app.logger.info(f"✅ [Backend] Bot stopped successfully: {result}")
            current_app.logger.info(f"✅ [Backend] New bot status: {bot_status}")

            return jsonify(result), 200
        except Exception as e:
            current_app.logger.error(f"❌ [Backend] Stop bot failed: {str(e)}")
            current_app.logger.error(f"❌ [Backend] Exception type: {type(e).__name__}")
            current_app.logger.error(
                f"❌ [Backend] Bot status after error: {bot_status}"
            )
            import traceback

            current_app.logger.error(
                f"❌ [Backend] Stack trace: {traceback.format_exc()}"
            )

            return (
                jsonify({"error": f"Failed to stop bot: {str(e)}", "success": False}),
                500,
            )

    @app.route("/api/bot-status", methods=["GET"])
    def get_bot_status_route():
        """Returnerar nuvarande status för tradingboten."""
        current_app.logger.info("🤖 [Backend] Bot status request received")

        try:
            status = get_bot_status()
            current_app.logger.info(f"✅ [Backend] Bot status retrieved: {status}")

            return jsonify(status), 200
        except Exception as e:
            current_app.logger.error(f"❌ [Backend] Get bot status failed: {str(e)}")
            current_app.logger.error(f"❌ [Backend] Exception type: {type(e).__name__}")
            import traceback

            current_app.logger.error(
                f"❌ [Backend] Stack trace: {traceback.format_exc()}"
            )

            return jsonify({"error": f"Failed to get bot status: {str(e)}"}), 500
