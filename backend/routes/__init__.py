"""
backend.routes package.

Route factory for centralized blueprint registration.
"""

# This file makes backend/routes a Python package

# from backend.routes import market_data
# from backend.routes.bot_control import register as register_bot_control


def register_all_routes(app: Flask) -> None:
    """
    Register all API routes and blueprints in a centralized manner.

    Args:
        app: Flask application instance

    This function eliminates duplicate registrations and provides
    a single point of truth for all route configuration.
    """
    # Register function-based routes (legacy pattern)
    # register_bot_control(app)
    # market_data.register(app)

    # Register blueprint-based routes
    # app.register_blueprint(live_portfolio_bp)


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
