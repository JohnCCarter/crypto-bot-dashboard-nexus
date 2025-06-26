"""
Live Portfolio API Routes - Exponerar live portfolio data med marknadsinfo
"""

import logging
import os

from flask import Blueprint, jsonify, request

from backend.services.live_data_service import LiveDataService
from backend.services.live_portfolio_service import LivePortfolioService

logger = logging.getLogger(__name__)

# Create blueprint
live_portfolio_bp = Blueprint("live_portfolio", __name__)


@live_portfolio_bp.route("/api/live-portfolio/snapshot", methods=["GET"])
def get_live_portfolio_snapshot():
    """
    Hämta komplett portfolio snapshot med live marknadsdata

    Query params:
        symbols: Comma-separated list of symbols (optional)

    Returns:
        JSON with live portfolio data
    """
    try:
        logger.info("📊 [API] GET /api/live-portfolio/snapshot")

        # Get query parameters
        symbols_param = request.args.get("symbols")
        symbols = symbols_param.split(",") if symbols_param else None

        # Initialize services
        exchange_config = {
            "exchange_id": "bitfinex",
            "api_key": os.getenv("BITFINEX_API_KEY"),
            "api_secret": os.getenv("BITFINEX_API_SECRET"),
        }

        live_portfolio = LivePortfolioService(exchange_config)

        # Get live snapshot
        snapshot = live_portfolio.get_live_portfolio_snapshot(symbols)

        # Convert to JSON-serializable format
        positions_data = []
        for pos in snapshot.positions:
            positions_data.append(
                {
                    "symbol": pos.symbol,
                    "amount": pos.amount,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_pct": pos.unrealized_pnl_pct,
                    "market_value": pos.market_value,
                    "timestamp": pos.timestamp.isoformat(),
                }
            )

        response_data = {
            "total_value": snapshot.total_value,
            "available_balance": snapshot.available_balance,
            "positions": positions_data,
            "total_unrealized_pnl": snapshot.total_unrealized_pnl,
            "total_unrealized_pnl_pct": snapshot.total_unrealized_pnl_pct,
            "timestamp": snapshot.timestamp.isoformat(),
            "market_data_quality": snapshot.market_data_quality,
            "status": "success",
        }

        logger.info(
            f"✅ [API] Portfolio snapshot returned: ${snapshot.total_value:.2f} total value"
        )

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"❌ [API] Error getting portfolio snapshot: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@live_portfolio_bp.route("/api/live-portfolio/position-value", methods=["GET"])
def get_position_value():
    """
    Beräkna värde för specifik position med live pricing

    Query params:
        symbol: Trading pair (e.g., 'BTC/USD')
        amount: Position amount

    Returns:
        JSON with position valuation
    """
    try:
        logger.info("💰 [API] GET /api/live-portfolio/position-value")

        # Get query parameters
        symbol = request.args.get("symbol")
        amount = request.args.get("amount")

        if not symbol or not amount:
            return (
                jsonify(
                    {
                        "error": "Missing required parameters: symbol, amount",
                        "status": "error",
                    }
                ),
                400,
            )

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"error": "Invalid amount format", "status": "error"}), 400

        # Initialize services
        exchange_config = {
            "exchange_id": "bitfinex",
            "api_key": os.getenv("BITFINEX_API_KEY"),
            "api_secret": os.getenv("BITFINEX_API_SECRET"),
        }

        live_portfolio = LivePortfolioService(exchange_config)

        # Calculate position value
        position_value = live_portfolio.get_position_value(symbol, amount)
        position_value["status"] = "success"

        logger.info(
            f"✅ [API] Position value calculated: ${position_value['market_value']:.2f}"
        )

        return jsonify(position_value)

    except Exception as e:
        logger.error(f"❌ [API] Error calculating position value: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@live_portfolio_bp.route("/api/live-portfolio/validate-trade", methods=["POST"])
def validate_trade():
    """
    Validera om en trade kan utföras baserat på live portfolio

    JSON body:
        symbol: Trading pair
        amount: Trade amount
        type: 'buy' or 'sell'

    Returns:
        JSON with validation results
    """
    try:
        logger.info("🔍 [API] POST /api/live-portfolio/validate-trade")

        # Get JSON data
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided", "status": "error"}), 400

        symbol = data.get("symbol")
        amount = data.get("amount")
        trade_type = data.get("type")

        if not all([symbol, amount, trade_type]):
            return (
                jsonify(
                    {
                        "error": "Missing required fields: symbol, amount, type",
                        "status": "error",
                    }
                ),
                400,
            )

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"error": "Invalid amount format", "status": "error"}), 400

        if trade_type not in ["buy", "sell"]:
            return (
                jsonify(
                    {
                        "error": 'Invalid trade type. Must be "buy" or "sell"',
                        "status": "error",
                    }
                ),
                400,
            )

        # Initialize services
        exchange_config = {
            "exchange_id": "bitfinex",
            "api_key": os.getenv("BITFINEX_API_KEY"),
            "api_secret": os.getenv("BITFINEX_API_SECRET"),
        }

        live_portfolio = LivePortfolioService(exchange_config)

        # Validate trade
        validation_result = live_portfolio.validate_trading_capacity(
            symbol, amount, trade_type
        )
        validation_result["status"] = "success"

        logger.info(
            f"✅ [API] Trade validation: {validation_result['valid']} - {validation_result['reason']}"
        )

        return jsonify(validation_result)

    except Exception as e:
        logger.error(f"❌ [API] Error validating trade: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@live_portfolio_bp.route("/api/live-portfolio/performance", methods=["GET"])
def get_performance_metrics():
    """
    Hämta portfolio performance metrics med live data

    Query params:
        timeframe: Time period (optional, default: '24h')

    Returns:
        JSON with performance metrics
    """
    try:
        logger.info("📊 [API] GET /api/live-portfolio/performance")

        # Get query parameters
        timeframe = request.args.get("timeframe", "24h")

        # Initialize services
        exchange_config = {
            "exchange_id": "bitfinex",
            "api_key": os.getenv("BITFINEX_API_KEY"),
            "api_secret": os.getenv("BITFINEX_API_SECRET"),
        }

        live_portfolio = LivePortfolioService(exchange_config)

        # Get performance metrics
        metrics = live_portfolio.get_portfolio_performance_metrics(timeframe)
        metrics["status"] = "success"

        logger.info(f"✅ [API] Performance metrics calculated for {timeframe}")

        return jsonify(metrics)

    except Exception as e:
        logger.error(f"❌ [API] Error getting performance metrics: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@live_portfolio_bp.route("/api/live-portfolio/market-overview", methods=["GET"])
def get_market_overview():
    """
    Hämta marknadsöversikt för alla tradade symboler

    Query params:
        symbols: Comma-separated list of symbols (optional)

    Returns:
        JSON with market overview data
    """
    try:
        logger.info("🌍 [API] GET /api/live-portfolio/market-overview")

        # Get query parameters
        symbols_param = request.args.get("symbols")
        symbols = symbols_param.split(",") if symbols_param else ["BTC/USD", "ETH/USD"]

        # Initialize service
        exchange_config = {
            "exchange_id": "bitfinex",
            "api_key": os.getenv("BITFINEX_API_KEY"),
            "api_secret": os.getenv("BITFINEX_API_SECRET"),
        }

        live_data = LiveDataService(
            exchange_id=exchange_config["exchange_id"],
            api_key=exchange_config["api_key"],
            api_secret=exchange_config["api_secret"],
        )

        # Get market context for each symbol
        market_overview = []

        for symbol in symbols:
            try:
                market_context = live_data.get_live_market_context(
                    symbol, timeframe="5m", limit=50
                )

                overview_data = {
                    "symbol": symbol,
                    "current_price": market_context["current_price"],
                    "best_bid": market_context["best_bid"],
                    "best_ask": market_context["best_ask"],
                    "spread": market_context["spread"],
                    "volume_24h": market_context["volume_24h"],
                    "price_change_24h": market_context.get("price_change_24h", 0),
                    "price_change_pct": market_context.get("price_change_pct", 0),
                    "volatility_pct": market_context["volatility_pct"],
                    "data_quality": market_context["data_quality"],
                    "timestamp": market_context["timestamp"],
                }

                market_overview.append(overview_data)

            except Exception as e:
                logger.error(f"❌ [API] Failed to get market data for {symbol}: {e}")
                # Add error entry
                market_overview.append(
                    {"symbol": symbol, "error": str(e), "timestamp": None}
                )

        response_data = {
            "market_overview": market_overview,
            "status": "success",
            "timestamp": (
                market_overview[0]["timestamp"]
                if market_overview and market_overview[0].get("timestamp")
                else None
            ),
        }

        logger.info(f"✅ [API] Market overview returned for {len(symbols)} symbols")

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"❌ [API] Error getting market overview: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500
