"""Positions API endpoints for fetching live positions from Bitfinex."""

from flask import current_app, jsonify

from backend.services.exchange import ExchangeError
from backend.services.positions_service import fetch_live_positions


def register(app):
    @app.route("/api/positions", methods=["GET"])
    def get_positions():
        """
        Fetch current positions from Bitfinex.

        Returns live positions if API keys are configured,
        otherwise returns empty list (no mock data for live trading).

        ---
        responses:
            200:
                description: List of live positions from Bitfinex
            500:
                description: Server error
        """
        current_app.logger.info("📋 [Positions] Live positions request received")

        try:
            # Attempt to fetch live positions from Bitfinex
            positions = fetch_live_positions()

            current_app.logger.info(
                f"✅ [Positions] Successfully fetched " f"{len(positions)} positions"
            )

            return jsonify(positions), 200

        except ExchangeError as e:
            current_app.logger.error(f"❌ [Positions] Exchange error: {str(e)}")

            # For exchange errors, return empty list rather than mock data
            # This prevents trading bot from using fake position data
            current_app.logger.warning(
                "⚠️ [Positions] Returning empty positions " "due to exchange error"
            )
            return jsonify([]), 200

        except Exception as e:
            current_app.logger.error(
                f"❌ [Positions] Failed to fetch positions: {str(e)}"
            )

            # Log the full error for debugging
            import traceback

            current_app.logger.error(
                f"❌ [Positions] Stack trace: {traceback.format_exc()}"
            )

            return jsonify({"error": str(e)}), 500
