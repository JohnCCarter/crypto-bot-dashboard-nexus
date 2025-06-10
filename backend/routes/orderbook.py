from flask import jsonify, request
import pandas as pd

from backend.services.orderbook_service import get_mock_orderbook
from backend.strategies.indicators import find_fvg_zones


def register(app):
    @app.route("/api/orderbook/<symbol>", methods=["GET"])
    def get_orderbook(symbol):
        """
        Hämta orderbok för given symbol (mockad data).
        ---
        responses:
            200:
                description: Orderbok (bids och asks)
        """
        try:
            data = get_mock_orderbook(symbol)
            return jsonify(data), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            return jsonify({"error": "Unexpected error"}), 500

    @app.route("/api/indicators/fvg", methods=["POST"])
    def get_fvg_zones():
        """
        Returnerar FVG-zoner för given OHLCV-data.
        ---
        requestBody:
            required: true
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            data:
                                type: object
                                description: OHLCV-data
                            min_gap_size:
                                type: number
                            direction:
                                type: string
        responses:
            200:
                description: Lista av FVG-zoner
        """
        try:
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            req = request.get_json()
            if "data" not in req:
                return jsonify({"error": "Missing 'data' field"}), 400
            df = None
            try:
                df = pd.DataFrame(req["data"])
            except Exception:
                return jsonify({"error": "Invalid data format"}), 400
            min_gap_size = req.get("min_gap_size", 0.0)
            direction = req.get("direction", "both")
            zones = find_fvg_zones(df, min_gap_size=min_gap_size, direction=direction)
            return jsonify(zones), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
