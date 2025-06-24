"""
🛡️ Integrated Risk Manager - SUPABASE VERSION
===============================================
Ersätter den gamla RiskManager som använde daily_pnl.json
Nu använder Supabase för persistent risk tracking.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Dict, Optional, Tuple

from backend.services.simple_database_service import simple_db

logger = logging.getLogger(__name__)


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
        max_action_prob = max(self.probability_buy, self.probability_sell)
        risk_score = 1.0 - (self.confidence * max_action_prob)
        return max(0.0, min(1.0, risk_score))


class IntegratedRiskManager:
    """
    🛡️ Risk Manager with Supabase Integration
    
    ERSÄTTER: gamla RiskManager som använde daily_pnl.json
    ANVÄNDER: Supabase för persistent risk tracking
    """
    
    def __init__(self, risk_params: RiskParameters):
        """Initialize risk manager with Supabase integration."""
        self.params = risk_params
        self.db = simple_db
        
        logger.info("✅ IntegratedRiskManager initialized with Supabase")
        
        # Initialize today's risk metrics if not exists
        self._ensure_today_risk_metrics()
    
    def _ensure_today_risk_metrics(self):
        """Ensure today's risk metrics exist in database."""
        risk_data = self.db.get_today_risk_metrics()
        if not risk_data:
            # Create today's risk metrics
            self.db.update_daily_pnl(0.0, 0)
            logger.info("📊 Created today's risk metrics in database")
    
    @property
    def daily_pnl(self) -> float:
        """Get today's P&L from database (persistent!)"""
        risk_data = self.db.get_today_risk_metrics()
        if risk_data:
            return float(risk_data.get('daily_pnl', 0))
        return 0.0
    
    def validate_order(
        self,
        order_data: Dict[str, Any],
        portfolio_value: float,
        current_positions: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Validate order against risk parameters using persistent data.
        """
        errors = []
        
        # Get current positions from database if not provided
        if current_positions is None:
            db_positions = self.db.get_all_positions()
            current_positions = {pos['symbol']: pos for pos in db_positions}
        
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

        # Check number of open positions (from database!)
        if len(current_positions) >= self.params.max_open_positions:
            errors.append(
                f"Maximum number of open positions ({self.params.max_open_positions}) exceeded"
            )

        # Check daily loss limit (from database!)
        current_daily_pnl = self.daily_pnl
        if current_daily_pnl < -self.params.max_daily_loss * portfolio_value:
            errors.append(
                f"Daily loss limit exceeded: {current_daily_pnl:.2f} < "
                f"-{self.params.max_daily_loss * portfolio_value:.2f}"
            )
        
        # Check if trading is allowed based on database risk metrics
        if not self.db.is_trading_allowed():
            errors.append("Trading is disabled due to risk limits")

        result = {
            "valid": len(errors) == 0, 
            "errors": errors,
            "daily_pnl": current_daily_pnl,
            "trading_allowed": self.db.is_trading_allowed()
        }
        
        logger.debug(f"🛡️ Order validation: {result}")
        return result

    def validate_order_with_probabilities(
        self,
        order_data: Dict[str, Any],
        portfolio_value: float,
        current_positions: Optional[Dict[str, Dict[str, Any]]] = None,
        probability_data: Optional[ProbabilityData] = None,
    ) -> Dict[str, Any]:
        """Enhanced order validation using probability data."""
        # Start with basic validation
        basic_validation = self.validate_order(order_data, portfolio_value, current_positions)
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
            "risk_score": probability_data.get_risk_score() if probability_data else 0.5,
            "confidence": probability_data.confidence if probability_data else 0.0,
            "daily_pnl": basic_validation["daily_pnl"],
            "trading_allowed": basic_validation["trading_allowed"]
        }

    def calculate_position_size(
        self,
        signal_confidence: float,
        portfolio_value: float,
        current_positions: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> float:
        """Calculate safe position size based on risk parameters."""
        # Get current positions from database if not provided
        if current_positions is None:
            db_positions = self.db.get_all_positions()
            current_positions = {pos['symbol']: pos for pos in db_positions}
        
        # Calculate available portfolio fraction
        used_capital = sum(
            float(pos.get("size", 0)) * float(pos.get("entry_price", 0))
            for pos in current_positions.values()
        )
        available_capital = portfolio_value - used_capital

        # Calculate position size based on confidence and risk parameters
        max_position = available_capital * self.params.max_position_size
        position_size = max_position * signal_confidence

        logger.debug(f"💰 Position size calculated: {position_size:.2f} (confidence: {signal_confidence:.2%})")
        return position_size

    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price."""
        if side == "buy":
            return entry_price * (1 - self.params.stop_loss_pct)
        else:
            return entry_price * (1 + self.params.stop_loss_pct)

    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """Calculate take profit price."""
        if side == "buy":
            return entry_price * (1 + self.params.take_profit_pct)
        else:
            return entry_price * (1 - self.params.take_profit_pct)

    def update_daily_pnl(self, pnl: float):
        """
        🚨 KRITISK METOD - Update daily P&L i Supabase (PERSISTENT!)
        
        Detta ersätter den gamla JSON-fil metoden som förlorade data vid restart.
        """
        # Get current trades count for metrics
        trades = self.db.get_all_trades()
        total_trades = len(trades)
        
        success = self.db.update_daily_pnl(pnl, total_trades)
        
        if success:
            logger.info(f"✅ Daily P&L updated in database: {pnl:.2f}")
            
            # Create alert if P&L is concerning
            if pnl < -500:  # Alert if loss > $500
                self.db.create_alert(
                    "risk_management",
                    "warning", 
                    "High Daily Loss",
                    f"Daily P&L: ${pnl:.2f}. Monitor risk carefully."
                )
        else:
            logger.error(f"❌ Failed to update daily P&L: {pnl}")
            # Create error alert
            self.db.create_alert(
                "system_error",
                "error",
                "P&L Update Failed", 
                f"Could not update daily P&L: {pnl:.2f}"
            )

    def reset_daily_pnl(self):
        """Reset daily P&L (new day)."""
        self.update_daily_pnl(0.0)
        logger.info("📊 Daily P&L reset for new day")

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get complete risk summary from database."""
        risk_metrics = self.db.get_today_risk_metrics()
        positions = self.db.get_all_positions()
        trades = self.db.get_all_trades()
        
        # Calculate metrics
        total_pnl = sum(float(t.get('pnl', 0)) for t in trades if t.get('pnl'))
        open_trades = len([t for t in trades if t.get('status') == 'open'])
        
        summary = {
            "daily_pnl": self.daily_pnl,
            "trading_allowed": self.db.is_trading_allowed(),
            "total_positions": len(positions),
            "open_trades": open_trades,
            "total_pnl": round(total_pnl, 2),
            "max_positions": self.params.max_open_positions,
            "max_daily_loss": self.params.max_daily_loss,
            "risk_params": {
                "max_position_size": self.params.max_position_size,
                "stop_loss_pct": self.params.stop_loss_pct,
                "take_profit_pct": self.params.take_profit_pct
            }
        }
        
        logger.info(f"🛡️ Risk summary: {summary}")
        return summary


# Global integrated risk manager instance 
# (replace the old one that used JSON files)
default_risk_params = RiskParameters(
    max_position_size=0.1,
    max_leverage=3.0, 
    stop_loss_pct=0.05,
    take_profit_pct=0.1,
    max_daily_loss=0.02,
    max_open_positions=5
)

integrated_risk_manager = IntegratedRiskManager(default_risk_params)