"""Positions API endpoints for fetching live positions from Bitfinex."""

from flask import jsonify

from backend.services.exchange import ExchangeError
from backend.services.positions_service import fetch_live_positions
from backend.services.event_logger import (
    event_logger, should_suppress_routine_log, EventType
)


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
        # Detta är routine polling - supprimerias enligt event_logger
        
        try:
            # Attempt to fetch live positions from Bitfinex
            positions = fetch_live_positions()

            # Endast logga om det INTE är routine polling
            if not should_suppress_routine_log("/api/positions", "GET"):
                event_logger.log_event(
                    EventType.API_ERROR,  # Using available type
                    f"Positions fetched: {len(positions)} positions"
                )

            return jsonify(positions), 200

        except ExchangeError as e:
            # FEL ska alltid loggas - de är meningsfulla
            event_logger.log_exchange_error("fetch_positions", str(e))
            
            # Return empty list rather than mock data for safety
            return jsonify([]), 200

        except Exception as e:
            # Kritiska fel ska alltid loggas
            event_logger.log_api_error("/api/positions", str(e))
            return jsonify({"error": str(e)}), 500
