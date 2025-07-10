"""Risk management service for trading operations - async version."""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
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
    probability_weight: float = 0.5  # Weight for probability vs confidence


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


class RiskManagerAsync:
    """Async service for managing trading risk."""

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
        asyncio.create_task(self._load_daily_pnl())

    async def _load_daily_pnl(self):
        """Load daily PnL data from persistence file asynchronously."""
        if os.path.exists(self.persistence_file):
            try:
                # Run file operations in a thread pool
                loop = asyncio.get_event_loop()
                content = await loop.run_in_executor(
                    None, lambda: open(self.persistence_file, "r").read()
                )
                data = json.loads(content)

                saved_date_str = data.get("date", str(date.today()))
                saved_date = date.fromisoformat(saved_date_str)

                # Reset if it's a new day
                if saved_date != self.current_date:
                    self.daily_pnl = 0.0
                    await self._save_daily_pnl()
                else:
                    self.daily_pnl = data.get("daily_pnl", 0.0)
            except (json.JSONDecodeError, KeyError, ValueError, IOError) as e:
                # If file is corrupted or can't be read, start fresh
                logging.warning(f"Error loading daily PnL data: {e}")
                self.daily_pnl = 0.0
                await self._save_daily_pnl()

    async def _save_daily_pnl(self):
        """Save daily PnL data to persistence file asynchronously."""
        data = {
            "date": str(self.current_date),
            "daily_pnl": self.daily_pnl,
            "last_updated": datetime.now().isoformat(),
        }
        try:
            # Run file operations in a thread pool
            loop = asyncio.get_event_loop()
            content = json.dumps(data, indent=2)
            await loop.run_in_executor(
                None, lambda: open(self.persistence_file, "w").write(content)
            )
        except IOError as e:
            # Log error but don't fail - this is non-critical
            logging.warning(f"Warning: Could not save daily PnL data: {e}")

    async def _check_new_day(self):
        """Check if it's a new day and reset daily PnL if needed."""
        today = date.today()
        if today != self.current_date:
            self.current_date = today
            self.daily_pnl = 0.0
            await self._save_daily_pnl()

    async def validate_order(
        self,
        order_data: Dict[str, Any],
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate order against risk parameters asynchronously.

        Args:
            order_data: Order data dictionary
            portfolio_value: Current portfolio value
            current_positions: Current open positions

        Returns:
            Dict containing validation result and any errors
        """
        # Check for new day first
        await self._check_new_day()

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

    async def validate_order_with_probabilities(
        self,
        order_data: Dict[str, Any],
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
        probability_data: Optional[ProbabilityData] = None,
    ) -> Dict[str, Any]:
        """
        Enhanced order validation using probability data asynchronously.

        Args:
            order_data: Order data dictionary
            portfolio_value: Current portfolio value
            current_positions: Current open positions
            probability_data: Strategy probability data

        Returns:
            Dict containing validation result, errors, and risk assessment
        """
        # Start with basic validation
        basic_validation = await self.validate_order(
            order_data, portfolio_value, current_positions
        )
        errors = basic_validation["errors"].copy()
        risk_score = 0.5  # Default risk score

        # Add probability-based validation if available
        if probability_data:
            action = order_data.get("side", "").lower()
            action_probability = probability_data.get_action_probability(action)

            # Check minimum confidence
            if probability_data.confidence < self.params.min_signal_confidence:
                errors.append(
                    f"Signal confidence {probability_data.confidence:.2%} "
                    f"below minimum {self.params.min_signal_confidence:.2%}"
                )

            # Check for conflicting action
            if action_probability < 0.4:  # Less than 40% probability for this action
                errors.append(
                    f"Low probability ({action_probability:.2%}) for {action} action"
                )

            # Calculate risk score (0-1, lower is safer)
            risk_score = probability_data.get_risk_score()

            # High-risk trades might need higher position size threshold
            position_size = float(order_data["amount"]) * float(
                order_data.get("price", 0)
            )
            position_size_pct = position_size / portfolio_value

            if (
                risk_score > 0.7
                and position_size_pct > self.params.max_position_size * 0.7
            ):
                errors.append(
                    f"Position size too large ({position_size_pct:.2%}) for high-risk "
                    f"trade (risk score: {risk_score:.2f})"
                )

        # Build enhanced result
        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "risk_assessment": {
                "daily_pnl_status": self.daily_pnl / portfolio_value,
                "position_count": len(current_positions),
                "risk_score": risk_score,
            },
        }

        return result

    async def calculate_intelligent_position_size(
        self,
        signal_confidence: float,
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
        probability_data: Optional[ProbabilityData] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate position size based on confidence and probability data asynchronously.

        Args:
            signal_confidence: Confidence of the trading signal
            portfolio_value: Current portfolio value
            current_positions: Current open positions
            probability_data: Strategy probability data

        Returns:
            Tuple of (position_size, calculation_metadata)
        """
        await self._check_new_day()

        # Base position size on risk parameters
        base_position_pct = self.params.max_position_size * signal_confidence

        metadata = {
            "base_position_pct": base_position_pct,
            "confidence_factor": signal_confidence,
        }

        # Adjust for probability if available
        if probability_data:
            # Lower position size if probabilities aren't clear
            buy_prob = probability_data.probability_buy
            sell_prob = probability_data.probability_sell

            # Calculate decision clarity (0-1, higher is clearer)
            decision_clarity = abs(buy_prob - sell_prob)

            # Use probability weight parameter to blend confidence with clarity
            pw = self.params.probability_weight
            combined_factor = (signal_confidence * (1 - pw)) + (decision_clarity * pw)

            # Adjust position size
            position_pct = base_position_pct * combined_factor

            metadata.update(
                {
                    "decision_clarity": decision_clarity,
                    "probability_factor": combined_factor,
                    "adjusted_position_pct": position_pct,
                }
            )
        else:
            position_pct = base_position_pct

        # Reduce position if close to daily loss limit
        daily_pnl_factor = max(
            0.5, 1.0 + (self.daily_pnl / (self.params.max_daily_loss * portfolio_value))
        )
        position_pct *= daily_pnl_factor

        # Reduce position if many positions already open
        position_count = len(current_positions)
        max_positions = self.params.max_open_positions
        if position_count > 0:
            diversification_factor = 1.0 - (position_count / max_positions) * 0.5
            position_pct *= max(0.5, diversification_factor)
            metadata["diversification_factor"] = diversification_factor

        # Calculate final position size
        position_size = portfolio_value * position_pct

        metadata.update(
            {
                "daily_pnl_factor": daily_pnl_factor,
                "position_count": position_count,
                "final_position_pct": position_pct,
                "calculated_position_size": position_size,
            }
        )

        return position_size, metadata

    async def calculate_dynamic_stop_loss(
        self,
        entry_price: float,
        side: str,
        probability_data: Optional[ProbabilityData] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate dynamic stop loss based on probability data asynchronously.

        Args:
            entry_price: Entry price for the position
            side: Order side (buy/sell)
            probability_data: Strategy probability data

        Returns:
            Tuple of (stop_loss_price, calculation_metadata)
        """
        # Base stop loss on risk parameters
        base_stop_pct = self.params.stop_loss_pct

        metadata = {
            "base_stop_pct": base_stop_pct,
            "side": side,
        }

        # Adjust stop loss if probability data available
        if probability_data:
            # Calculate risk score (0-1, higher is riskier)
            risk_score = probability_data.get_risk_score()

            # Tighter stop loss for higher risk
            adjusted_stop_pct = base_stop_pct * (1.0 - risk_score * 0.3)

            metadata.update(
                {
                    "risk_score": risk_score,
                    "adjusted_stop_pct": adjusted_stop_pct,
                }
            )
        else:
            adjusted_stop_pct = base_stop_pct

        # Calculate final stop loss price
        if side.lower() == "buy":
            stop_price = entry_price * (1.0 - adjusted_stop_pct)
        else:
            stop_price = entry_price * (1.0 + adjusted_stop_pct)

        metadata["stop_price"] = stop_price

        return stop_price, metadata

    async def calculate_dynamic_take_profit(
        self,
        entry_price: float,
        side: str,
        probability_data: Optional[ProbabilityData] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate dynamic take profit based on probability data asynchronously.

        Args:
            entry_price: Entry price for the position
            side: Order side (buy/sell)
            probability_data: Strategy probability data

        Returns:
            Tuple of (take_profit_price, calculation_metadata)
        """
        # Base take profit on risk parameters
        base_tp_pct = self.params.take_profit_pct

        metadata = {
            "base_tp_pct": base_tp_pct,
            "side": side,
        }

        # Adjust take profit if probability data available
        if probability_data:
            # Use confidence to adjust take profit
            confidence = probability_data.confidence

            # Higher confidence = higher take profit
            adjusted_tp_pct = base_tp_pct * (1.0 + confidence * 0.5)

            metadata.update(
                {
                    "confidence": confidence,
                    "adjusted_tp_pct": adjusted_tp_pct,
                }
            )
        else:
            adjusted_tp_pct = base_tp_pct

        # Calculate final take profit price
        if side.lower() == "buy":
            tp_price = entry_price * (1.0 + adjusted_tp_pct)
        else:
            tp_price = entry_price * (1.0 - adjusted_tp_pct)

        metadata["tp_price"] = tp_price

        return tp_price, metadata

    async def assess_portfolio_risk(
        self,
        current_positions: Dict[str, Dict[str, Any]],
        pending_orders: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Assess overall portfolio risk asynchronously.

        Args:
            current_positions: Current open positions
            pending_orders: Pending orders

        Returns:
            Dict with risk assessment metrics
        """
        await self._check_new_day()

        # Calculate total exposure
        total_exposure = 0.0
        max_exposure = 0.0
        symbols = set()

        for pos_id, pos in current_positions.items():
            exposure = abs(float(pos.get("notional", 0.0)))
            symbol = pos.get("symbol", "")
            total_exposure += exposure
            max_exposure = max(max_exposure, exposure)
            symbols.add(symbol)

        if pending_orders:
            for order_id, order in pending_orders.items():
                exposure = float(order.get("amount", 0.0)) * float(
                    order.get("price", 0.0)
                )
                symbol = order.get("symbol", "")
                total_exposure += exposure
                symbols.add(symbol)

        # Calculate diversification metrics
        symbol_count = len(symbols)
        pos_count = len(current_positions)

        # Concentration risk (higher is more concentrated)
        concentration = max_exposure / total_exposure if total_exposure > 0 else 0.0

        # Build risk assessment
        risk_assessment = {
            "total_exposure": total_exposure,
            "position_count": pos_count,
            "symbol_count": symbol_count,
            "concentration_risk": concentration,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_pct": (
                self.daily_pnl / total_exposure if total_exposure > 0 else 0.0
            ),
            "positions_vs_max": pos_count / self.params.max_open_positions,
            "risk_level": self._calculate_overall_risk_level(
                concentration, pos_count, self.daily_pnl, total_exposure
            ),
            "timestamp": datetime.now().isoformat(),
        }

        return risk_assessment

    def _calculate_overall_risk_level(
        self,
        concentration: float,
        position_count: int,
        daily_pnl: float,
        total_exposure: float,
    ) -> str:
        """Calculate overall risk level based on multiple factors."""
        risk_points = 0

        # High concentration adds risk
        if concentration > 0.5:
            risk_points += 2
        elif concentration > 0.3:
            risk_points += 1

        # Many positions adds risk
        max_positions = self.params.max_open_positions
        if position_count > max_positions * 0.8:
            risk_points += 2
        elif position_count > max_positions * 0.5:
            risk_points += 1

        # Negative daily PnL adds risk
        if daily_pnl < 0 and total_exposure > 0:
            daily_pnl_pct = abs(daily_pnl / total_exposure)
            if daily_pnl_pct > self.params.max_daily_loss * 0.7:
                risk_points += 3
            elif daily_pnl_pct > self.params.max_daily_loss * 0.4:
                risk_points += 2
            elif daily_pnl_pct > self.params.max_daily_loss * 0.2:
                risk_points += 1

        # Convert to risk level
        if risk_points >= 5:
            return "critical"
        elif risk_points >= 3:
            return "high"
        elif risk_points >= 1:
            return "moderate"
        else:
            return "low"

    async def update_daily_pnl(self, pnl: float):
        """
        Update daily PnL and persist it asynchronously.

        Args:
            pnl: PnL amount to add (positive or negative)
        """
        await self._check_new_day()
        self.daily_pnl += pnl
        await self._save_daily_pnl()

    async def reset_daily_pnl(self):
        """Reset daily PnL to zero asynchronously."""
        self.daily_pnl = 0.0
        await self._save_daily_pnl()


# Singleton instance
_risk_manager_async: Optional[RiskManagerAsync] = None


async def get_risk_manager_async(
    risk_params: Optional[RiskParameters] = None,
) -> RiskManagerAsync:
    """
    Get or create a singleton instance of RiskManagerAsync.

    Args:
        risk_params: Risk parameters, only used if instance doesn't exist

    Returns:
        RiskManagerAsync instance
    """
    global _risk_manager_async

    if _risk_manager_async is None:
        if risk_params is None:
            # Default parameters if none provided
            risk_params = RiskParameters(
                max_position_size=0.2,  # Max 20% of portfolio per position
                max_leverage=3.0,  # Max 3x leverage
                stop_loss_pct=0.05,  # 5% stop loss
                take_profit_pct=0.1,  # 10% take profit
                max_daily_loss=0.1,  # Max 10% daily loss
                max_open_positions=5,  # Max 5 open positions
                min_signal_confidence=0.6,  # Minimum 60% confidence
                probability_weight=0.5,  # Equal weight to confidence/probability
            )

        _risk_manager_async = RiskManagerAsync(risk_params)

    return _risk_manager_async
