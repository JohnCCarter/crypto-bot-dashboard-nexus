"""Trading bot application entrypoint."""

import json
import logging
import os
from typing import Any, Dict

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from backend.routes.backtest import backtest_bp
from backend.routes.balances import register as register_balances
from backend.routes.bot_control import register as register_bot_control
from backend.routes.config import register as register_config
from backend.routes.orders import register as register_orders
from backend.routes.positions import register as register_positions
from backend.routes.status import status_bp
from backend.routes.strategy_analysis import strategy_analysis_bp
from backend.routes.live_portfolio import live_portfolio_bp
from backend.routes import market_data
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
CORS(app, origins=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"])

# Registrera routes som inte använder blueprint
register_balances(app)
register_bot_control(app)
register_orders(app)
register_positions(app)
register_config(app)
market_data.register(app)


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json file with fallback to environment variables.
    
    Returns:
        Dict containing configuration data
    """
    config_file = "backend/config.json"
    
    try:
        # Try to load from config file
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                logger.info("Loaded configuration from config.json")
                return file_config
        else:
            logger.warning(f"Config file {config_file} not found, using environment variables")
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load config file: {e}, falling back to environment variables")
    
    # Fallback to environment variables
    return {
        "risk": {
            "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "0.1")),
            "max_leverage": float(os.getenv("MAX_LEVERAGE", "3.0")),
            "stop_loss_percent": float(os.getenv("STOP_LOSS_PCT", "2.0")),
            "take_profit_percent": float(os.getenv("TAKE_PROFIT_PCT", "4.0")),
            "max_daily_loss": float(os.getenv("MAX_DAILY_LOSS", "5.0")),
            "max_open_positions": int(os.getenv("MAX_OPEN_POSITIONS", "5")),
            "min_signal_confidence": float(os.getenv("MIN_SIGNAL_CONFIDENCE", "0.6")),
            "probability_weight": float(os.getenv("PROBABILITY_WEIGHT", "0.5")),
            "risk_per_trade": float(os.getenv("RISK_PER_TRADE", "0.02")),
            "lookback": int(os.getenv("LOOKBACK", "5"))
        }
    }


# Initialize services
def init_services() -> Dict[str, Any]:
    """
    Initialize trading services.

    Returns:
        Dict containing initialized services
    """
    # Load configuration from file
    config = load_config()
    
    # Exchange configuration from environment variables (sensitive data)
    exchange_config = {
        "exchange_id": os.getenv("EXCHANGE_ID", "bitfinex"),
        "api_key": os.getenv("BITFINEX_API_KEY"),
        "api_secret": os.getenv("BITFINEX_API_SECRET"),
    }

    # Initialize exchange service
    exchange = ExchangeService(
        exchange_config["exchange_id"], 
        exchange_config["api_key"], 
        exchange_config["api_secret"]
    )

    # Initialize risk manager with new parameters
    risk_config = config.get("risk", {})
    
    # Convert percentage values and ensure all required parameters exist
    risk_params_dict = {
        "max_position_size": risk_config.get("max_position_size", 0.1),
        "max_leverage": risk_config.get("max_leverage", 3.0),
        "stop_loss_pct": risk_config.get("stop_loss_percent", 2.0) / 100.0,  # Convert % to decimal
        "take_profit_pct": risk_config.get("take_profit_percent", 4.0) / 100.0,  # Convert % to decimal
        "max_daily_loss": risk_config.get("max_daily_loss", 5.0) / 100.0,  # Convert % to decimal
        "max_open_positions": risk_config.get("max_open_positions", 5),
        "min_signal_confidence": risk_config.get("min_signal_confidence", 0.6),
        "probability_weight": risk_config.get("probability_weight", 0.5),
    }
    
    logger.info(f"Initializing risk manager with params: {risk_params_dict}")
    
    try:
        risk_params = RiskParameters(**risk_params_dict)
        risk_manager = RiskManager(risk_params)
        logger.info("Risk manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize risk manager: {e}")
        # Create with minimal safe defaults
        risk_params = RiskParameters(
            max_position_size=0.1,
            max_leverage=2.0,
            stop_loss_pct=0.02,
            take_profit_pct=0.04,
            max_daily_loss=0.05,
            max_open_positions=5,
            min_signal_confidence=0.6,
            probability_weight=0.5
        )
        risk_manager = RiskManager(risk_params)
        logger.info("Risk manager initialized with safe defaults")

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
        "exchange_config": exchange_config,
    }


# Initialize services
services = init_services()

# Make services available to blueprints
app._services = services


def register_routes():
    """Register all API routes."""
    app.register_blueprint(status_bp)
    app.register_blueprint(backtest_bp)
    app.register_blueprint(strategy_analysis_bp)
    app.register_blueprint(live_portfolio_bp)


# Register routes
register_routes()


# Root route for API documentation
@app.route("/", methods=["GET"])
def api_documentation():
    """Show API documentation and available endpoints."""
    api_info = {
        "name": "Crypto Trading Bot API",
        "version": "1.0.0",
        "description": "Live cryptocurrency trading bot with Bitfinex integration",
        "status": "running",
        "endpoints": {
            "health": {
                "url": "/api/status",
                "description": "Bot health check and basic status"
            },
            "live_market_data": {
                "ohlcv": "/api/market/ohlcv/{symbol}?timeframe=5m&limit=100",
                "orderbook": "/api/market/orderbook/{symbol}?limit=20", 
                "ticker": "/api/market/ticker/{symbol}",
                "markets": "/api/market/markets"
            },
            "trading": {
                "orders": "/api/orders",
                "positions": "/api/positions", 
                "balances": "/api/balances"
            },
            "live_portfolio": {
                "snapshot": "/api/live-portfolio/snapshot?symbols=BTC/USD,ETH/USD",
                "position_value": "/api/live-portfolio/position-value?symbol=BTC/USD&amount=0.1",
                "validate_trade": "/api/live-portfolio/validate-trade (POST)",
                "performance": "/api/live-portfolio/performance?timeframe=24h",
                "market_overview": "/api/live-portfolio/market-overview?symbols=BTC/USD,ETH/USD"
            },
            "bot_control": {
                "start": "/api/start-bot",
                "stop": "/api/stop-bot",
                "status": "/api/bot-status"
            },
            "analysis": {
                "backtest": "/api/backtest/run",
                "strategy_analysis": "/api/strategy-analysis"
            }
        },
        "features": [
            "Live Bitfinex integration",
            "Real-time OHLCV data", 
            "Live order book data",
            "Live portfolio management with real-time pricing",
            "Real-time position valuation and PnL tracking",
            "Live trading capacity validation",
            "Market overview with live data quality metrics", 
            "Trading bot control",
            "Strategy backtesting",
            "Risk management",
            "Enhanced logging"
        ],
        "frontend_url": "http://localhost:8080"
    }
    
    return jsonify(api_info)


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
    app.run(debug=False, port=5000)
