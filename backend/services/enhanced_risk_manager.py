"""
⚠️ Enhanced Risk Manager with Supabase Persistence
=================================================
LÖSER DET KRITISKA IN-MEMORY STATE PROBLEMET!

Ingen mer dataförlust vid restart - daily P&L tracking är nu persistent!
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from dataclasses import dataclass

from backend.services.database_service import db_service
from backend.models.trading_models import RiskMetricsModel, AlertModel

logger = logging.getLogger(__name__)


@dataclass
class RiskParameters:
    """Risk management parameters (unchanged from original)"""
    max_position_size: float = 0.1
    max_leverage: float = 3.0
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 4.0
    max_daily_loss: float = 5.0
    max_open_positions: int = 5
    min_signal_confidence: float = 0.6
    probability_weight: float = 0.5
    risk_per_trade: float = 0.02
    lookback: int = 5


class EnhancedRiskManager:
    """
    🔒 Enhanced Risk Manager with Persistent Storage
    
    KRITISK FÖRBÄTTRING:
    - Ersätter in-memory daily_pnl med Supabase-persistens
    - Förhindrar överhandel efter restart
    - Complete audit trail av alla risk-beslut
    """
    
    def __init__(self, parameters: RiskParameters = None):
        """Initialize with risk parameters"""
        self.params = parameters or RiskParameters()
        self.db = db_service
        logger.info("✅ Enhanced RiskManager initialized with Supabase persistence")
    
    # ============================================
    # 💰 PERSISTENT DAILY P&L TRACKING (KRITISK!)
    # ============================================
    
    def get_daily_pnl(self, target_date: date = None) -> Decimal:
        """
        Get persistent daily P&L from database
        
        🔥 KRITISK: Denna data förloras INTE vid restart!
        """
        if target_date is None:
            target_date = date.today()
            
        try:
            metrics = self.db.get_daily_risk_metrics(target_date)
            if metrics:
                pnl = metrics.daily_pnl
                logger.debug(f"💰 Daily P&L for {target_date}: {pnl}")
                return pnl
            else:
                # Initialize new day metrics
                logger.info(f"📅 Initializing risk metrics for {target_date}")
                new_metrics = RiskMetricsModel(date=target_date)
                self.db.update_daily_risk_metrics(new_metrics)
                return Decimal('0')
                
        except Exception as e:
            logger.error(f"❌ Failed to get daily P&L: {e}")
            return Decimal('0')
    
    def update_daily_pnl(self, trade_pnl: Decimal, target_date: date = None) -> bool:
        """
        Update persistent daily P&L after trade
        
        🔥 KRITISK: Data sparas i databas och överlever restart!
        """
        if target_date is None:
            target_date = date.today()
            
        try:
            # Get existing metrics or create new
            metrics = self.db.get_daily_risk_metrics(target_date)
            if not metrics:
                metrics = RiskMetricsModel(date=target_date)
            
            # Update P&L
            old_pnl = metrics.daily_pnl
            metrics.daily_pnl += trade_pnl
            
            # Update loss tracking
            if trade_pnl < 0:
                metrics.daily_loss += abs(trade_pnl)
                metrics.consecutive_losses += 1
                metrics.losing_trades += 1
                if abs(trade_pnl) > metrics.largest_loss:
                    metrics.largest_loss = abs(trade_pnl)
            else:
                metrics.consecutive_losses = 0
                metrics.winning_trades += 1
                if trade_pnl > metrics.largest_win:
                    metrics.largest_win = trade_pnl
            
            metrics.total_trades += 1
            
            # Calculate win rate
            if metrics.total_trades > 0:
                metrics.win_rate = Decimal(metrics.winning_trades) / Decimal(metrics.total_trades)
            
            # Update risk score and trading allowance
            metrics.risk_score = self._calculate_risk_score(metrics)
            metrics.trading_allowed = self._is_trading_allowed(metrics)
            
            # Save to database
            success = self.db.update_daily_risk_metrics(metrics)
            
            if success:
                logger.info(f"💰 Daily P&L updated: {old_pnl} → {metrics.daily_pnl} (trade: {trade_pnl})")
                
                # Create alert if daily loss limit exceeded
                if metrics.daily_loss >= Decimal(str(self.params.max_daily_loss)):
                    self._create_risk_alert(
                        "Daily Loss Limit Exceeded",
                        f"Daily loss: {metrics.daily_loss}% (limit: {self.params.max_daily_loss}%)",
                        "critical"
                    )
                
                return True
            else:
                logger.error(f"❌ Failed to save risk metrics to database")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update daily P&L: {e}")
            return False
    
    def is_trading_allowed(self, target_date: date = None) -> bool:
        """
        Check if trading is allowed based on persistent risk metrics
        
        🔒 SÄKERHET: Förhindrar handel efter för stora förluster
        """
        try:
            metrics = self.db.get_daily_risk_metrics(target_date)
            if not metrics:
                return True  # Allow trading if no metrics exist yet
            
            allowed = self._is_trading_allowed(metrics)
            
            if not allowed:
                logger.warning(f"🚫 Trading BLOCKED - Risk limits exceeded")
                self._create_risk_alert(
                    "Trading Suspended",
                    f"Risk limits exceeded. Daily loss: {metrics.daily_loss}%",
                    "critical"
                )
            
            return allowed
            
        except Exception as e:
            logger.error(f"❌ Failed to check trading allowance: {e}")
            # Fail safe - block trading if we can't check risk
            return False
    
    # ============================================
    # 🎯 RISK CALCULATION HELPERS
    # ============================================
    
    def _is_trading_allowed(self, metrics: RiskMetricsModel) -> bool:
        """Internal helper to determine trading allowance"""
        # Check daily loss limit
        if metrics.daily_loss >= Decimal(str(self.params.max_daily_loss)):
            return False
        
        # Check consecutive losses
        if metrics.consecutive_losses >= 5:
            return False
        
        # Check risk score
        if metrics.risk_score >= Decimal('0.9'):
            return False
        
        return True
    
    def _calculate_risk_score(self, metrics: RiskMetricsModel) -> Decimal:
        """Calculate risk score from 0.0 (safe) to 1.0 (dangerous)"""
        score = Decimal('0')
        
        # Daily loss component (0-0.5)
        loss_ratio = metrics.daily_loss / Decimal(str(self.params.max_daily_loss))
        score += min(loss_ratio * Decimal('0.5'), Decimal('0.5'))
        
        # Consecutive losses component (0-0.3)
        if metrics.consecutive_losses > 0:
            loss_factor = min(metrics.consecutive_losses / 5, 1.0)
            score += Decimal(str(loss_factor)) * Decimal('0.3')
        
        # Win rate component (0-0.2)
        if metrics.total_trades > 10:  # Only consider if enough trades
            poor_winrate = max(0, (Decimal('0.4') - metrics.win_rate)) * 2
            score += poor_winrate * Decimal('0.2')
        
        return min(score, Decimal('1.0'))
    
    def _create_risk_alert(self, title: str, message: str, severity: str) -> None:
        """Create risk management alert"""
        try:
            alert = AlertModel(
                type="risk",
                severity=severity,
                title=title,
                message=message,
                metadata={
                    "risk_manager": "enhanced",
                    "timestamp": datetime.now().isoformat()
                }
            )
            self.db.create_alert(alert)
        except Exception as e:
            logger.error(f"❌ Failed to create risk alert: {e}")
    
    # ============================================
    # 📊 RISK REPORTING & ANALYTICS
    # ============================================
    
    def get_risk_summary(self, days: int = 7) -> dict:
        """Get risk summary for recent days"""
        try:
            # This would get multiple days of metrics
            today_metrics = self.db.get_daily_risk_metrics()
            
            if not today_metrics:
                return {
                    "status": "no_data",
                    "message": "No risk metrics available"
                }
            
            return {
                "status": "active",
                "daily_pnl": float(today_metrics.daily_pnl),
                "daily_loss": float(today_metrics.daily_loss),
                "win_rate": float(today_metrics.win_rate),
                "total_trades": today_metrics.total_trades,
                "risk_score": float(today_metrics.risk_score),
                "trading_allowed": today_metrics.trading_allowed,
                "consecutive_losses": today_metrics.consecutive_losses
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get risk summary: {e}")
            return {"status": "error", "error": str(e)}


# Global enhanced risk manager instance
enhanced_risk_manager = EnhancedRiskManager()


# ============================================
# 🔄 MIGRATION HELPER
# ============================================

def migrate_from_old_risk_manager(old_daily_pnl: float = 0.0) -> bool:
    """
    Migration helper to transfer data from old in-memory risk manager
    
    🔄 Använd detta för att migrera befintlig daily P&L data
    """
    try:
        if old_daily_pnl != 0.0:
            logger.info(f"🔄 Migrating old daily P&L: {old_daily_pnl}")
            enhanced_risk_manager.update_daily_pnl(Decimal(str(old_daily_pnl)))
            return True
        return True
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False