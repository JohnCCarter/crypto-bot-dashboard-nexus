"""Risk management service for trading operations."""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Dict, Optional, Tuple


@dataclass
class RiskParameters:
    """Risk management parameters."""

    max_position_size: float  # Maximum position size as fraction of portfolio
    max_leverage: float  # Maximum allowed leverage
    stop_loss_pct: float  # Stop loss percentage
    take_profit_pct: float  # Take profit percentage
    max_daily_loss: float  # Maximum daily loss as fraction of portfolio
    max_open_positions: int  # Maximum number of open positions
    min_signal_confidence: float = 0.6  # Minimum confidence to trade
    probability_weight: float = 0.5  # How much to weight probability vs confidence


@dataclass
class ProbabilityData:
    """Container for strategy probability data."""

    probability_buy: float
    probability_sell: float
    probability_hold: float
    confidence: float

    def get_action_probability(self, action: str) -> float:
        """Get probability for specific action."""
        return {
            "buy": self.probability_buy,
            "sell": self.probability_sell,
            "hold": self.probability_hold,
        }.get(action, 0.0)

    def get_risk_score(self) -> float:
        """Calculate risk score based on probabilities (0-1, lower is safer)."""
        # High confidence + high action probability = lower risk
        max_action_prob = max(self.probability_buy, self.probability_sell)
        risk_score = 1.0 - (self.confidence * max_action_prob)
        return max(0.0, min(1.0, risk_score))


class RiskManager:
    """Service for managing trading risk."""

    def __init__(
        self, risk_params: RiskParameters, persistence_file: str = "daily_pnl.json"
    ):
        """
        Initialize risk manager.

        Args:
            risk_params: Risk management parameters
            persistence_file: File to persist daily PnL data
        """
        self.params = risk_params
        self.persistence_file = persistence_file
        self.daily_pnl = 0.0
        self.current_date = date.today()
        self.open_positions: Dict[str, Dict[str, Any]] = {}

        # Load persisted daily PnL data
        self._load_daily_pnl()

    def _load_daily_pnl(self):
        """Load daily PnL data from persistence file."""
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r") as f:
                    data = json.load(f)
                    saved_date_str = data.get("date", str(date.today()))
                    saved_date = date.fromisoformat(saved_date_str)

                    # Reset if it's a new day
                    if saved_date != self.current_date:
                        self.daily_pnl = 0.0
                        self._save_daily_pnl()
                    else:
                        self.daily_pnl = data.get("daily_pnl", 0.0)
            except (json.JSONDecodeError, KeyError, ValueError):
                # If file is corrupted, start fresh
                self.daily_pnl = 0.0
                self._save_daily_pnl()

    def _save_daily_pnl(self):
        """Save daily PnL data to persistence file."""
        data = {
            "date": str(self.current_date),
            "daily_pnl": self.daily_pnl,
            "last_updated": datetime.now().isoformat(),
        }
        try:
            with open(self.persistence_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            # Log error but don't fail - this is non-critical
            logging.warning(f"Warning: Could not save daily PnL data: {e}")

    def _check_new_day(self):
        """Check if it's a new day and reset daily PnL if needed."""
        today = date.today()
        if today != self.current_date:
            self.current_date = today
            self.daily_pnl = 0.0
            self._save_daily_pnl()

    def validate_order(
        self,
        order_data: Dict[str, Any],
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate order against risk parameters.

        Args:
            order_data: Order data dictionary
            portfolio_value: Current portfolio value
            current_positions: Current open positions

        Returns:
            Dict containing validation result and any errors

        Raises:
            ValueError: If order violates risk parameters
        """
        errors = []

        # Check position size
        position_value = float(order_data["amount"]) * float(order_data.get("price", 0))
        position_size_pct = position_value / portfolio_value

        if position_size_pct > self.params.max_position_size:
            errors.append(
                f"Position size {position_size_pct:.2%} exceeds maximum "
                f"{self.params.max_position_size:.2%}"
            )

        # Check leverage
        leverage = float(order_data.get("leverage", 1.0))
        if leverage > self.params.max_leverage:
            errors.append(
                f"Leverage {leverage}x exceeds maximum {self.params.max_leverage}x"
            )

        # Check number of open positions
        if len(current_positions) >= self.params.max_open_positions:
            errors.append(
                f"Maximum number of open positions ({self.params.max_open_positions}) "
                "exceeded"
            )

        # Check daily loss limit
        if self.daily_pnl < -self.params.max_daily_loss * portfolio_value:
            errors.append("Daily loss limit exceeded")

        return {"valid": len(errors) == 0, "errors": errors}

    def validate_order_with_probabilities(
        self,
        order_data: Dict[str, Any],
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
        probability_data: Optional[ProbabilityData] = None,
    ) -> Dict[str, Any]:
        """
        Enhanced order validation using probability data.

        Args:
            order_data: Order data dictionary
            portfolio_value: Current portfolio value
            current_positions: Current open positions
            probability_data: Strategy probability data

        Returns:
            Dict containing validation result, errors, and risk assessment
        """
        # Start with basic validation
        basic_validation = self.validate_order(
            order_data, portfolio_value, current_positions
        )
        errors = basic_validation["errors"].copy()

        # Add probability-based validation if available
        if probability_data:
            action = order_data.get("side", "").lower()
            action_probability = probability_data.get_action_probability(action)

            # Check minimum confidence
            if probability_data.confidence < self.params.min_signal_confidence:
                errors.append(
                    f"Signal confidence {probability_data.confidence:.2%} below minimum "
                    f"{self.params.min_signal_confidence:.2%}"
                )

            # Check action probability
            if action_probability < 0.5:
                errors.append(
                    f"Low probability for {action} action: {action_probability:.2%}"
                )

            # Calculate risk score
            risk_score = probability_data.get_risk_score()
            if risk_score > 0.7:  # High risk threshold
                errors.append(
                    f"High risk score: {risk_score:.2%} (probability analysis)"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "risk_score": (
                probability_data.get_risk_score() if probability_data else 0.5
            ),
            "confidence": probability_data.confidence if probability_data else 0.0,
        }

    def calculate_intelligent_position_size(
        self,
        signal_confidence: float,
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
        probability_data: Optional[ProbabilityData] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate position size using both confidence and probability data.

        Args:
            signal_confidence: Strategy signal confidence (0-1)
            portfolio_value: Current portfolio value
            current_positions: Current open positions
            probability_data: Strategy probability data

        Returns:
            Tuple of (position_size, metadata)
        """
        # Calculate available portfolio fraction
        used_capital = sum(
            pos.get("size", 0) * pos.get("entry_price", 0)
            for pos in current_positions.values()
        )
        available_capital = portfolio_value - used_capital

        # Base position size from original method
        max_position = available_capital * self.params.max_position_size
        base_position_size = max_position * signal_confidence

        # Apply probability-based adjustments if available
        if probability_data:
            # Combine confidence with probability data
            probability_factor = (
                self.params.probability_weight
                * max(
                    probability_data.probability_buy, probability_data.probability_sell
                )
                + (1 - self.params.probability_weight) * probability_data.confidence
            )

            # Risk adjustment - reduce size for high risk signals
            risk_score = probability_data.get_risk_score()
            risk_adjustment = 1.0 - (
                risk_score * 0.5
            )  # Max 50% reduction for high risk

            adjusted_position_size = (
                base_position_size * probability_factor * risk_adjustment
            )
        else:
            adjusted_position_size = base_position_size
            probability_factor = signal_confidence
            risk_adjustment = 1.0

        metadata = {
            "base_position_size": base_position_size,
            "probability_factor": probability_factor,
            "risk_adjustment": risk_adjustment,
            "final_position_size": adjusted_position_size,
            "risk_score": (
                probability_data.get_risk_score() if probability_data else None
            ),
        }

        return adjusted_position_size, metadata

    def calculate_dynamic_stop_loss(
        self,
        entry_price: float,
        side: str,
        probability_data: Optional[ProbabilityData] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate dynamic stop loss based on confidence and probabilities.

        Args:
            entry_price: Position entry price
            side: 'buy' or 'sell'
            probability_data: Strategy probability data

        Returns:
            Tuple of (stop_loss_price, metadata)
        """
        base_stop_loss = self.calculate_stop_loss(entry_price, side)

        if probability_data:
            # Tighter stop loss for low confidence signals
            confidence_factor = probability_data.confidence
            risk_score = probability_data.get_risk_score()

            # Adjust stop loss based on risk - higher risk = tighter stop
            risk_adjustment = 1.0 + (risk_score * 0.5)  # Up to 50% tighter
            confidence_adjustment = (
                2.0 - confidence_factor
            )  # Lower confidence = tighter

            adjusted_stop_pct = (
                self.params.stop_loss_pct * risk_adjustment * confidence_adjustment
            )
            adjusted_stop_pct = min(adjusted_stop_pct, 0.15)  # Cap at 15%

            if side == "buy":
                dynamic_stop_loss = entry_price * (1 - adjusted_stop_pct)
            else:
                dynamic_stop_loss = entry_price * (1 + adjusted_stop_pct)
        else:
            dynamic_stop_loss = base_stop_loss
            adjusted_stop_pct = self.params.stop_loss_pct
            confidence_factor = 0.5
            risk_adjustment = 1.0

        metadata = {
            "base_stop_loss": base_stop_loss,
            "dynamic_stop_loss": dynamic_stop_loss,
            "adjusted_stop_pct": adjusted_stop_pct,
            "confidence_factor": confidence_factor,
            "risk_adjustment": risk_adjustment,
        }

        return dynamic_stop_loss, metadata

    def calculate_dynamic_take_profit(
        self,
        entry_price: float,
        side: str,
        probability_data: Optional[ProbabilityData] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate dynamic take profit based on confidence and probabilities.

        Args:
            entry_price: Position entry price
            side: 'buy' or 'sell'
            probability_data: Strategy probability data

        Returns:
            Tuple of (take_profit_price, metadata)
        """
        base_take_profit = self.calculate_take_profit(entry_price, side)

        if probability_data:
            # More aggressive take profit for high confidence signals
            confidence_factor = probability_data.confidence

            # Adjust take profit based on confidence - higher confidence = more aggressive
            take_profit_multiplier = 1.0 + (
                confidence_factor * 0.5
            )  # Up to 50% more aggressive

            adjusted_take_profit_pct = (
                self.params.take_profit_pct * take_profit_multiplier
            )
            adjusted_take_profit_pct = min(adjusted_take_profit_pct, 0.3)  # Cap at 30%

            if side == "buy":
                dynamic_take_profit = entry_price * (1 + adjusted_take_profit_pct)
            else:
                dynamic_take_profit = entry_price * (1 - adjusted_take_profit_pct)
        else:
            dynamic_take_profit = base_take_profit
            adjusted_take_profit_pct = self.params.take_profit_pct
            confidence_factor = 0.5

        metadata = {
            "base_take_profit": base_take_profit,
            "dynamic_take_profit": dynamic_take_profit,
            "adjusted_take_profit_pct": adjusted_take_profit_pct,
            "confidence_factor": confidence_factor,
        }

        return dynamic_take_profit, metadata

    def assess_portfolio_risk(
        self,
        current_positions: Dict[str, Dict[str, Any]],
        pending_orders: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Assess overall portfolio risk considering all positions and their probabilities.

        Args:
            current_positions: Current open positions with their probability data
            pending_orders: Pending orders with probability data

        Returns:
            Portfolio risk assessment
        """
        if not current_positions:
            return {
                "overall_risk_score": 0.0,
                "risk_level": "none",
                "recommendations": ["No open positions"],
            }

        risk_scores = []
        total_exposure = 0.0
        recommendations = []

        # Analyze current positions
        for symbol, position in current_positions.items():
            prob_data = position.get("probability_data")
            if prob_data and isinstance(prob_data, dict):
                prob_obj = ProbabilityData(
                    probability_buy=prob_data.get("probability_buy", 0.33),
                    probability_sell=prob_data.get("probability_sell", 0.33),
                    probability_hold=prob_data.get("probability_hold", 0.34),
                    confidence=prob_data.get("confidence", 0.5),
                )
                risk_scores.append(prob_obj.get_risk_score())
            else:
                risk_scores.append(0.5)  # Default medium risk

            position_value = position.get("size", 0) * position.get("entry_price", 0)
            total_exposure += position_value

        # Calculate overall risk metrics
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        max_risk_score = max(risk_scores) if risk_scores else 0.0

        # Determine risk level
        if avg_risk_score < 0.3:
            risk_level = "low"
        elif avg_risk_score < 0.6:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Generate recommendations
        if max_risk_score > 0.8:
            recommendations.append("Consider closing high-risk positions")
        if avg_risk_score > 0.6:
            recommendations.append("Portfolio risk is elevated - reduce position sizes")
        if len(current_positions) > self.params.max_open_positions * 0.8:
            recommendations.append("Approaching maximum position limit")

        return {
            "overall_risk_score": avg_risk_score,
            "max_position_risk_score": max_risk_score,
            "risk_level": risk_level,
            "total_exposure": total_exposure,
            "position_count": len(current_positions),
            "daily_pnl": self.daily_pnl,
            "recommendations": recommendations,
            "position_risks": {
                symbol: {"risk_score": score}
                for symbol, score in zip(current_positions.keys(), risk_scores)
            },
        }

    def calculate_position_size(
        self,
        signal_confidence: float,
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Calculate safe position size based on risk parameters.

        Args:
            signal_confidence: Strategy signal confidence (0-1)
            portfolio_value: Current portfolio value
            current_positions: Current open positions

        Returns:
            Safe position size in base currency
        """
        # Calculate available portfolio fraction
        used_capital = sum(
            pos.get("size", 0) * pos.get("entry_price", 0)
            for pos in current_positions.values()
        )
        available_capital = portfolio_value - used_capital

        # Calculate position size based on confidence and risk parameters
        max_position = available_capital * self.params.max_position_size
        position_size = max_position * signal_confidence

        return position_size

    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Position entry price
            side: 'buy' or 'sell'

        Returns:
            Stop loss price
        """
        if side == "buy":
            return entry_price * (1 - self.params.stop_loss_pct)
        else:
            return entry_price * (1 + self.params.stop_loss_pct)

    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """
        Calculate take profit price.

        Args:
            entry_price: Position entry price
            side: 'buy' or 'sell'

        Returns:
            Take profit price
        """
        if side == "buy":
            return entry_price * (1 + self.params.take_profit_pct)
        else:
            return entry_price * (1 - self.params.take_profit_pct)

    def update_daily_pnl(self, pnl: float):
        """
        Update daily profit/loss.

        Args:
            pnl: Profit/loss amount
        """
        self._check_new_day()
        self.daily_pnl += pnl
        self._save_daily_pnl()

    def reset_daily_pnl(self):
        """Reset daily profit/loss at start of new day."""
        self.daily_pnl = 0.0
        self._save_daily_pnl()
