"""
🗄️ Trading Database Models (Pydantic)
=====================================
Models that correspond to Supabase database schema.
Replaces in-memory state with persistent storage.
"""

from datetime import datetime
from datetime import date as Date
from decimal import Decimal
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ============================================
# 📊 TRADING MODELS
# ============================================

class TradeModel(BaseModel):
    """Individual trade record with P&L tracking"""
    id: Optional[int] = None
    symbol: str = Field(..., max_length=20)
    side: Literal['buy', 'sell']
    amount: Decimal = Field(..., decimal_places=8)
    price: Decimal = Field(..., decimal_places=8)
    cost: Decimal = Field(..., decimal_places=8)
    fee_cost: Decimal = Field(default=Decimal('0'), decimal_places=8)
    fee_currency: Optional[str] = Field(None, max_length=10)
    order_id: Optional[str] = Field(None, max_length=50)
    exchange_id: Optional[str] = Field(None, max_length=50)
    strategy: Optional[str] = Field(None, max_length=50)
    signal_strength: Optional[Decimal] = Field(None, decimal_places=4)
    probability: Optional[Decimal] = Field(None, decimal_places=4)
    pnl: Decimal = Field(default=Decimal('0'), decimal_places=8)
    status: Literal['open', 'closed', 'cancelled'] = 'open'
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class PositionModel(BaseModel):
    """Active trading position"""
    id: Optional[int] = None
    symbol: str = Field(..., max_length=20)
    side: Literal['long', 'short']
    size: Decimal = Field(..., decimal_places=8)
    entry_price: Decimal = Field(..., decimal_places=8)
    current_price: Optional[Decimal] = Field(None, decimal_places=8)
    unrealized_pnl: Decimal = Field(default=Decimal('0'), decimal_places=8)
    stop_loss: Optional[Decimal] = Field(None, decimal_places=8)
    take_profit: Optional[Decimal] = Field(None, decimal_places=8)
    strategy: Optional[str] = Field(None, max_length=50)
    risk_amount: Optional[Decimal] = Field(None, decimal_places=8)
    margin_used: Decimal = Field(default=Decimal('0'), decimal_places=8)
    opened_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class OrderModel(BaseModel):
    """Order execution record"""
    id: Optional[int] = None
    exchange_order_id: Optional[str] = Field(None, max_length=100)
    symbol: str = Field(..., max_length=20)
    type: Literal['market', 'limit', 'stop', 'stop_limit']
    side: Literal['buy', 'sell']
    amount: Decimal = Field(..., decimal_places=8)
    price: Optional[Decimal] = Field(None, decimal_places=8)
    filled: Decimal = Field(default=Decimal('0'), decimal_places=8)
    remaining: Optional[Decimal] = Field(None, decimal_places=8)
    cost: Decimal = Field(default=Decimal('0'), decimal_places=8)
    average: Optional[Decimal] = Field(None, decimal_places=8)
    fee_cost: Decimal = Field(default=Decimal('0'), decimal_places=8)
    fee_currency: Optional[str] = Field(None, max_length=10)
    status: Literal['pending', 'open', 'closed', 'cancelled', 'rejected'] = 'pending'
    strategy: Optional[str] = Field(None, max_length=50)
    signal_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class RiskMetricsModel(BaseModel):
    """Daily risk metrics (CRITICAL for trading limits)"""
    id: Optional[int] = None
    date: Date = Field(default_factory=lambda: Date.today())
    daily_pnl: Decimal = Field(default=Decimal('0'), decimal_places=8)
    daily_loss: Decimal = Field(default=Decimal('0'), decimal_places=8)
    max_drawdown: Decimal = Field(default=Decimal('0'), decimal_places=8)
    win_rate: Decimal = Field(default=Decimal('0'), decimal_places=4)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    largest_win: Decimal = Field(default=Decimal('0'), decimal_places=8)
    largest_loss: Decimal = Field(default=Decimal('0'), decimal_places=8)
    consecutive_losses: int = 0
    risk_score: Decimal = Field(default=Decimal('0'), decimal_places=4)
    trading_allowed: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
            Date: lambda v: v.isoformat()
        }


class AlertModel(BaseModel):
    """System alerts and notifications"""
    id: Optional[int] = None
    type: Literal['risk', 'trade', 'system', 'error']
    severity: Literal['low', 'medium', 'high', 'critical']
    title: str = Field(..., max_length=255)
    message: str
    symbol: Optional[str] = Field(None, max_length=20)
    strategy: Optional[str] = Field(None, max_length=50)
    acknowledged: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BalanceSnapshotModel(BaseModel):
    """Account balance snapshot"""
    id: Optional[int] = None
    total_balance: Decimal = Field(..., decimal_places=8)
    available_balance: Decimal = Field(..., decimal_places=8)
    used_balance: Decimal = Field(..., decimal_places=8)
    currencies: Dict[str, Any] = Field(default_factory=dict)
    exchange: str = 'bitfinex'
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class StrategyPerformanceModel(BaseModel):
    """Strategy performance metrics"""
    id: Optional[int] = None
    strategy_name: str = Field(..., max_length=50)
    date: Date = Field(default_factory=lambda: Date.today())
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: Decimal = Field(default=Decimal('0'), decimal_places=8)
    win_rate: Decimal = Field(default=Decimal('0'), decimal_places=4)
    avg_win: Decimal = Field(default=Decimal('0'), decimal_places=8)
    avg_loss: Decimal = Field(default=Decimal('0'), decimal_places=8)
    max_drawdown: Decimal = Field(default=Decimal('0'), decimal_places=8)
    sharpe_ratio: Decimal = Field(default=Decimal('0'), decimal_places=6)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
            Date: lambda v: v.isoformat()
        }


# ============================================
# 📋 REQUEST/RESPONSE MODELS  
# ============================================

class CreateTradeRequest(BaseModel):
    """Request to create a new trade"""
    symbol: str
    side: Literal['buy', 'sell']
    amount: Decimal
    price: Decimal
    strategy: Optional[str] = None
    signal_strength: Optional[Decimal] = None
    probability: Optional[Decimal] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdatePositionRequest(BaseModel):
    """Request to update position"""
    current_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None


class CreateAlertRequest(BaseModel):
    """Request to create alert"""
    type: Literal['risk', 'trade', 'system', 'error']
    severity: Literal['low', 'medium', 'high', 'critical']
    title: str
    message: str
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================
# 🎯 TRADE SIGNAL MODEL
# ============================================

class TradeSignal(BaseModel):
    """Enhanced trade signal with database integration"""
    action: Literal['buy', 'sell', 'hold']
    symbol: str
    amount: Decimal
    price: Optional[Decimal] = None
    confidence: Decimal = Field(..., ge=0, le=1, decimal_places=4)
    probability: Decimal = Field(..., ge=0, le=1, decimal_places=4)
    strategy: str
    reasoning: str
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    risk_amount: Optional[Decimal] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_trade_model(self) -> TradeModel:
        """Convert signal to trade model for database storage"""
        return TradeModel(
            symbol=self.symbol,
            side=self.action,  # buy/sell maps directly
            amount=self.amount,
            price=self.price or Decimal('0'),
            cost=self.amount * (self.price or Decimal('0')),
            strategy=self.strategy,
            signal_strength=self.confidence,
            probability=self.probability,
            metadata={
                'reasoning': self.reasoning,
                'stop_loss': str(self.stop_loss) if self.stop_loss else None,
                'take_profit': str(self.take_profit) if self.take_profit else None,
                **self.metadata
            }
        )

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }