"""Trading bot application entrypoint."""

import logging
import os
from typing import Any, Dict

from flask import Flask, jsonify
from flask_cors import CORS

from backend.routes.backtest import backtest_bp
from backend.routes.balances import register as register_balances
from backend.routes.bot_control import register as register_bot_control
from backend.routes.orders import orders_bp
from backend.routes.status import status_bp
from backend.services.exchange import ExchangeService
from backend.services.monitor import Monitor
from backend.services.order_service import OrderService
from backend.services.risk_manager import RiskManager, RiskParameters

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Registrera routes som inte använder blueprint
register_balances(app)
register_bot_control(app)


# Initialize services
def init_services() -> Dict[str, Any]:
    """
    Initialize trading services.

    Returns:
        Dict containing initialized services
    """
    # Load configuration
    config = {
        "exchange_id": os.getenv("EXCHANGE_ID", "binance"),
        "api_key": os.getenv("EXCHANGE_API_KEY"),
        "api_secret": os.getenv("EXCHANGE_API_SECRET"),
        "risk_params": {
            "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "0.1")),
            "max_leverage": float(os.getenv("MAX_LEVERAGE", "3.0")),
            "stop_loss_pct": float(os.getenv("STOP_LOSS_PCT", "0.02")),
            "take_profit_pct": float(os.getenv("TAKE_PROFIT_PCT", "0.04")),
            "max_daily_loss": float(os.getenv("MAX_DAILY_LOSS", "0.05")),
            "max_open_positions": int(os.getenv("MAX_OPEN_POSITIONS", "5")),
        },
    }

    # Initialize exchange service
    exchange = ExchangeService(
        config["exchange_id"], config["api_key"], config["api_secret"]
    )

    # Initialize risk manager
    risk_params = RiskParameters(**config["risk_params"])
    risk_manager = RiskManager(risk_params)

    # Initialize monitor
    monitor = Monitor()

    # Initialize order service
    order_service = OrderService(exchange)

    return {
        "exchange": exchange,
        "risk_manager": risk_manager,
        "monitor": monitor,
        "order_service": order_service,
        "config": config,
    }


# Initialize services
services = init_services()


def register_routes():
    """Register all API routes."""
    app.register_blueprint(status_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(backtest_bp)


# Register routes
register_routes()


# Add monitoring endpoints
@app.route("/api/monitor/status", methods=["GET"])
def get_status():
    """Get trading bot status."""
    try:
        # Get performance report
        report = services["monitor"].get_performance_report()

        # Get exchange status
        exchange_status = services["exchange"].fetch_ticker("BTC/USD")

        return jsonify(
            {"status": "running", "performance": report, "market": exchange_status}
        )
    except Exception as e:
        logger.error("Error getting status: %s", str(e))
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/monitor/alerts", methods=["GET"])
def get_alerts():
    """Get recent alerts."""
    try:
        alerts = services["monitor"].get_recent_alerts()
        return jsonify(
            {
                "alerts": [
                    {
                        "level": alert.level.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "metadata": alert.metadata,
                    }
                    for alert in alerts
                ]
            }
        )
    except Exception as e:
        logger.error("Error getting alerts: %s", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
