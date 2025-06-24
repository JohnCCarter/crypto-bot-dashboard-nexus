"""
🗄️ Simple Trading Models (Minimal Supabase Schema)
==================================================
Simplified models that match our minimal database schema.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ============================================
# 📊 SIMPLE TRADING MODELS
# ============================================

class SimpleTradeModel(BaseModel):
    """Minimal trade record"""
    id: Optional[int] = None
    symbol: str = Field(..., max_length=20)
    side: str = Field(..., max_length=10)  # 'buy' or 'sell'
    amount: Decimal = Field(..., decimal_places=8)
    price: Decimal = Field(..., decimal_places=8)
    cost: Decimal = Field(..., decimal_places=8)
    status: str = Field(default='open', max_length=20)
    strategy: Optional[str] = Field(None, max_length=50)
    pnl: Decimal = Field(default=Decimal('0'), decimal_places=8)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class SimplePositionModel(BaseModel):
    """Minimal position record"""
    id: Optional[int] = None
    symbol: str = Field(..., max_length=20)
    side: str = Field(..., max_length=10)  # 'long' or 'short'
    size: Decimal = Field(..., decimal_places=8)
    entry_price: Decimal = Field(..., decimal_places=8)
    current_price: Optional[Decimal] = Field(None, decimal_places=8)
    unrealized_pnl: Decimal = Field(default=Decimal('0'), decimal_places=8)
    strategy: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    opened_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class SimpleRiskMetricsModel(BaseModel):
    """Minimal risk metrics (CRITICAL for trading limits)"""
    id: Optional[int] = None
    date: date = Field(default_factory=lambda: date.today())
    daily_pnl: Decimal = Field(default=Decimal('0'), decimal_places=8)
    total_trades: int = 0
    trading_allowed: bool = True
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class SimpleAlertModel(BaseModel):
    """Simple system alerts"""
    id: Optional[int] = None
    type: str = Field(..., max_length=20)
    severity: str = Field(..., max_length=10)
    title: str = Field(..., max_length=255)
    message: str
    acknowledged: bool = False
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SimpleOrderModel(BaseModel):
    """Minimal order record"""
    id: Optional[int] = None
    symbol: str = Field(..., max_length=20)
    type: str = Field(..., max_length=20)
    side: str = Field(..., max_length=10)
    amount: Decimal = Field(..., decimal_places=8)
    price: Optional[Decimal] = Field(None, decimal_places=8)
    status: str = Field(default='pending', max_length=20)
    strategy: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# ============================================
# 🎯 TRADE SIGNAL (FOR STRATEGIES)
# ============================================

class SimpleTradeSignal(BaseModel):
    """Simple trade signal for strategies"""
    action: Literal['buy', 'sell', 'hold']
    symbol: str
    amount: Decimal
    price: Optional[Decimal] = None
    confidence: Decimal = Field(..., ge=0, le=1, decimal_places=4)
    strategy: str
    reasoning: str = ""
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_trade_model(self) -> SimpleTradeModel:
        """Convert signal to trade model for database storage"""
        return SimpleTradeModel(
            symbol=self.symbol,
            side=self.action,  # 'buy' or 'sell'
            amount=self.amount,
            price=self.price or Decimal('0'),
            cost=self.amount * (self.price or Decimal('0')),
            strategy=self.strategy,
            metadata={
                'reasoning': self.reasoning,
                'confidence': str(self.confidence),
                **self.metadata
            }
        )

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }