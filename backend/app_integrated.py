"""
🚀 Trading bot application entrypoint - SUPABASE INTEGRATED VERSION
==================================================================
ERSÄTTER: backend/app.py
ANVÄNDER: Supabase-integrerade services för persistent data
"""

import json
import logging
import os
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

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

# 🚀 SUPABASE INTEGRATION - Ersätt gamla services
from backend.services.integrated_risk_manager import (
    IntegratedRiskManager, RiskParameters
)
from backend.services.integrated_order_service import IntegratedOrderService
from backend.services.simple_database_service import simple_db
from backend.services.auth_service import (
    AuthService, init_rate_limiter, require_auth, public_endpoint
)

# Load environment variables from .env file
load_dotenv()

# Configure logging for production performance
log_level = (
    logging.WARNING if os.getenv("ENVIRONMENT") == "production" else logging.INFO
)
logging.basicConfig(
    level=log_level, format="[%(asctime)s] %(levelname)s: %(message)s"  # Shorter format
)
logger = logging.getLogger(__name__)

# Silence verbose libraries in production
if os.getenv("ENVIRONMENT") == "production":
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

# Initialize Flask app
app = Flask(__name__)

# Secure CORS configuration - only allow specific development origins
allowed_origins = [
    "http://localhost:3000",    # React dev server (alternative)
    "http://localhost:8080",    # Vite dev server (alternative)
    "http://localhost:8081",    # Current Vite dev server
    "http://127.0.0.1:3000",    # Local React dev
    "http://127.0.0.1:8080",    # Local Vite dev (alternative)
    "http://127.0.0.1:8081",    # Local Vite dev (current)
]

# In production, only allow specific domains
if os.getenv("ENVIRONMENT") == "production":
    production_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    allowed_origins = [origin.strip() for origin in production_origins if origin.strip()]
    if not allowed_origins:
        logger.warning("⚠️ SECURITY: No production origins configured! CORS disabled.")
        allowed_origins = []

CORS(
    app,
    origins=allowed_origins,
    supports_credentials=True,  # For future authentication
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
)

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
            with open(config_file, "r") as f:
                file_config = json.load(f)
                logger.info("Loaded configuration from config.json")
                return file_config
        else:
            logger.warning(
                f"Config file {config_file} not found, using environment variables"
            )
    except (json.JSONDecodeError, IOError) as e:
        logger.error(
            f"Failed to load config file: {e}, falling back to environment variables"
        )

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
            "lookback": int(os.getenv("LOOKBACK", "5")),
        }
    }


# 🚀 SUPABASE INTEGRATED SERVICES INITIALIZATION
def init_integrated_services() -> Dict[str, Any]:
    """
    Initialize trading services with Supabase integration.
    
    ERSÄTTER: gamla init_services() som använde in-memory storage
    ANVÄNDER: Persistent Supabase services

    Returns:
        Dict containing initialized services
    """
    logger.info("🚀 Initializing services with Supabase integration...")
    
    # Load configuration from file
    config = load_config()

    # 🔍 FIRST: Verify Supabase connection
    try:
        if not simple_db.health_check():
            logger.error("❌ Supabase connection failed! Cannot start.")
            raise Exception("Supabase database not available")
        logger.info("✅ Supabase connection verified")
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        raise

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
        exchange_config["api_secret"],
    )

    # 🛡️ INTEGRATED RISK MANAGER - Uses Supabase for persistent P&L tracking
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

    logger.info(f"🛡️ Initializing IntegratedRiskManager with params: {risk_params_dict}")

    try:
        risk_params = RiskParameters(**risk_params_dict)
        risk_manager = IntegratedRiskManager(risk_params)
        logger.info("✅ IntegratedRiskManager initialized with Supabase persistence")
        
        # Log current risk status
        risk_summary = risk_manager.get_risk_summary()
        logger.info(f"📊 Risk summary: Daily P&L: {risk_summary['daily_pnl']}, Trading allowed: {risk_summary['trading_allowed']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize risk manager: {e}")
        # Create with minimal safe defaults
        risk_params = RiskParameters(
            max_position_size=0.1,
            max_leverage=2.0,
            stop_loss_pct=0.02,
            take_profit_pct=0.04,
            max_daily_loss=0.05,
            max_open_positions=5,
            min_signal_confidence=0.6,
            probability_weight=0.5,
        )
        risk_manager = IntegratedRiskManager(risk_params)
        logger.info("✅ IntegratedRiskManager initialized with safe defaults")

    # Initialize monitor
    monitor = Monitor()

    # 📋 INTEGRATED ORDER SERVICE - Uses Supabase for persistent order storage
    logger.info("📋 Initializing IntegratedOrderService with Supabase...")
    try:
        order_service = IntegratedOrderService(exchange)
        logger.info("✅ IntegratedOrderService initialized with persistent storage")
    except Exception as e:
        logger.error(f"❌ Failed to initialize order service: {e}")
        raise

    # 📊 Get initial database stats
    try:
        stats = simple_db.get_trading_stats()
        logger.info(f"📊 Database stats: {stats}")
    except Exception as e:
        logger.warning(f"⚠️ Could not get database stats: {e}")

    return {
        "exchange": exchange,
        "risk_manager": risk_manager,  # ← Now IntegratedRiskManager!
        "monitor": monitor,
        "order_service": order_service,  # ← Now IntegratedOrderService!
        "config": config,
        "exchange_config": exchange_config,
        "database": simple_db,  # ← Direct access to database service
    }


# Initialize services with Supabase integration
logger.info("🚀 Starting application with Supabase integration...")
services = init_integrated_services()

# Make services available to blueprints
app._services = services

# Initialize authentication and rate limiting
app._auth_service = AuthService()
app._limiter = init_rate_limiter(app)

# 🗄️ PERSISTENT ORDER METADATA - Using Supabase instead of in-memory dict
# The order metadata is now stored in the database via IntegratedOrderService
# No need for app._order_metadata = {} anymore!
logger.info("✅ Order metadata now handled by Supabase - no in-memory storage needed")


def register_routes():
    """Register all API routes."""
    app.register_blueprint(status_bp)
    app.register_blueprint(backtest_bp)
    app.register_blueprint(strategy_analysis_bp)
    app.register_blueprint(live_portfolio_bp)


# Register routes
register_routes()


# 🔍 ENHANCED STATUS ENDPOINT - With database health
@app.route("/api/status/health", methods=["GET"])
@public_endpoint
def database_health():
    """Check database and service health status."""
    try:
        # Check Supabase health
        db_healthy = simple_db.health_check()
        
        # Get trading stats
        stats = simple_db.get_trading_stats()
        
        # Get risk summary
        risk_summary = services["risk_manager"].get_risk_summary()
        
        health_status = {
            "status": "healthy" if db_healthy else "degraded",
            "database": {
                "connected": db_healthy,
                "stats": stats
            },
            "risk_management": {
                "daily_pnl": risk_summary["daily_pnl"],
                "trading_allowed": risk_summary["trading_allowed"],
                "total_positions": risk_summary["total_positions"]
            },
            "services": {
                "exchange": "connected",
                "risk_manager": "integrated_supabase",
                "order_service": "integrated_supabase"
            }
        }
        
        return jsonify(health_status), 200 if db_healthy else 503
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "database": {"connected": False}
        }), 500


# Authentication endpoints
@app.route("/api/auth/login", methods=["POST"])
@app._limiter.limit("5 per minute")  # Rate limit login attempts
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({
            "error": "Invalid request",
            "message": "Username and password required"
        }), 400
    
    username = data["username"]
    password = data["password"]
    
    user = app._auth_service.authenticate_user(username, password)
    if not user:
        logger.warning(f"🔒 Failed login attempt for username: {username}")
        return jsonify({
            "error": "Authentication failed",
            "message": "Invalid username or password"
        }), 401
    
    # Generate JWT token
    token = app._auth_service.generate_token(user["username"], user["role"])
    
    logger.info(f"✅ Successful login: {username} ({user['role']})")
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "username": user["username"],
            "role": user["role"],
            "permissions": user["permissions"]
        },
        "expires_in_hours": app._auth_service.token_expiry_hours
    }), 200


@app.route("/api/auth/verify", methods=["GET"])
@require_auth()
def verify_token():
    """Verify current JWT token is valid."""
    from flask import g
    return jsonify({
        "message": "Token is valid",
        "user": g.current_user
    }), 200


# Root route for API documentation - Enhanced with Supabase info
@app.route("/", methods=["GET"])
@public_endpoint
def api_documentation():
    """Show API documentation and available endpoints."""
    api_info = {
        "name": "Crypto Trading Bot API - Supabase Integrated",
        "version": "2.0.0",
        "description": "Live cryptocurrency trading bot with Bitfinex integration and persistent Supabase storage",
        "status": "running",
        "persistence": "supabase_postgresql",
        "data_safety": "persistent_across_restarts",
        "endpoints": {
            "health": {
                "basic": "/api/status",
                "database": "/api/status/health",
                "description": "Bot health check with database status",
            },
            "live_market_data": {
                "ohlcv": "/api/market/ohlcv/{symbol}?timeframe=5m&limit=100",
                "orderbook": "/api/market/orderbook/{symbol}?limit=20",
                "ticker": "/api/market/ticker/{symbol}",
                "markets": "/api/market/markets",
            },
            "trading": {
                "orders": "/api/orders (persistent storage)",
                "positions": "/api/positions (persistent storage)",
                "balances": "/api/balances",
            },
            "live_portfolio": {
                "snapshot": "/api/live-portfolio/snapshot?symbols=BTC/USD,ETH/USD",
                "position_value": "/api/live-portfolio/position-value?symbol=BTC/USD&amount=0.1",
                "validate_trade": "/api/live-portfolio/validate-trade (POST)",
                "performance": "/api/live-portfolio/performance?timeframe=24h",
                "market_overview": "/api/live-portfolio/market-overview?symbols=BTC/USD,ETH/USD",
            },
            "bot_control": {
                "start": "/api/start-bot",
                "stop": "/api/stop-bot",
                "status": "/api/bot-status",
            },
            "analysis": {
                "backtest": "/api/backtest/run",
                "strategy_analysis": "/api/strategy-analysis",
            },
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
            "🚀 PERSISTENT risk management with Supabase",
            "🚀 PERSISTENT order storage with Supabase",
            "🚀 Cross-restart data preservation",
            "Enhanced logging",
        ],
        "supabase_integration": {
            "persistent_data": True,
            "risk_tracking": "cross_restart_pnl",
            "order_history": "complete_audit_trail",
            "data_loss_protection": True
        },
        "frontend_url": "http://localhost:8080",
    }

    return jsonify(api_info)


# Add monitoring endpoints with database integration
@app.route("/api/monitor/status", methods=["GET"])
@require_auth(required_role="user")
def get_status():
    """Get trading bot status with database metrics."""
    try:
        # Get performance report
        report = services["monitor"].get_performance_report()

        # Get exchange status
        exchange_status = services["exchange"].fetch_ticker("BTC/USD")
        
        # Get database stats
        db_stats = services["database"].get_trading_stats()
        
        # Get risk summary
        risk_summary = services["risk_manager"].get_risk_summary()

        return jsonify({
            "status": "running",
            "performance": report,
            "market": exchange_status,
            "database": db_stats,
            "risk_management": risk_summary
        })
    except Exception as e:
        logger.error("Error getting status: %s", str(e))
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/monitor/alerts", methods=["GET"])
@require_auth(required_role="user")
def get_alerts():
    """Get recent alerts from both monitor and database."""
    try:
        # Get alerts from monitor
        monitor_alerts = services["monitor"].get_recent_alerts()
        
        # Get alerts from database
        db_alerts = services["database"].get_recent_alerts()
        
        # Combine alerts
        all_alerts = []
        
        # Add monitor alerts
        for alert in monitor_alerts:
            all_alerts.append({
                "source": "monitor",
                "level": alert.level.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata,
            })
        
        # Add database alerts
        for alert in db_alerts:
            all_alerts.append({
                "source": "database",
                "level": alert.get("severity", "info"),
                "message": alert.get("message", ""),
                "timestamp": alert.get("created_at", ""),
                "metadata": alert.get("metadata", {}),
            })
        
        # Sort by timestamp (most recent first)
        all_alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return jsonify({"alerts": all_alerts})
        
    except Exception as e:
        logger.error("Error getting alerts: %s", str(e))
        return jsonify({"error": str(e)}), 500


# WebSocket proxy endpoints (unchanged - works with new backend)
import websocket
import threading
import time

# WebSocket proxy globals
bitfinex_ws = None
latest_ticker_data = None
ws_connection_status = {"connected": False, "error": None, "last_heartbeat": None}

# Rate limiting för logging
last_ticker_log = 0
last_error_log = 0
ticker_update_count = 0


def on_bitfinex_message(ws, message):
    """Hantera meddelanden från Bitfinex WebSocket - Performance Optimized"""
    global latest_ticker_data, ws_connection_status, last_ticker_log, ticker_update_count
    try:
        data = json.loads(message)

        # Uppdatera heartbeat utan logging
        if isinstance(data, list) and len(data) >= 2 and data[1] == "hb":
            ws_connection_status["last_heartbeat"] = time.time()
            return

        # Hantera ticker data
        if (
            isinstance(data, list)
            and len(data) >= 2
            and isinstance(data[1], list)
            and len(data[1]) >= 10
        ):
            ticker_data = data[1]
            latest_ticker_data = {
                "symbol": "BTCUSD",
                "bid": float(ticker_data[0]),
                "ask": float(ticker_data[2]),
                "price": float(ticker_data[6]),
                "volume": float(ticker_data[7]),
                "timestamp": time.time(),
            }

            # Rate limited logging - endast var 30:e sekund
            ticker_update_count += 1
            now = time.time()
            if now - last_ticker_log > 30:
                logger.info(
                    f"📊 WebSocket updates: {ticker_update_count} tickers, price: ${latest_ticker_data['price']:,.0f}"
                )
                last_ticker_log = now
                ticker_update_count = 0

    except Exception as e:
        # Rate limited error logging - max 1 error per 60 sekunder
        global last_error_log
        now = time.time()
        if now - last_error_log > 60:
            logger.error(f"Error processing Bitfinex WebSocket message: {e}")
            last_error_log = now


def on_bitfinex_error(ws, error):
    """Hantera WebSocket errors - Rate Limited"""
    global ws_connection_status, last_error_log
    now = time.time()
    if now - last_error_log > 60:  # Max 1 error log per minute
        logger.error(f"Bitfinex WebSocket error: {error}")
        last_error_log = now
    ws_connection_status["connected"] = False
    ws_connection_status["error"] = str(error)


def on_bitfinex_close(ws, close_status_code, close_msg):
    """Hantera WebSocket disconnect"""
    global ws_connection_status
    logger.warning(f"Bitfinex WebSocket closed: {close_status_code}")
    ws_connection_status["connected"] = False


def on_bitfinex_open(ws):
    """Hantera WebSocket connection"""
    global ws_connection_status, ticker_update_count
    logger.info("✅ Backend WebSocket connected to Bitfinex - Live data active")
    ws_connection_status["connected"] = True
    ws_connection_status["error"] = None
    ticker_update_count = 0  # Reset counter

    # Subscribe till BTCUSD ticker
    ticker_msg = {"event": "subscribe", "channel": "ticker", "symbol": "tBTCUSD"}
    ws.send(json.dumps(ticker_msg))
    logger.info("📡 Backend: Subscribed to BTCUSD live data feed")


def init_bitfinex_websocket():
    """Initiera WebSocket anslutning till Bitfinex"""
    global bitfinex_ws

    try:
        logger.info("🚀 Starting Backend WebSocket connection to Bitfinex...")
        bitfinex_ws = websocket.WebSocketApp(
            "wss://api-pub.bitfinex.com/ws/2",
            on_open=on_bitfinex_open,
            on_message=on_bitfinex_message,
            on_error=on_bitfinex_error,
            on_close=on_bitfinex_close,
        )

        def run_websocket():
            """Kör WebSocket i background thread"""
            try:
                bitfinex_ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as e:
                logger.error(f"WebSocket thread error: {e}")

        # Starta WebSocket i background thread
        ws_thread = threading.Thread(target=run_websocket, daemon=True)
        ws_thread.start()
        logger.info("📡 Backend WebSocket thread started")

    except Exception as e:
        logger.error(f"Failed to initialize WebSocket: {e}")


@app.route("/api/ws-proxy/status", methods=["GET"])
@public_endpoint  # Allow public access for monitoring
def get_websocket_status():
    """Get WebSocket connection status"""
    return jsonify({
        "connected": ws_connection_status["connected"],
        "error": ws_connection_status["error"],
        "last_heartbeat": ws_connection_status["last_heartbeat"],
        "has_data": latest_ticker_data is not None
    })


@app.route("/api/ws-proxy/ticker", methods=["GET"])
@app._limiter.limit("60 per minute")  # Rate limit market data access
@public_endpoint
def get_websocket_ticker():
    """Get latest ticker data from WebSocket"""
    if latest_ticker_data:
        return jsonify(latest_ticker_data)
    else:
        return jsonify({
            "error": "No ticker data available",
            "connected": ws_connection_status["connected"]
        }), 503


# Application startup
if __name__ == "__main__":
    # 🚀 SUPABASE STARTUP VERIFICATION
    logger.info("=" * 60)
    logger.info("🚀 CRYPTO TRADING BOT - SUPABASE INTEGRATED VERSION")
    logger.info("=" * 60)
    
    # Verify all services are working
    try:
        logger.info("🔍 Performing startup health checks...")
        
        # Check database
        if not simple_db.health_check():
            logger.error("❌ STARTUP FAILED: Supabase database not available")
            exit(1)
        
        # Check services
        risk_summary = services["risk_manager"].get_risk_summary()
        logger.info(f"🛡️ Risk Manager: P&L={risk_summary['daily_pnl']}, Trading={risk_summary['trading_allowed']}")
        
        stats = services["database"].get_trading_stats()
        logger.info(f"📊 Database: {stats['total_trades']} trades, {stats['active_positions']} positions")
        
        logger.info("✅ All services healthy - Starting application...")
        
    except Exception as e:
        logger.error(f"❌ STARTUP FAILED: {e}")
        exit(1)
    
    # Initialize WebSocket
    init_bitfinex_websocket()
    
    # Start Flask application
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("ENVIRONMENT") != "production"
    
    logger.info(f"🌐 Starting Flask app on port {port} (debug={debug})")
    logger.info("🚀 Application ready with persistent Supabase storage!")
    
    app.run(host="0.0.0.0", port=port, debug=debug)