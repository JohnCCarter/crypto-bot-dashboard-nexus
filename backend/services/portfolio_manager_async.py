"""Portfolio management service for combining multiple strategy signals - async version."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

from backend.services.risk_manager_async import ProbabilityData, RiskManagerAsync
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


class PortfolioManagerAsync:
    """Async service for managing portfolio with multiple strategies."""

    def __init__(
        self, risk_manager: RiskManagerAsync, strategy_weights: List[StrategyWeight]
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

    async def combine_strategy_signals(
        self,
        strategy_signals: Dict[str, TradeSignal],
        symbol: str,
        current_price: float,
    ) -> CombinedSignal:
        """
        Combine signals from multiple strategies into a single decision asynchronously.

        Args:
            strategy_signals: Dict of strategy_name -> TradeSignal
            symbol: Trading symbol
            current_price: Current price for the symbol

        Returns:
            CombinedSignal with combined probabilities and action
        """
        if not strategy_signals:
            return await self._create_hold_signal("No strategy signals provided")

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
            return await self._create_hold_signal("No valid signals after filtering")

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

    async def _create_hold_signal(self, reason: str) -> CombinedSignal:
        """Create a neutral 'hold' signal with metadata."""
        prob_data = ProbabilityData(
            probability_buy=0.2,
            probability_sell=0.2,
            probability_hold=0.6,
            confidence=0.5,
        )

        return CombinedSignal(
            action="hold",
            combined_confidence=0.5,
            combined_probabilities=prob_data,
            individual_signals={},
            metadata={"reason": reason, "timestamp": datetime.now().isoformat()},
        )

    async def calculate_portfolio_position_size(
        self,
        combined_signal: CombinedSignal,
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
        symbol: str,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate position size for the combined signal asynchronously.

        Args:
            combined_signal: Combined signal from multiple strategies
            portfolio_value: Current portfolio value
            current_positions: Current open positions
            symbol: Trading symbol

        Returns:
            Tuple of (position_size, calculation_metadata)
        """
        # Use intelligent position sizing with combined probabilities
        position_size, metadata = (
            await self.risk_manager.calculate_intelligent_position_size(
                signal_confidence=combined_signal.combined_confidence,
                portfolio_value=portfolio_value,
                current_positions=current_positions,
                probability_data=combined_signal.combined_probabilities,
            )
        )

        # Add portfolio-specific metadata
        metadata.update(
            {
                "symbol": symbol,
                "combined_signal_action": combined_signal.action,
                "strategies_count": len(combined_signal.individual_signals),
                "portfolio_diversification_factor": await self._calculate_diversification_factor(
                    current_positions
                ),
            }
        )

        return position_size, metadata

    async def _calculate_diversification_factor(
        self, current_positions: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate diversification factor based on current positions asynchronously."""
        if not current_positions:
            return 1.0

        # Simple diversification: more positions = lower individual position size
        position_count = len(current_positions)
        max_positions = self.risk_manager.params.max_open_positions

        diversification_factor = max(0.5, 1.0 - (position_count / max_positions) * 0.5)
        return diversification_factor

    async def should_execute_trade(
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
        position_size, size_metadata = await self.calculate_portfolio_position_size(
            combined_signal, portfolio_value, current_positions, symbol
        )

        order_data = {
            "symbol": symbol,
            "side": combined_signal.action,  # buy or sell
            "type": "market",
            "amount": position_size,
            "price": current_price,
        }

        # Get risk assessment
        validation_result = await self.risk_manager.validate_order_with_probabilities(
            order_data=order_data,
            portfolio_value=portfolio_value,
            current_positions=current_positions,
            probability_data=combined_signal.combined_probabilities,
        )

        # Determine if we should execute
        should_execute = (
            validation_result["valid"]
            and combined_signal.action in ["buy", "sell"]
            and position_size > 0
        )

        # Create decision metadata
        metadata = {
            "symbol": symbol,
            "action": combined_signal.action,
            "confidence": combined_signal.combined_confidence,
            "position_size": position_size,
            "position_size_metadata": size_metadata,
            "risk_validation": validation_result,
            "timestamp": datetime.now().isoformat(),
        }

        return should_execute, metadata

    async def rebalance_portfolio_weights(
        self, performance_data: Dict[str, float]
    ) -> None:
        """
        Rebalance strategy weights based on performance data.

        Args:
            performance_data: Dict mapping strategy_name -> performance_score
        """
        if not performance_data:
            return

        # Simple rebalancing algorithm: adjust weights based on performance
        for strategy_name, performance in performance_data.items():
            if strategy_name in self.strategy_weights:
                # Adjust weight based on performance (normalize between 0.5 and 1.5)
                normalized_performance = max(0.5, min(1.5, performance))
                self.strategy_weights[strategy_name].weight *= normalized_performance

        # Normalize weights
        await self._normalize_weights()

    async def process_signals(
        self, signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process strategy signals to determine trading actions.

        Args:
            signals: List of strategy signal dictionaries

        Returns:
            List of recommended trading actions
        """
        actions = []

        # Group signals by symbol
        symbols_signals = {}
        for signal in signals:
            symbol = signal.get("symbol")
            if symbol not in symbols_signals:
                symbols_signals[symbol] = {}

            strategy_name = signal.get("source", "unknown")
            signals_dict = {
                "action": signal.get("signal_type"),
                "confidence": signal.get("confidence", 0.5),
                "metadata": {
                    "probability_buy": signal.get("indicators", {}).get(
                        "probability_buy", 0.33
                    ),
                    "probability_sell": signal.get("indicators", {}).get(
                        "probability_sell", 0.33
                    ),
                    "probability_hold": signal.get("indicators", {}).get(
                        "probability_hold", 0.34
                    ),
                },
            }

            # Convert to TradeSignal
            trade_signal = TradeSignal(
                action=signals_dict["action"],
                confidence=signals_dict["confidence"],
                metadata=signals_dict["metadata"],
            )

            symbols_signals[symbol][strategy_name] = trade_signal

        # Process each symbol's signals
        for symbol, strategy_signals in symbols_signals.items():
            # Get current price from the first signal for this symbol
            price = next(
                (s.get("price", 0.0) for s in signals if s.get("symbol") == symbol), 0.0
            )

            # Combine signals for this symbol
            combined_signal = await self.combine_strategy_signals(
                strategy_signals=strategy_signals, symbol=symbol, current_price=price
            )

            # Mock portfolio value and positions for demo
            portfolio_value = 100000.0  # Mock portfolio value
            current_positions = {}  # Mock current positions

            # Determine if we should execute a trade
            should_execute, metadata = await self.should_execute_trade(
                combined_signal=combined_signal,
                portfolio_value=portfolio_value,
                current_positions=current_positions,
                symbol=symbol,
                current_price=price,
            )

            # Create action recommendation
            action = {
                "symbol": symbol,
                "action": combined_signal.action,
                "confidence": combined_signal.combined_confidence,
                "should_execute": should_execute,
                "position_size": metadata.get("position_size", 0.0),
                "price": price,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata,
            }

            actions.append(action)

        return actions

    async def calculate_allocations(
        self,
        signals: List[Dict[str, Any]],
        risk_profile: str = "moderate",
        max_allocation_percent: float = 0.8,
    ) -> List[Dict[str, Any]]:
        """
        Calculate optimal portfolio allocation based on strategy signals and risk profile.

        Args:
            signals: List of strategy signals
            risk_profile: Risk profile ('conservative', 'moderate', 'aggressive')
            max_allocation_percent: Maximum percentage to allocate (0.0-1.0)

        Returns:
            List of allocation recommendations
        """
        allocations = []

        # Convert risk profile to factor
        risk_factors = {"conservative": 0.5, "moderate": 0.75, "aggressive": 1.0}
        risk_factor = risk_factors.get(risk_profile, 0.75)

        # Process signals to get actions
        actions = await self.process_signals(signals)

        # Calculate total confidence for buy signals
        buy_actions = [
            a for a in actions if a["action"] == "buy" and a["should_execute"]
        ]
        total_buy_confidence = sum(a["confidence"] for a in buy_actions)

        # Calculate allocations based on confidence and risk profile
        for action in buy_actions:
            if total_buy_confidence > 0:
                # Weight by confidence
                allocation_weight = action["confidence"] / total_buy_confidence

                # Apply risk profile and max allocation
                allocation_percent = (
                    allocation_weight * max_allocation_percent * risk_factor
                )

                allocations.append(
                    {
                        "symbol": action["symbol"],
                        "percentage": allocation_percent,
                        "action": "buy",
                        "target_allocation": allocation_percent,
                        "current_allocation": 0.0,  # This would be from current portfolio
                        "confidence": action["confidence"],
                        "price": action["price"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return allocations

    async def _normalize_weights(self) -> None:
        """Normalize strategy weights to sum to 1.0."""
        enabled_weights = [
            (name, sw.weight)
            for name, sw in self.strategy_weights.items()
            if sw.enabled
        ]
        total_weight = sum(w for _, w in enabled_weights)

        if total_weight > 0:
            # Normalize weights
            for name, _ in enabled_weights:
                self.strategy_weights[name].weight /= total_weight

    async def get_portfolio_summary(
        self, current_positions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get portfolio summary statistics.

        Args:
            current_positions: Current open positions

        Returns:
            Dict with portfolio summary data
        """
        total_positions = len(current_positions)
        total_exposure = sum(
            float(pos.get("amount", 0)) * float(pos.get("entry_price", 0))
            for pos in current_positions.values()
        )

        # Get risk assessment
        risk_assessment = await self.risk_manager.assess_portfolio_risk(
            current_positions
        )

        return {
            "total_positions": total_positions,
            "total_exposure": total_exposure,
            "risk_assessment": risk_assessment,
            "active_strategies": [
                name for name, sw in self.strategy_weights.items() if sw.enabled
            ],
            "timestamp": datetime.now().isoformat(),
        }

    async def get_portfolio_status(self) -> Dict[str, Any]:
        """
        Get current portfolio status with allocations and metrics.

        Returns:
            Dict with portfolio status information
        """
        # Mock current positions for demo
        current_positions = {
            "BTC/USD": {
                "symbol": "BTC/USD",
                "side": "buy",
                "amount": 0.5,
                "entry_price": 35000.0,
                "mark_price": 36000.0,
                "pnl": 500.0,
                "pnl_percentage": 2.86,
            },
            "ETH/USD": {
                "symbol": "ETH/USD",
                "side": "buy",
                "amount": 5.0,
                "entry_price": 2000.0,
                "mark_price": 2100.0,
                "pnl": 500.0,
                "pnl_percentage": 5.0,
            },
        }

        # Get portfolio summary
        summary = await self.get_portfolio_summary(current_positions)

        # Add additional portfolio metrics
        total_value = sum(
            pos.get("amount", 0) * pos.get("mark_price", 0)
            for pos in current_positions.values()
        )

        total_pnl = sum(pos.get("pnl", 0) for pos in current_positions.values())

        # Calculate weighted average PnL percentage
        if total_value > 0:
            weighted_pnl_percentage = total_pnl / total_value * 100
        else:
            weighted_pnl_percentage = 0.0

        # Get active strategy weights
        active_strategies = {
            name: {"weight": sw.weight, "min_confidence": sw.min_confidence}
            for name, sw in self.strategy_weights.items()
            if sw.enabled
        }

        return {
            "total_value": total_value,
            "positions": current_positions,
            "position_count": len(current_positions),
            "total_pnl": total_pnl,
            "pnl_percentage": weighted_pnl_percentage,
            "risk_summary": summary["risk_assessment"],
            "active_strategies": active_strategies,
            "timestamp": datetime.now().isoformat(),
        }

    async def rebalance_portfolio(
        self, target_allocations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Rebalance portfolio to match target allocations.

        Args:
            target_allocations: List of target allocation objects

        Returns:
            Dict with rebalancing results
        """
        # Mock current positions and portfolio value for demo
        current_positions = {
            "BTC/USD": {
                "symbol": "BTC/USD",
                "amount": 0.5,
                "current_price": 36000.0,
                "value": 18000.0,
            },
            "ETH/USD": {
                "symbol": "ETH/USD",
                "amount": 5.0,
                "current_price": 2100.0,
                "value": 10500.0,
            },
        }

        portfolio_value = sum(pos.get("value", 0) for pos in current_positions.values())

        # Calculate current allocations
        current_allocations = {
            pos["symbol"]: pos["value"] / portfolio_value if portfolio_value > 0 else 0
            for pos in current_positions.values()
        }

        # Prepare rebalancing actions
        rebalancing_actions = []

        for target in target_allocations:
            symbol = target.get("symbol")
            target_pct = (
                target.get("percentage", 0) / 100
                if isinstance(target.get("percentage"), float)
                else 0
            )
            current_pct = current_allocations.get(symbol, 0)

            # Calculate difference
            diff_pct = target_pct - current_pct

            # Calculate amount to buy or sell
            action_value = diff_pct * portfolio_value

            # Get current price
            current_price = 0.0
            if symbol in current_positions:
                current_price = current_positions[symbol].get("current_price", 0)
            else:
                # Mock prices for demo
                if "BTC" in symbol:
                    current_price = 36000.0
                elif "ETH" in symbol:
                    current_price = 2100.0
                elif "LTC" in symbol:
                    current_price = 155.0
                else:
                    current_price = 100.0

            # Calculate amount
            amount = action_value / current_price if current_price > 0 else 0

            # Determine action
            action_type = "buy" if diff_pct > 0 else "sell" if diff_pct < 0 else "hold"

            rebalancing_actions.append(
                {
                    "symbol": symbol,
                    "current_allocation": current_pct * 100,
                    "target_allocation": target_pct * 100,
                    "difference": diff_pct * 100,
                    "action": action_type,
                    "amount": abs(amount),
                    "price": current_price,
                    "value": abs(action_value),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return {
            "portfolio_value": portfolio_value,
            "actions": rebalancing_actions,
            "timestamp": datetime.now().isoformat(),
        }


async def get_portfolio_manager_async(
    risk_manager: RiskManagerAsync, strategy_weights: List[StrategyWeight]
) -> PortfolioManagerAsync:
    """
    Get an instance of PortfolioManagerAsync.

    Args:
        risk_manager: Risk manager instance
        strategy_weights: Strategy weights configuration

    Returns:
        PortfolioManagerAsync instance
    """
    portfolio_manager = PortfolioManagerAsync(risk_manager, strategy_weights)
    logging.info(
        "PortfolioManagerAsync initialized with %d strategies", len(strategy_weights)
    )
    return portfolio_manager
