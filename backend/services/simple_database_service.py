"""
🗄️ Simple Database Service (Clean Implementation)
==================================================
Production-ready database service for Supabase integration.
Replaces in-memory state with persistent storage.
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from backend.supabase_client import supabase

logger = logging.getLogger(__name__)


class SimpleDatabaseService:
    """
    🗄️ Clean database service for Supabase integration
    
    Provides simple, reliable database operations for trading bot.
    All methods handle errors gracefully and return sensible defaults.
    """
    
    def __init__(self):
        """Initialize database service"""
        self.client = supabase
        logger.info("✅ SimpleDatabaseService initialized with Supabase")
    
    def _clean_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix None metadata values for clean processing"""
        if 'metadata' in data and data['metadata'] is None:
            data['metadata'] = {}
        return data
    
    # ============================================
    # 📊 TRADES OPERATIONS
    # ============================================
    
    def create_trade(self, symbol: str, side: str, amount: float, 
                     price: float, strategy: str = None) -> Dict[str, Any]:
        """Create new trade record"""
        try:
            trade_data = {
                'symbol': symbol,
                'side': side,
                'amount': str(amount),
                'price': str(price),
                'cost': str(amount * price),
                'strategy': strategy,
                'metadata': {}
            }
            
            result = self.client.table('trades').insert(trade_data).execute()
            
            if result.data:
                trade = result.data[0]
                logger.info(f"✅ Trade created: {symbol} {side} {amount} @ {price}")
                return trade
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            logger.error(f"❌ Failed to create trade: {e}")
            return {}
    
    def get_all_trades(self) -> List[Dict[str, Any]]:
        """Get all trades"""
        try:
            result = (self.client.table('trades').select('*')
                      .order('created_at', desc=True).execute())
            trades = [self._clean_metadata(trade) for trade in result.data]
            logger.debug(f"📊 Retrieved {len(trades)} trades")
            return trades
        except Exception as e:
            logger.error(f"❌ Failed to get trades: {e}")
            return []
    
    def get_open_trades(self) -> List[Dict[str, Any]]:
        """Get only open trades"""
        try:
            result = self.client.table('trades').select('*').eq('status', 'open').execute()
            trades = [self._clean_metadata(trade) for trade in result.data]
            logger.debug(f"📊 Retrieved {len(trades)} open trades")
            return trades
        except Exception as e:
            logger.error(f"❌ Failed to get open trades: {e}")
            return []
    
    def close_trade(self, trade_id: int, pnl: float) -> bool:
        """Close trade and set P&L"""
        try:
            result = self.client.table('trades').update({
                'status': 'closed',
                'pnl': str(pnl)
            }).eq('id', trade_id).execute()
            
            if result.data:
                logger.info(f"✅ Trade {trade_id} closed with P&L: {pnl}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to close trade {trade_id}: {e}")
            return False
    
    # ============================================
    # 🎯 POSITIONS OPERATIONS  
    # ============================================
    
    def create_position(self, symbol: str, side: str, size: float, entry_price: float,
                       strategy: str = None) -> Dict[str, Any]:
        """Create or update position"""
        try:
            position_data = {
                'symbol': symbol,
                'side': side,
                'size': str(size),
                'entry_price': str(entry_price),
                'strategy': strategy,
                'metadata': {}
            }
            
            # Use upsert to handle updates
            result = self.client.table('positions').upsert(
                position_data, 
                on_conflict='symbol'
            ).execute()
            
            if result.data:
                position = result.data[0]
                logger.info(f"✅ Position created/updated: {symbol} {side} {size}")
                return position
            else:
                raise Exception("No data returned from upsert")
                
        except Exception as e:
            logger.error(f"❌ Failed to create/update position: {e}")
            return {}
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all active positions"""
        try:
            result = self.client.table('positions').select('*').execute()
            positions = [self._clean_metadata(pos) for pos in result.data]
            logger.debug(f"🎯 Retrieved {len(positions)} positions")
            return positions
        except Exception as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return []
    
    def close_position(self, symbol: str) -> bool:
        """Close position by removing it"""
        try:
            result = self.client.table('positions').delete().eq('symbol', symbol).execute()
            if result.data:
                logger.info(f"✅ Position closed: {symbol}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to close position {symbol}: {e}")
            return False
    
    # ============================================
    # ⚠️ RISK METRICS (CRITICAL!)
    # ============================================
    
    def get_today_risk_metrics(self) -> Optional[Dict[str, Any]]:
        """Get today's risk metrics (critical for trading limits!)"""
        try:
            today = date.today().isoformat()
            result = self.client.table('risk_metrics').select('*').eq('date', today).execute()
            
            if result.data:
                metrics = self._clean_metadata(result.data[0])
                logger.debug(f"⚠️ Today's risk: P&L={metrics.get('daily_pnl')}, Allowed={metrics.get('trading_allowed')}")
                return metrics
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get today's risk metrics: {e}")
            return None
    
    def update_daily_pnl(self, pnl: float, total_trades: int = None) -> bool:
        """Update today's P&L and trading metrics"""
        try:
            today = date.today().isoformat()
            
            update_data = {
                'date': today,
                'daily_pnl': str(pnl),
                'trading_allowed': pnl > -1000,  # Stop trading if loss > $1000
                'metadata': {'last_updated': datetime.now().isoformat()}
            }
            
            if total_trades is not None:
                update_data['total_trades'] = total_trades
            
            result = self.client.table('risk_metrics').upsert(
                update_data,
                on_conflict='date'
            ).execute()
            
            if result.data:
                trading_status = update_data['trading_allowed']
                logger.info(f"⚠️ Daily P&L updated: {pnl} (Trading allowed: {trading_status})")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update daily P&L: {e}")
            return False
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed based on risk metrics"""
        risk = self.get_today_risk_metrics()
        if risk:
            return risk.get('trading_allowed', True)
        return True  # Default to allow if no metrics
    
    # ============================================
    # 🚨 ALERTS
    # ============================================
    
    def create_alert(self, alert_type: str, severity: str, title: str, 
                    message: str) -> Dict[str, Any]:
        """Create system alert"""
        try:
            alert_data = {
                'type': alert_type,
                'severity': severity,
                'title': title,
                'message': message,
                'metadata': {}
            }
            
            result = self.client.table('alerts').insert(alert_data).execute()
            
            if result.data:
                alert = result.data[0]
                logger.warning(f"🚨 Alert created: {severity} - {title}")
                return alert
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            logger.error(f"❌ Failed to create alert: {e}")
            return {}
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent unacknowledged alerts"""
        try:
            result = self.client.table('alerts').select('*').eq('acknowledged', False).order('created_at', desc=True).limit(limit).execute()
            alerts = [self._clean_metadata(alert) for alert in result.data]
            logger.debug(f"🚨 Retrieved {len(alerts)} recent alerts")
            return alerts
        except Exception as e:
            logger.error(f"❌ Failed to get alerts: {e}")
            return []
    
    # ============================================
    # 🛠️ UTILITY OPERATIONS
    # ============================================
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            result = self.client.table('trades').select('id').limit(1).execute()
            logger.info("✅ Database health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    def get_trading_stats(self) -> Dict[str, Any]:
        """Get overall trading statistics"""
        try:
            # Get trades data
            trades = self.get_all_trades()
            positions = self.get_all_positions()
            
            # Calculate basic stats
            total_trades = len(trades)
            open_trades = len([t for t in trades if t.get('status') == 'open'])
            total_pnl = sum(float(t.get('pnl', 0)) for t in trades if t.get('pnl'))
            
            stats = {
                'total_trades': total_trades,
                'open_trades': open_trades, 
                'active_positions': len(positions),
                'total_pnl': round(total_pnl, 2),
                'database_status': 'connected',
                'trading_allowed': self.is_trading_allowed()
            }
            
            logger.info(f"📊 Trading stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get trading stats: {e}")
            return {'database_status': 'error', 'error': str(e)}


# Global database service instance
simple_db = SimpleDatabaseService()