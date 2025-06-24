"""
🗄️ Database Service (Supabase Integration)
===========================================
Replaces in-memory state with persistent Supabase storage.
Critical for production trading - no more data loss on restart!
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from backend.supabase_client import supabase
from backend.models.trading_models import (
    TradeModel, PositionModel, OrderModel, RiskMetricsModel, 
    AlertModel, BalanceSnapshotModel
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    🗄️ Centralized database operations using Supabase
    
    Replaces all in-memory storage with persistent database storage.
    Critical for production trading systems.
    """
    
    def __init__(self):
        """Initialize database service"""
        self.client = supabase
        logger.info("✅ DatabaseService initialized with Supabase")
    
    # ============================================
    # 📊 TRADES OPERATIONS
    # ============================================
    
    def create_trade(self, trade: TradeModel) -> TradeModel:
        """Create new trade in database"""
        try:
            trade_data = trade.dict(exclude={'id', 'created_at', 'updated_at'})
            
            # Convert Decimal to string for Supabase
            for key, value in trade_data.items():
                if isinstance(value, Decimal):
                    trade_data[key] = str(value)
            
            result = self.client.table('trades').insert(trade_data).execute()
            
            if result.data:
                created_trade = TradeModel(**result.data[0])
                logger.info(f"✅ Trade created: {created_trade.symbol} {created_trade.side} {created_trade.amount}")
                return created_trade
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            logger.error(f"❌ Failed to create trade: {e}")
            raise
    
    def get_open_trades(self) -> List[TradeModel]:
        """Get all open trades"""
        try:
            result = self.client.table('trades').select("*").eq('status', 'open').execute()
            trades = [TradeModel(**trade) for trade in result.data]
            logger.debug(f"📊 Retrieved {len(trades)} open trades")
            return trades
        except Exception as e:
            logger.error(f"❌ Failed to get open trades: {e}")
            return []
    
    def close_trade(self, trade_id: int, pnl: Decimal) -> bool:
        """Close trade and update P&L"""
        try:
            result = self.client.table('trades').update({
                'status': 'closed',
                'pnl': str(pnl),
                'closed_at': datetime.now().isoformat()
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
    
    def create_position(self, position: PositionModel) -> PositionModel:
        """Create or update position"""
        try:
            position_data = position.dict(exclude={'id', 'last_updated'})
            
            # Convert Decimal to string
            for key, value in position_data.items():
                if isinstance(value, Decimal):
                    position_data[key] = str(value)
            
            # Use upsert to handle position updates
            result = self.client.table('positions').upsert(
                position_data, 
                on_conflict='symbol'
            ).execute()
            
            if result.data:
                created_position = PositionModel(**result.data[0])
                logger.info(f"✅ Position created/updated: {created_position.symbol} {created_position.side}")
                return created_position
            else:
                raise Exception("No data returned from upsert")
                
        except Exception as e:
            logger.error(f"❌ Failed to create/update position: {e}")
            raise
    
    def get_all_positions(self) -> List[PositionModel]:
        """Get all active positions"""
        try:
            result = self.client.table('positions').select("*").execute()
            positions = [PositionModel(**pos) for pos in result.data]
            logger.debug(f"🎯 Retrieved {len(positions)} positions")
            return positions
        except Exception as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return []
    
    def close_position(self, symbol: str) -> bool:
        """Close position by symbol"""
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
    # ⚠️ RISK METRICS OPERATIONS (CRITICAL!)
    # ============================================
    
    def get_daily_risk_metrics(self, target_date: date = None) -> Optional[RiskMetricsModel]:
        """Get risk metrics for specific date (critical for trading limits!)"""
        if target_date is None:
            target_date = date.today()
            
        try:
            result = self.client.table('risk_metrics').select("*").eq(
                'date', target_date.isoformat()
            ).execute()
            
            if result.data:
                metrics = RiskMetricsModel(**result.data[0])
                logger.debug(f"⚠️ Risk metrics for {target_date}: P&L={metrics.daily_pnl}, Allowed={metrics.trading_allowed}")
                return metrics
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get risk metrics for {target_date}: {e}")
            return None
    
    def update_daily_risk_metrics(self, metrics: RiskMetricsModel) -> bool:
        """Update daily risk metrics (critical for preventing overtrading!)"""
        try:
            metrics_data = metrics.dict(exclude={'id', 'created_at', 'updated_at'})
            
            # Convert Decimal to string
            for key, value in metrics_data.items():
                if isinstance(value, Decimal):
                    metrics_data[key] = str(value)
                elif isinstance(value, date):
                    metrics_data[key] = value.isoformat()
            
            result = self.client.table('risk_metrics').upsert(
                metrics_data,
                on_conflict='date'
            ).execute()
            
            if result.data:
                logger.info(f"⚠️ Risk metrics updated for {metrics.date}: P&L={metrics.daily_pnl}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update risk metrics: {e}")
            return False
    
    # ============================================
    # 📈 ORDERS OPERATIONS
    # ============================================
    
    def create_order(self, order: OrderModel) -> OrderModel:
        """Create order record"""
        try:
            order_data = order.dict(exclude={'id', 'created_at', 'updated_at'})
            
            # Convert Decimal to string
            for key, value in order_data.items():
                if isinstance(value, Decimal):
                    order_data[key] = str(value)
            
            result = self.client.table('orders').insert(order_data).execute()
            
            if result.data:
                created_order = OrderModel(**result.data[0])
                logger.info(f"📈 Order created: {created_order.symbol} {created_order.type} {created_order.side}")
                return created_order
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            logger.error(f"❌ Failed to create order: {e}")
            raise
    
    def update_order_status(self, order_id: int, status: str, filled: Decimal = None) -> bool:
        """Update order status and filled amount"""
        try:
            update_data = {'status': status}
            if filled is not None:
                update_data['filled'] = str(filled)
                if status == 'closed':
                    update_data['filled_at'] = datetime.now().isoformat()
            
            result = self.client.table('orders').update(update_data).eq('id', order_id).execute()
            
            if result.data:
                logger.info(f"📈 Order {order_id} updated to {status}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update order {order_id}: {e}")
            return False
    
    # ============================================
    # 🚨 ALERTS OPERATIONS
    # ============================================
    
    def create_alert(self, alert: AlertModel) -> AlertModel:
        """Create system alert"""
        try:
            alert_data = alert.dict(exclude={'id', 'created_at'})
            
            result = self.client.table('alerts').insert(alert_data).execute()
            
            if result.data:
                created_alert = AlertModel(**result.data[0])
                logger.warning(f"🚨 Alert created: {created_alert.severity} - {created_alert.title}")
                return created_alert
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            logger.error(f"❌ Failed to create alert: {e}")
            raise
    
    def get_unacknowledged_alerts(self) -> List[AlertModel]:
        """Get all unacknowledged alerts"""
        try:
            result = self.client.table('alerts').select("*").eq('acknowledged', False).order('created_at', desc=True).execute()
            alerts = [AlertModel(**alert) for alert in result.data]
            logger.debug(f"🚨 Retrieved {len(alerts)} unacknowledged alerts")
            return alerts
        except Exception as e:
            logger.error(f"❌ Failed to get alerts: {e}")
            return []
    
    # ============================================
    # 💰 BALANCE OPERATIONS
    # ============================================
    
    def save_balance_snapshot(self, snapshot: BalanceSnapshotModel) -> bool:
        """Save balance snapshot"""
        try:
            snapshot_data = snapshot.dict(exclude={'id', 'created_at'})
            
            # Convert Decimal to string
            for key, value in snapshot_data.items():
                if isinstance(value, Decimal):
                    snapshot_data[key] = str(value)
            
            result = self.client.table('balance_snapshots').insert(snapshot_data).execute()
            
            if result.data:
                logger.info(f"💰 Balance snapshot saved: {snapshot.total_balance}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to save balance snapshot: {e}")
            return False
    
    # ============================================
    # 🛠️ UTILITY OPERATIONS
    # ============================================
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            result = self.client.table('risk_metrics').select("id").limit(1).execute()
            logger.info("✅ Database health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    def get_trading_stats(self) -> Dict[str, Any]:
        """Get overall trading statistics"""
        try:
            # Get total trades
            trades_result = self.client.table('trades').select("id, pnl, status").execute()
            trades = trades_result.data
            
            # Get active positions
            positions_result = self.client.table('positions').select("id").execute()
            positions = positions_result.data
            
            # Calculate stats
            total_trades = len(trades)
            total_pnl = sum(float(trade.get('pnl', 0)) for trade in trades if trade.get('pnl'))
            open_trades = len([t for t in trades if t.get('status') == 'open'])
            
            stats = {
                'total_trades': total_trades,
                'open_trades': open_trades,
                'active_positions': len(positions),
                'total_pnl': total_pnl,
                'database_status': 'connected'
            }
            
            logger.info(f"📊 Trading stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get trading stats: {e}")
            return {'database_status': 'error', 'error': str(e)}


# Global database service instance
db_service = DatabaseService()