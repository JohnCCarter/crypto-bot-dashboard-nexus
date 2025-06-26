"""
backend.routes package.
"""

# This file makes backend/routes a Python package

"""Route factory for centralized blueprint registration."""

from flask import Flask

from backend.routes import market_data
from backend.routes.backtest import backtest_bp
from backend.routes.balances import register as register_balances
from backend.routes.bot_control import register as register_bot_control
from backend.routes.config import register as register_config
from backend.routes.live_portfolio import live_portfolio_bp
from backend.routes.orders import register as register_orders
from backend.routes.positions import register as register_positions
from backend.routes.status import status_bp
from backend.routes.strategy_analysis import strategy_analysis_bp


def register_all_routes(app: Flask) -> None:
    """
    Register all API routes and blueprints in a centralized manner.

    Args:
        app: Flask application instance

    This function eliminates duplicate registrations and provides
    a single point of truth for all route configuration.
    """
    # Register function-based routes (legacy pattern)
    register_balances(app)
    register_bot_control(app)
    register_orders(app)
    register_positions(app)
    register_config(app)
    market_data.register(app)

    # Register blueprint-based routes
    app.register_blueprint(status_bp)
    app.register_blueprint(backtest_bp)
    app.register_blueprint(strategy_analysis_bp)
    app.register_blueprint(live_portfolio_bp)


def get_registered_routes(app: Flask) -> dict:
    """
    Get summary of all registered routes for debugging/documentation.

    Args:
        app: Flask application instance

    Returns:
        Dict containing route information grouped by blueprint
    """
    routes_info = {"function_routes": [], "blueprint_routes": {}, "total_routes": 0}

    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith("static"):
            continue

        route_info = {
            "endpoint": rule.endpoint,
            "methods": list((rule.methods or set()) - {"HEAD", "OPTIONS"}),
            "rule": str(rule),
        }

        if "." in rule.endpoint:
            blueprint_name = rule.endpoint.split(".")[0]
            if blueprint_name not in routes_info["blueprint_routes"]:
                routes_info["blueprint_routes"][blueprint_name] = []
            routes_info["blueprint_routes"][blueprint_name].append(route_info)
        else:
            routes_info["function_routes"].append(route_info)

        routes_info["total_routes"] += 1

    return routes_info
