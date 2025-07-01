"""Configuration service for loading and managing trading bot settings."""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.services.portfolio_manager import StrategyWeight


@dataclass
class TradingConfig:
    """Main trading configuration container."""

    risk_config: Dict[str, Any]
    strategy_config: Dict[str, Any]
    portfolio_strategies: Dict[str, Any]
    probability_settings: Dict[str, Any]
    trading_window: Dict[str, Any]
    notifications: Dict[str, Any]


class ConfigService:
    """Service for managing trading bot configuration."""

    def __init__(self, config_file: str = "backend/config.json"):
        """
        Initialize configuration service.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self._config_cache: Optional[Dict[str, Any]] = None

    def load_config(self, force_reload: bool = False) -> TradingConfig:
        """
        Load configuration from file with caching.

        Args:
            force_reload: Force reload from file even if cached

        Returns:
            TradingConfig object with all settings
        """
        if self._config_cache is None or force_reload:
            self._config_cache = self._load_from_file()

        return self._parse_config(self._config_cache)

    async def load_config_async(self, force_reload: bool = False) -> TradingConfig:
        """
        Asynkron version av load_config.
        
        Load configuration from file with caching.
        This async function currently wraps the synchronous implementation
        but can be updated to use async file operations in the future.

        Args:
            force_reload: Force reload from file even if cached

        Returns:
            TradingConfig object with all settings
        """
        # För närvarande, använd den synkrona implementationen
        # Detta kan uppdateras i framtiden för asynkrona filoperationer
        return self.load_config(force_reload)

    def _load_from_file(self) -> Dict[str, Any]:
        """Load raw configuration from JSON file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.logger.info(f"Loaded configuration from {self.config_file}")
                    return config
            else:
                self.logger.warning(f"Config file {self.config_file} not found")
                return self._get_default_config()

        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to load config file: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration as fallback."""
        return {
            "risk": {
                "max_position_size": 0.1,
                "max_leverage": 3.0,
                "stop_loss_percent": 2.0,
                "take_profit_percent": 4.0,
                "max_daily_loss": 5.0,
                "max_open_positions": 5,
                "min_signal_confidence": 0.6,
                "probability_weight": 0.5,
                "risk_per_trade": 0.02,
                "lookback": 5,
            },
            "strategy": {
                "symbol": "BTC/USD",
                "timeframe": "1h",
                "ema_fast": 12,
                "ema_slow": 26,
                "rsi_period": 14,
            },
            "trading_window": {
                "start_hour": 0,
                "end_hour": 24,
                "max_trades_per_day": 5,
            },
            "notifications": {"email_enabled": False},
            "portfolio_strategies": {
                "ema_crossover": {
                    "enabled": True,
                    "weight": 0.4,
                    "min_confidence": 0.6,
                },
                "rsi": {"enabled": True, "weight": 0.3, "min_confidence": 0.5},
                "fvg": {"enabled": False, "weight": 0.2, "min_confidence": 0.5},
            },
            "probability_settings": {
                "confidence_threshold_buy": 0.7,
                "confidence_threshold_sell": 0.7,
                "confidence_threshold_hold": 0.6,
                "risk_score_threshold": 0.8,
                "combination_method": "weighted_average",
                "enable_dynamic_weights": True,
            },
        }

    def _parse_config(self, raw_config: Dict[str, Any]) -> TradingConfig:
        """Parse raw configuration into structured format."""
        return TradingConfig(
            risk_config=raw_config.get("risk", {}),
            strategy_config=raw_config.get("strategy", {}),
            portfolio_strategies=raw_config.get("portfolio_strategies", {}),
            probability_settings=raw_config.get("probability_settings", {}),
            trading_window=raw_config.get("trading_window", {}),
            notifications=raw_config.get("notifications", {}),
        )

    def get_strategy_weights(self) -> List[StrategyWeight]:
        """
        Get strategy weights for portfolio manager.

        Returns:
            List of StrategyWeight objects
        """
        config = self.load_config()
        strategy_weights = []

        for strategy_name, strategy_config in config.portfolio_strategies.items():
            if isinstance(strategy_config, dict):
                weight = StrategyWeight(
                    strategy_name=strategy_name,
                    weight=strategy_config.get("weight", 0.25),
                    min_confidence=strategy_config.get("min_confidence", 0.5),
                    enabled=strategy_config.get("enabled", True),
                )
                strategy_weights.append(weight)

        # Ensure weights sum to 1.0 for enabled strategies
        enabled_weights = [sw for sw in strategy_weights if sw.enabled]
        if enabled_weights:
            total_weight = sum(sw.weight for sw in enabled_weights)
            if total_weight > 0:
                for sw in enabled_weights:
                    sw.weight = sw.weight / total_weight

        return strategy_weights

    async def get_strategy_weights_async(self) -> List[StrategyWeight]:
        """
        Asynkron version av get_strategy_weights.
        
        Get strategy weights for portfolio manager.
        This async function currently wraps the synchronous implementation.

        Returns:
            List of StrategyWeight objects
        """
        # Wrappa synkrona funktionen
        return self.get_strategy_weights()

    def get_strategy_params(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get parameters for a specific strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Dict with strategy parameters
        """
        config = self.load_config()

        # Get base strategy config
        base_params = config.strategy_config.copy()

        # Get strategy-specific config
        strategy_config = config.portfolio_strategies.get(strategy_name, {})

        # Merge with base parameters
        strategy_params = base_params.copy()
        strategy_params.update(strategy_config)

        return strategy_params

    async def get_strategy_params_async(self, strategy_name: str) -> Dict[str, Any]:
        """
        Asynkron version av get_strategy_params.
        
        Get parameters for a specific strategy.
        This async function currently wraps the synchronous implementation.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Dict with strategy parameters
        """
        # Wrappa synkrona funktionen
        return self.get_strategy_params(strategy_name)

    def update_strategy_weight(self, strategy_name: str, new_weight: float) -> bool:
        """
        Update strategy weight in configuration.

        Args:
            strategy_name: Name of strategy to update
            new_weight: New weight value (0.0 - 1.0)

        Returns:
            True if successful, False otherwise
        """
        try:
            config = self._load_from_file()

            if "portfolio_strategies" not in config:
                config["portfolio_strategies"] = {}

            if strategy_name not in config["portfolio_strategies"]:
                self.logger.warning(f"Strategy {strategy_name} not found in config")
                return False

            config["portfolio_strategies"][strategy_name]["weight"] = new_weight

            # Save back to file
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            # Clear cache to force reload
            self._config_cache = None

            self.logger.info(f"Updated {strategy_name} weight to {new_weight}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update strategy weight: {e}")
            return False

    async def update_strategy_weight_async(self, strategy_name: str, new_weight: float) -> bool:
        """
        Asynkron version av update_strategy_weight.
        
        Update strategy weight in configuration.
        This async function currently wraps the synchronous implementation.

        Args:
            strategy_name: Name of strategy to update
            new_weight: New weight value (0.0 - 1.0)

        Returns:
            True if successful, False otherwise
        """
        # Wrappa synkrona funktionen
        return self.update_strategy_weight(strategy_name, new_weight)

    def update_probability_settings(self, new_settings: Dict[str, Any]) -> bool:
        """
        Update probability settings in configuration.

        Args:
            new_settings: New probability settings

        Returns:
            True if successful, False otherwise
        """
        try:
            config = self._load_from_file()

            if "probability_settings" not in config:
                config["probability_settings"] = {}

            config["probability_settings"].update(new_settings)

            # Save back to file
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            # Clear cache to force reload
            self._config_cache = None

            self.logger.info(f"Updated probability settings: {new_settings}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update probability settings: {e}")
            return False

    async def update_probability_settings_async(self, new_settings: Dict[str, Any]) -> bool:
        """
        Asynkron version av update_probability_settings.
        
        Update probability settings in configuration.
        This async function currently wraps the synchronous implementation.

        Args:
            new_settings: New probability settings

        Returns:
            True if successful, False otherwise
        """
        # Wrappa synkrona funktionen
        return self.update_probability_settings(new_settings)

    def validate_config(self) -> List[str]:
        """
        Validate current configuration and return any errors.

        Returns:
            List of validation error messages
        """
        errors = []

        try:
            config = self.load_config()

            # Validate risk settings
            risk = config.risk_config
            if (
                risk.get("max_position_size", 0) <= 0
                or risk.get("max_position_size", 0) > 1
            ):
                errors.append("max_position_size must be between 0 and 1")

            if risk.get("max_leverage", 0) < 1:
                errors.append("max_leverage must be >= 1")

            # Validate strategy weights
            enabled_strategies = [
                name
                for name, cfg in config.portfolio_strategies.items()
                if cfg.get("enabled", False)
            ]

            if not enabled_strategies:
                errors.append("At least one strategy must be enabled")

            total_weight = sum(
                cfg.get("weight", 0)
                for cfg in config.portfolio_strategies.values()
                if cfg.get("enabled", False)
            )

            if abs(total_weight - 1.0) > 0.01:  # Allow small rounding errors
                errors.append(f"Strategy weights should sum to 1.0, got {total_weight}")

            # Validate probability settings
            prob = config.probability_settings
            for threshold in [
                "confidence_threshold_buy",
                "confidence_threshold_sell",
                "confidence_threshold_hold",
            ]:
                value = prob.get(threshold, 0)
                if value < 0 or value > 1:
                    errors.append(f"{threshold} must be between 0 and 1")

        except Exception as e:
            errors.append(f"Configuration validation failed: {str(e)}")

        return errors

    async def validate_config_async(self) -> List[str]:
        """
        Asynkron version av validate_config.
        
        Validate current configuration and return any errors.
        This async function currently wraps the synchronous implementation.

        Returns:
            List of validation error messages
        """
        # Wrappa synkrona funktionen
        return self.validate_config()

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration.

        Returns:
            Dict with configuration summary
        """
        try:
            config = self.load_config()
            validation_errors = self.validate_config()

            enabled_strategies = [
                name
                for name, cfg in config.portfolio_strategies.items()
                if cfg.get("enabled", False)
            ]

            return {
                "config_file": self.config_file,
                "config_valid": len(validation_errors) == 0,
                "validation_errors": validation_errors,
                "enabled_strategies": enabled_strategies,
                "total_strategy_count": len(config.portfolio_strategies),
                "risk_management": {
                    "max_position_size": config.risk_config.get("max_position_size"),
                    "min_signal_confidence": config.risk_config.get(
                        "min_signal_confidence"
                    ),
                    "probability_weight": config.risk_config.get("probability_weight"),
                },
                "probability_framework": {
                    "combination_method": config.probability_settings.get(
                        "combination_method"
                    ),
                    "dynamic_weights_enabled": config.probability_settings.get(
                        "enable_dynamic_weights"
                    ),
                    "risk_threshold": config.probability_settings.get(
                        "risk_score_threshold"
                    ),
                },
            }

        except Exception as e:
            return {
                "config_file": self.config_file,
                "config_valid": False,
                "error": str(e),
            }

    async def get_config_summary_async(self) -> Dict[str, Any]:
        """
        Asynkron version av get_config_summary.
        
        Get a summary of current configuration.
        This async function currently wraps the synchronous implementation.

        Returns:
            Dict with configuration summary
        """
        # Wrappa synkrona funktionen
        return self.get_config_summary()
