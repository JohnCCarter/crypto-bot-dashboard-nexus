"""Portfolio management service for combining multiple strategy signals."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from backend.services.risk_manager import RiskManager, ProbabilityData
from backend.strategies.sample_strategy import TradeSignal


@dataclass
class StrategyWeight:
    """Weight configuration for a strategy."""

    strategy_name: str
    weight: float  # 0.0 to 1.0
    min_confidence: float = 0.5
    enabled: bool = True


@dataclass
class CombinedSignal:
    """Combined signal from multiple strategies."""

    action: str  # 'buy', 'sell', 'hold'
    combined_confidence: float
    combined_probabilities: ProbabilityData
    individual_signals: Dict[str, TradeSignal]
    metadata: Dict[str, Any]


class PortfolioManager:
    """Service for managing portfolio with multiple strategies."""

    def __init__(
        self, risk_manager: RiskManager, strategy_weights: List[StrategyWeight]
    ):
        """
        Initialize portfolio manager.

        Args:
            risk_manager: Risk management service
            strategy_weights: List of strategy configurations with weights
        """
        self.risk_manager = risk_manager
        self.strategy_weights = {sw.strategy_name: sw for sw in strategy_weights}
        self._validate_weights()

    def _validate_weights(self):
        """Validate that strategy weights sum to reasonable values."""
        enabled_weights = [
            sw.weight for sw in self.strategy_weights.values() if sw.enabled
        ]
        total_weight = sum(enabled_weights)

        if total_weight > 1.1 or total_weight < 0.9:
            logging.warning(
                f"Strategy weights sum to {total_weight:.2f}, consider normalizing"
            )

    def combine_strategy_signals(
        self,
        strategy_signals: Dict[str, TradeSignal],
        symbol: str,
        current_price: float,
    ) -> CombinedSignal:
        """
        Combine signals from multiple strategies into a single decision.

        Args:
            strategy_signals: Dict of strategy_name -> TradeSignal
            symbol: Trading symbol
            current_price: Current price for the symbol

        Returns:
            CombinedSignal with combined probabilities and action
        """
        if not strategy_signals:
            return self._create_hold_signal("No strategy signals provided")

        # Filter valid signals and apply weights
        valid_signals = {}
        weighted_buy_prob = 0.0
        weighted_sell_prob = 0.0
        weighted_hold_prob = 0.0
        weighted_confidence = 0.0
        total_weight = 0.0

        for strategy_name, signal in strategy_signals.items():
            if strategy_name not in self.strategy_weights:
                logging.warning(f"Unknown strategy: {strategy_name}")
                continue

            weight_config = self.strategy_weights[strategy_name]

            if not weight_config.enabled:
                continue

            if signal.confidence < weight_config.min_confidence:
                logging.info(f"Signal from {strategy_name} below minimum confidence")
                continue

            # Extract probabilities from signal metadata
            metadata = signal.metadata or {}
            prob_buy = metadata.get("probability_buy", 0.33)
            prob_sell = metadata.get("probability_sell", 0.33)
            prob_hold = metadata.get("probability_hold", 0.34)

            # Apply strategy weight
            weight = weight_config.weight
            weighted_buy_prob += prob_buy * weight
            weighted_sell_prob += prob_sell * weight
            weighted_hold_prob += prob_hold * weight
            weighted_confidence += signal.confidence * weight
            total_weight += weight

            valid_signals[strategy_name] = signal

        if total_weight == 0:
            return self._create_hold_signal("No valid signals after filtering")

        # Normalize probabilities
        if total_weight > 0:
            combined_buy_prob = weighted_buy_prob / total_weight
            combined_sell_prob = weighted_sell_prob / total_weight
            combined_hold_prob = weighted_hold_prob / total_weight
            combined_confidence = weighted_confidence / total_weight
        else:
            combined_buy_prob = combined_sell_prob = 0.33
            combined_hold_prob = 0.34
            combined_confidence = 0.0

        # Determine final action
        probabilities = [
            ("buy", combined_buy_prob),
            ("sell", combined_sell_prob),
            ("hold", combined_hold_prob),
        ]

        # Choose action with highest probability
        final_action = max(probabilities, key=lambda x: x[1])[0]

        # Create combined probability data
        combined_prob_data = ProbabilityData(
            probability_buy=combined_buy_prob,
            probability_sell=combined_sell_prob,
            probability_hold=combined_hold_prob,
            confidence=combined_confidence,
        )

        metadata = {
            "symbol": symbol,
            "current_price": current_price,
            "strategies_used": list(valid_signals.keys()),
            "total_weight": total_weight,
            "combination_method": "weighted_average",
            "timestamp": datetime.now().isoformat(),
        }

        return CombinedSignal(
            action=final_action,
            combined_confidence=combined_confidence,
            combined_probabilities=combined_prob_data,
            individual_signals=valid_signals,
            metadata=metadata,
        )

    def calculate_portfolio_position_size(
        self,
        combined_signal: CombinedSignal,
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
        symbol: str,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate position size for the combined signal.

        Args:
            combined_signal: Combined signal from multiple strategies
            portfolio_value: Current portfolio value
            current_positions: Current open positions
            symbol: Trading symbol

        Returns:
            Tuple of (position_size, calculation_metadata)
        """
        # Use intelligent position sizing with combined probabilities
        position_size, metadata = self.risk_manager.calculate_intelligent_position_size(
            signal_confidence=combined_signal.combined_confidence,
            portfolio_value=portfolio_value,
            current_positions=current_positions,
            probability_data=combined_signal.combined_probabilities,
        )

        # Add portfolio-specific metadata
        metadata.update(
            {
                "symbol": symbol,
                "combined_signal_action": combined_signal.action,
                "strategies_count": len(combined_signal.individual_signals),
                "portfolio_diversification_factor": self._calculate_diversification_factor(
                    current_positions
                ),
            }
        )

        return position_size, metadata

    def _calculate_diversification_factor(
        self, current_positions: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate diversification factor based on current positions."""
        if not current_positions:
            return 1.0

        # Simple diversification: more positions = lower individual position size
        position_count = len(current_positions)
        max_positions = self.risk_manager.params.max_open_positions

        diversification_factor = max(0.5, 1.0 - (position_count / max_positions) * 0.5)
        return diversification_factor

    def should_execute_trade(
        self,
        combined_signal: CombinedSignal,
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
        symbol: str,
        current_price: float,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if a trade should be executed based on combined signal and risk management.

        Args:
            combined_signal: Combined signal from strategies
            portfolio_value: Current portfolio value
            current_positions: Current open positions
            symbol: Trading symbol
            current_price: Current price

        Returns:
            Tuple of (should_execute, decision_metadata)
        """
        # Create order data for validation
        position_size, size_metadata = self.calculate_portfolio_position_size(
            combined_signal, portfolio_value, current_positions, symbol
        )

        order_data = {
            "amount": position_size / current_price,  # Convert to quantity
            "price": current_price,
            "side": combined_signal.action,
            "leverage": 1.0,
        }

        # Validate with risk manager
        validation = self.risk_manager.validate_order_with_probabilities(
            order_data,
            portfolio_value,
            current_positions,
            combined_signal.combined_probabilities,
        )

        # Additional portfolio-level checks
        portfolio_risk = self.risk_manager.assess_portfolio_risk(current_positions)

        execution_decision = validation["valid"]

        # Override decision based on portfolio risk
        if (
            portfolio_risk["risk_level"] == "high"
            and combined_signal.combined_probabilities.get_risk_score() > 0.6
        ):
            execution_decision = False
            validation["errors"].append(
                "Portfolio risk too high for additional positions"
            )

        decision_metadata = {
            "validation_result": validation,
            "portfolio_risk_assessment": portfolio_risk,
            "position_size_calculation": size_metadata,
            "combined_signal_metadata": combined_signal.metadata,
            "final_decision": execution_decision,
            "decision_timestamp": datetime.now().isoformat(),
        }

        return execution_decision, decision_metadata

    def rebalance_portfolio_weights(self, performance_data: Dict[str, float]):
        """
        Rebalance strategy weights based on recent performance.

        Args:
            performance_data: Dict of strategy_name -> recent_performance_score
        """
        if not performance_data:
            return

        # Simple rebalancing: increase weights for better performing strategies
        for strategy_name, performance in performance_data.items():
            if strategy_name in self.strategy_weights:
                current_weight = self.strategy_weights[strategy_name].weight

                # Adjust weight based on performance (simple linear adjustment)
                adjustment = (performance - 0.5) * 0.1  # ±10% max adjustment
                new_weight = max(0.1, min(0.9, current_weight + adjustment))

                self.strategy_weights[strategy_name].weight = new_weight

                logging.info(
                    f"Adjusted {strategy_name} weight: {current_weight:.2f} -> {new_weight:.2f}"
                )

        # Normalize weights to sum to 1.0
        self._normalize_weights()

    def _normalize_weights(self):
        """Normalize strategy weights to sum to 1.0."""
        enabled_strategies = {
            name: sw for name, sw in self.strategy_weights.items() if sw.enabled
        }

        if not enabled_strategies:
            return

        total_weight = sum(sw.weight for sw in enabled_strategies.values())

        if total_weight > 0:
            for strategy_weight in enabled_strategies.values():
                strategy_weight.weight = strategy_weight.weight / total_weight

    def _create_hold_signal(self, reason: str) -> CombinedSignal:
        """Create a default hold signal."""
        prob_data = ProbabilityData(
            probability_buy=0.2,
            probability_sell=0.2,
            probability_hold=0.6,
            confidence=0.0,
        )

        return CombinedSignal(
            action="hold",
            combined_confidence=0.0,
            combined_probabilities=prob_data,
            individual_signals={},
            metadata={"reason": reason, "timestamp": datetime.now().isoformat()},
        )

    def get_portfolio_summary(
        self, current_positions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary including risk assessment.

        Args:
            current_positions: Current open positions

        Returns:
            Portfolio summary with risk metrics
        """
        portfolio_risk = self.risk_manager.assess_portfolio_risk(current_positions)

        strategy_info = {
            name: {
                "weight": sw.weight,
                "enabled": sw.enabled,
                "min_confidence": sw.min_confidence,
            }
            for name, sw in self.strategy_weights.items()
        }

        return {
            "portfolio_risk": portfolio_risk,
            "strategy_weights": strategy_info,
            "total_strategies": len(self.strategy_weights),
            "enabled_strategies": sum(
                1 for sw in self.strategy_weights.values() if sw.enabled
            ),
            "summary_timestamp": datetime.now().isoformat(),
        }
