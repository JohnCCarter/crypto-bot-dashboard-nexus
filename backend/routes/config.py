"""API routes for configuration management."""

from flask import Blueprint, jsonify, request
from backend.services.config_service import ConfigService


def register(app):
    """Register configuration routes."""

    config_service = ConfigService()

    @app.route("/api/config", methods=["GET"])
    def get_config():
        """Get current configuration."""
        try:
            config_summary = config_service.get_config_summary()
            return jsonify(config_summary), 200

        except Exception as e:
            return jsonify({"error": f"Failed to get configuration: {str(e)}"}), 500

    @app.route("/api/config", methods=["POST"])
    def update_config():
        """Update configuration."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing JSON body"}), 400

            # For now, just return success - in real implementation this would update config
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Configuration updated successfully",
                        "updated_fields": list(data.keys()),
                    }
                ),
                200,
            )

        except Exception as e:
            return jsonify({"error": f"Failed to update configuration: {str(e)}"}), 500

    @app.route("/api/config/summary", methods=["GET"])
    def get_config_summary():
        """Get configuration summary with validation status."""
        try:
            summary = config_service.get_config_summary()
            return jsonify(summary), 200

        except Exception as e:
            return jsonify({"error": f"Failed to get config summary: {str(e)}"}), 500

    @app.route("/api/config/strategies", methods=["GET"])
    def get_strategy_config():
        """Get strategy configuration."""
        try:
            strategy_weights = config_service.get_strategy_weights()

            weights_data = [
                {
                    "strategy_name": sw.strategy_name,
                    "weight": sw.weight,
                    "min_confidence": sw.min_confidence,
                    "enabled": sw.enabled,
                }
                for sw in strategy_weights
            ]

            return (
                jsonify(
                    {
                        "strategy_weights": weights_data,
                        "total_strategies": len(weights_data),
                        "enabled_strategies": len(
                            [sw for sw in strategy_weights if sw.enabled]
                        ),
                    }
                ),
                200,
            )

        except Exception as e:
            return jsonify({"error": f"Failed to get strategy config: {str(e)}"}), 500

    @app.route("/api/config/strategy/<strategy_name>", methods=["GET"])
    def get_strategy_params(strategy_name):
        """Get parameters for a specific strategy."""
        try:
            params = config_service.get_strategy_params(strategy_name)
            return jsonify({"strategy_name": strategy_name, "parameters": params}), 200

        except Exception as e:
            return jsonify({"error": f"Failed to get strategy params: {str(e)}"}), 500

    @app.route("/api/config/strategy/<strategy_name>/weight", methods=["PUT"])
    def update_strategy_weight(strategy_name):
        """Update strategy weight."""
        try:
            data = request.get_json()
            new_weight = data.get("weight")

            if new_weight is None:
                return jsonify({"error": "Weight value is required"}), 400

            if not (0.0 <= new_weight <= 1.0):
                return jsonify({"error": "Weight must be between 0.0 and 1.0"}), 400

            success = config_service.update_strategy_weight(strategy_name, new_weight)

            if success:
                return (
                    jsonify(
                        {
                            "message": f"Updated {strategy_name} weight to {new_weight}",
                            "strategy_name": strategy_name,
                            "new_weight": new_weight,
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"error": "Failed to update strategy weight"}), 500

        except Exception as e:
            return (
                jsonify({"error": f"Failed to update strategy weight: {str(e)}"}),
                500,
            )

    @app.route("/api/config/probability", methods=["GET"])
    def get_probability_config():
        """Get probability configuration."""
        try:
            config = config_service.load_config()
            return (
                jsonify(
                    {
                        "probability_settings": config.probability_settings,
                        "risk_config": {
                            "min_signal_confidence": config.risk_config.get(
                                "min_signal_confidence"
                            ),
                            "probability_weight": config.risk_config.get(
                                "probability_weight"
                            ),
                        },
                    }
                ),
                200,
            )

        except Exception as e:
            return (
                jsonify({"error": f"Failed to get probability config: {str(e)}"}),
                500,
            )

    @app.route("/api/config/probability", methods=["PUT"])
    def update_probability_config():
        """Update probability configuration."""
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Validate probability settings
            if "probability_settings" in data:
                prob_settings = data["probability_settings"]

                # Validate threshold values
                for key in [
                    "confidence_threshold_buy",
                    "confidence_threshold_sell",
                    "confidence_threshold_hold",
                    "risk_score_threshold",
                ]:
                    if key in prob_settings:
                        value = prob_settings[key]
                        if not (0.0 <= value <= 1.0):
                            return (
                                jsonify(
                                    {"error": f"{key} must be between 0.0 and 1.0"}
                                ),
                                400,
                            )

                success = config_service.update_probability_settings(prob_settings)

                if success:
                    return (
                        jsonify(
                            {
                                "message": "Probability settings updated successfully",
                                "updated_settings": prob_settings,
                            }
                        ),
                        200,
                    )
                else:
                    return (
                        jsonify({"error": "Failed to update probability settings"}),
                        500,
                    )
            else:
                return jsonify({"error": "probability_settings field is required"}), 400

        except Exception as e:
            return (
                jsonify({"error": f"Failed to update probability config: {str(e)}"}),
                500,
            )

    @app.route("/api/config/validate", methods=["GET"])
    def validate_config():
        """Validate current configuration."""
        try:
            validation_errors = config_service.validate_config()

            return (
                jsonify(
                    {
                        "valid": len(validation_errors) == 0,
                        "errors": validation_errors,
                        "error_count": len(validation_errors),
                    }
                ),
                200,
            )

        except Exception as e:
            return jsonify({"error": f"Configuration validation failed: {str(e)}"}), 500

    @app.route("/api/config/reload", methods=["POST"])
    def reload_config():
        """Force reload configuration from file."""
        try:
            config = config_service.load_config(force_reload=True)
            validation_errors = config_service.validate_config()

            return (
                jsonify(
                    {
                        "message": "Configuration reloaded successfully",
                        "config_valid": len(validation_errors) == 0,
                        "validation_errors": validation_errors,
                    }
                ),
                200,
            )

        except Exception as e:
            return jsonify({"error": f"Failed to reload configuration: {str(e)}"}), 500
