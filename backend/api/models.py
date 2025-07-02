"""
Pydantic models for API request and response validation.
"""

from typing import Dict, Optional, Any, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    """API status response model."""
    
    status: str = Field(..., description="Current system status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Current environment")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Health status")


class Balance(BaseModel):
    """Balance model for a single currency."""
    
    currency: str = Field(..., description="Currency code")
    available: float = Field(..., description="Available balance")
    reserved: float = Field(..., description="Reserved balance")
    total: float = Field(..., description="Total balance")


class BalancesResponse(BaseModel):
    """Response model for multiple balances."""
    
    balances: List[Balance] = Field(..., description="List of balances")


class OrderType(str, Enum):
    """Order type enumeration."""
    
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(str, Enum):
    """Order side enumeration."""
    
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Order(BaseModel):
    """Order model."""
    
    id: str = Field(..., description="Order ID")
    symbol: str = Field(..., description="Trading pair symbol")
    type: OrderType = Field(..., description="Order type")
    side: OrderSide = Field(..., description="Order side")
    price: float = Field(..., description="Order price")
    amount: float = Field(..., description="Order amount")
    status: OrderStatus = Field(..., description="Order status")
    created_at: datetime = Field(..., description="Order creation timestamp")
    cancelled_at: Optional[datetime] = Field(
        None, description="Order cancellation timestamp"
    )
    executed_at: Optional[datetime] = Field(
        None, description="Order execution timestamp"
    )


class OrdersResponse(BaseModel):
    """Response model for multiple orders."""
    
    orders: List[Order] = Field(..., description="List of orders")


class OrderRequest(BaseModel):
    """Request model for placing an order."""
    
    symbol: str = Field(..., description="Trading pair symbol")
    type: OrderType = Field(..., description="Order type")
    side: OrderSide = Field(..., description="Order side")
    price: float = Field(..., description="Order price")
    amount: float = Field(..., description="Order amount")
    stop_price: Optional[float] = Field(
        None, description="Stop price for stop orders"
    )
    trailing_amount: Optional[float] = Field(
        None, description="Trailing amount for trailing stop orders"
    )


# Alias for OrderRequest for backward compatibility
OrderCreateModel = OrderRequest


class Strategy(BaseModel):
    """Strategy model for backtesting."""
    
    id: str = Field(..., description="Strategy ID")
    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")


class StrategiesResponse(BaseModel):
    """Response model for available strategies."""
    
    strategies: List[Strategy] = Field(..., description="List of strategies")


class BacktestRequest(BaseModel):
    """Request model for running a backtest."""
    
    strategy_id: str = Field(..., description="Strategy ID")
    symbol: str = Field(..., description="Trading pair symbol")
    timeframe: str = Field(..., description="Timeframe for the backtest")
    start_date: datetime = Field(..., description="Start date for the backtest")
    end_date: datetime = Field(..., description="End date for the backtest")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Strategy parameters"
    )


class BacktestTrade(BaseModel):
    """Trade model for backtest results."""
    
    id: int = Field(..., description="Trade ID")
    timestamp: datetime = Field(..., description="Trade timestamp")
    type: str = Field(..., description="Trade type (buy/sell)")
    price: float = Field(..., description="Trade price")
    amount: float = Field(..., description="Trade amount")
    profit: Optional[float] = Field(None, description="Trade profit/loss")


class BacktestResults(BaseModel):
    """Results model for backtest."""
    
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: float = Field(..., description="Win rate")
    profit_factor: float = Field(..., description="Profit factor")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    net_profit: float = Field(..., description="Net profit")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")


class BacktestResponse(BaseModel):
    """Response model for backtest results."""
    
    id: str = Field(..., description="Backtest ID")
    strategy: str = Field(..., description="Strategy ID")
    symbol: str = Field(..., description="Trading pair symbol")
    timeframe: str = Field(..., description="Timeframe for the backtest")
    start_date: datetime = Field(..., description="Start date for the backtest")
    end_date: datetime = Field(..., description="End date for the backtest")
    status: str = Field(..., description="Backtest status")
    results: BacktestResults = Field(..., description="Backtest results")
    trades: Optional[List[BacktestTrade]] = Field(
        None, description="List of trades"
    ) 

# Position models
class Position(BaseModel):
    """Position model."""
    
    id: str = Field(..., description="Position ID")
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., description="Position side (buy/sell)")
    amount: float = Field(..., description="Position amount")
    entry_price: float = Field(..., description="Entry price")
    mark_price: float = Field(..., description="Current mark price")
    pnl: float = Field(..., description="Unrealized profit/loss")
    pnl_percentage: float = Field(..., description="Profit/loss percentage")
    timestamp: int = Field(..., description="Position timestamp")
    contracts: float = Field(..., description="Number of contracts")
    notional: float = Field(..., description="Notional value")
    collateral: float = Field(..., description="Collateral amount")
    margin_mode: str = Field(..., description="Margin mode (cross/isolated/spot)")
    maintenance_margin: float = Field(..., description="Maintenance margin")
    position_type: str = Field(..., description="Position type (margin/spot)")
    leverage: float = Field(..., description="Position leverage")


class PositionsResponse(BaseModel):
    """Response model for multiple positions."""
    
    positions: List[Position] = Field(..., description="List of positions")


# Config models
class StrategyWeight(BaseModel):
    """Strategy weight configuration."""
    
    strategy_name: str = Field(..., description="Strategy name")
    weight: float = Field(..., description="Strategy weight")
    min_confidence: float = Field(..., description="Minimum confidence threshold")
    enabled: bool = Field(..., description="Whether the strategy is enabled")


class StrategyWeightsResponse(BaseModel):
    """Response model for strategy weights."""
    
    strategy_weights: List[StrategyWeight] = Field(..., description="List of strategy weights")
    total_strategies: int = Field(..., description="Total number of strategies")
    enabled_strategies: int = Field(..., description="Number of enabled strategies")


class StrategyParamsResponse(BaseModel):
    """Response model for strategy parameters."""
    
    strategy_name: str = Field(..., description="Strategy name")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters")


class UpdateStrategyWeightRequest(BaseModel):
    """Request model for updating strategy weight."""
    
    weight: float = Field(..., description="New weight value", ge=0.0, le=1.0)


class ProbabilityConfig(BaseModel):
    """Probability configuration."""
    
    probability_settings: Dict[str, Any] = Field(..., description="Probability settings")
    risk_config: Dict[str, Any] = Field(..., description="Risk configuration")


class UpdateProbabilitySettingsRequest(BaseModel):
    """Request model for updating probability settings."""
    
    probability_settings: Dict[str, Any] = Field(..., description="New probability settings")


class ConfigSummary(BaseModel):
    """Configuration summary."""
    
    config_file: str = Field(..., description="Configuration file path")
    config_valid: bool = Field(..., description="Whether the configuration is valid")
    validation_errors: List[str] = Field([], description="Validation errors")
    enabled_strategies: List[str] = Field(..., description="Enabled strategies")
    total_strategy_count: int = Field(..., description="Total number of strategies")
    risk_management: Dict[str, Any] = Field(..., description="Risk management settings")
    probability_framework: Dict[str, Any] = Field(..., description="Probability framework settings")


class ValidationResponse(BaseModel):
    """Configuration validation response."""
    
    valid: bool = Field(..., description="Whether the configuration is valid")
    errors: List[str] = Field(..., description="Validation errors")
    error_count: int = Field(..., description="Number of validation errors")


class ReloadConfigResponse(BaseModel):
    """Response model for config reload."""
    
    message: str = Field(..., description="Result message")
    config_valid: bool = Field(..., description="Whether the configuration is valid")
    validation_errors: List[str] = Field(..., description="Validation errors")


# Bot control models
class BotStatusResponse(BaseModel):
    """Bot status response model."""
    
    status: str = Field(..., description="Current bot status (running/stopped)")
    uptime: float = Field(..., description="Bot uptime in seconds")
    last_update: Optional[str] = Field(None, description="Last update timestamp")
    thread_alive: bool = Field(..., description="Whether the bot thread is alive")
    cycle_count: int = Field(..., description="Number of completed cycles")
    last_cycle_time: Optional[str] = Field(None, description="Last cycle timestamp")
    error: Optional[str] = Field(None, description="Error message if any")


class BotActionResponse(BaseModel):
    """Bot action response model."""
    
    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Response message")
    status: str = Field(..., description="Current bot status")


# Market data models
class OHLCV(BaseModel):
    """OHLCV candle model."""
    
    timestamp: int = Field(..., description="Candle timestamp in milliseconds")
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: float = Field(..., description="Volume")


class OHLCVResponse(BaseModel):
    """Response model for OHLCV data."""
    
    data: List[List[float]] = Field(..., description="OHLCV data")


class OrderBookEntry(BaseModel):
    """Order book entry model."""
    
    price: float = Field(..., description="Price level")
    amount: float = Field(..., description="Amount at price level")


class OrderBook(BaseModel):
    """Order book model."""
    
    bids: List[List[float]] = Field(..., description="Bid orders")
    asks: List[List[float]] = Field(..., description="Ask orders")
    timestamp: Optional[int] = Field(None, description="Timestamp")
    datetime: Optional[str] = Field(None, description="Datetime in ISO format")
    nonce: Optional[int] = Field(None, description="Nonce")


class Ticker(BaseModel):
    """Ticker model."""
    
    symbol: str = Field(..., description="Trading pair symbol")
    bid: float = Field(..., description="Best bid price")
    ask: float = Field(..., description="Best ask price")
    last: float = Field(..., description="Last trade price")
    high: float = Field(..., description="24h high")
    low: float = Field(..., description="24h low")
    change: float = Field(..., description="24h price change")
    percentage: float = Field(..., description="24h percentage change")
    volume: float = Field(..., description="24h volume")
    timestamp: int = Field(..., description="Timestamp")


class Trade(BaseModel):
    """Trade model."""
    
    id: str = Field(..., description="Trade ID")
    timestamp: int = Field(..., description="Trade timestamp")
    datetime: str = Field(..., description="Trade datetime")
    symbol: str = Field(..., description="Trading pair symbol")
    order: Optional[str] = Field(None, description="Order ID")
    type: Optional[str] = Field(None, description="Trade type")
    side: str = Field(..., description="Trade side (buy/sell)")
    price: float = Field(..., description="Trade price")
    amount: float = Field(..., description="Trade amount")
    cost: float = Field(..., description="Trade cost")
    fee: Optional[Dict[str, Any]] = Field(None, description="Trade fee")


class TradesResponse(BaseModel):
    """Response model for recent trades."""
    
    trades: List[Trade] = Field(..., description="List of trades")


class Market(BaseModel):
    """Market model."""
    
    id: str = Field(..., description="Market ID")
    symbol: str = Field(..., description="Trading pair symbol")
    base: str = Field(..., description="Base currency")
    quote: str = Field(..., description="Quote currency")
    active: bool = Field(..., description="Whether the market is active")


class MarketsResponse(BaseModel):
    """Response model for available markets."""
    
    markets: List[Market] = Field(..., description="List of markets")

# Risk management and portfolio models
class ResponseStatus(str, Enum):
    """API response status enumeration."""
    
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ProbabilityDataModel(BaseModel):
    """Probability data model for trade signals."""
    
    probability_buy: float = Field(..., description="Buy probability")
    probability_sell: float = Field(..., description="Sell probability")
    probability_hold: float = Field(..., description="Hold probability")
    confidence: float = Field(..., description="Overall confidence level")
    
    def dict(self) -> Dict[str, Any]:
        """Override dict method to return a dictionary representation."""
        return {
            "probability_buy": self.probability_buy,
            "probability_sell": self.probability_sell,
            "probability_hold": self.probability_hold,
            "confidence": self.confidence
        }
    
    def get_risk_score(self) -> float:
        """Calculate risk score based on probabilities."""
        # Higher risk when probabilities are close or confidence is low
        highest_prob = max(self.probability_buy, self.probability_sell, self.probability_hold)
        second_highest = sorted([self.probability_buy, self.probability_sell, self.probability_hold])[-2]
        
        # How close are the top probabilities (normalized to 0-1)
        probability_gap = 1.0 - (highest_prob - second_highest)
        
        # Confidence factor (inverse - lower confidence means higher risk)
        confidence_factor = 1.0 - self.confidence
        
        # Combine factors (weighted average)
        risk_score = 0.6 * probability_gap + 0.4 * confidence_factor
        
        return min(1.0, max(0.0, risk_score))


class OrderData(BaseModel):
    """Order data model for risk validation."""
    
    symbol: str = Field(..., description="Trading pair symbol")
    side: OrderSide = Field(..., description="Order side (buy/sell)")
    type: OrderType = Field(..., description="Order type")
    amount: float = Field(..., description="Order amount")
    price: float = Field(..., description="Order price")
    stop_price: Optional[float] = Field(None, description="Stop price if applicable")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    
    def dict(self) -> Dict[str, Any]:
        """Override dict method to return a dictionary representation."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "type": self.type,
            "amount": self.amount,
            "price": self.price,
            "stop_price": self.stop_price,
            "take_profit": self.take_profit,
            "stop_loss": self.stop_loss
        }


class OrderValidationResponse(BaseModel):
    """Response model for order validation."""
    
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    valid: bool = Field(..., description="Whether the order is valid")
    errors: List[str] = Field([], description="Validation errors")
    risk_assessment: Optional[Dict[str, Any]] = Field(
        None, description="Risk assessment details"
    )


class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment."""
    
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment details")


class RiskScoreResponse(BaseModel):
    """Response model for risk score calculation."""
    
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    symbol: str = Field(..., description="Trading pair symbol")
    risk_score: float = Field(..., description="Calculated risk score")
    risk_level: str = Field(..., description="Risk level description")
    probability_data: Dict[str, float] = Field(..., description="Probability data")


class SignalData(BaseModel):
    """Trading signal data."""
    
    symbol: str = Field(..., description="Trading pair symbol")
    signal_type: str = Field(..., description="Signal type (buy/sell/hold)")
    strength: float = Field(..., description="Signal strength")
    confidence: float = Field(..., description="Signal confidence")
    timestamp: datetime = Field(..., description="Signal timestamp")
    source: str = Field(..., description="Signal source (strategy name)")
    indicators: Dict[str, Any] = Field(..., description="Indicator values")
    price: float = Field(..., description="Current price")


class StrategySignalRequest(BaseModel):
    """Request model for processing strategy signals."""
    
    signals: List[SignalData] = Field(..., description="List of strategy signals")
    timestamp: datetime = Field(..., description="Request timestamp")


class StrategySignalResponse(BaseModel):
    """Response model for strategy signal processing."""
    
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    actions: List[Dict[str, Any]] = Field(..., description="Recommended actions")
    timestamp: datetime = Field(..., description="Response timestamp")


class AllocationItem(BaseModel):
    """Portfolio allocation item."""
    
    symbol: str = Field(..., description="Trading pair symbol")
    percentage: float = Field(..., description="Allocation percentage")
    amount: Optional[float] = Field(None, description="Allocation amount")
    action: str = Field(..., description="Required action (buy/sell/hold)")
    current_allocation: Optional[float] = Field(None, description="Current allocation")
    target_allocation: float = Field(..., description="Target allocation")


class RiskProfile(str, Enum):
    """Risk profile enumeration."""
    
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class PortfolioAllocationRequest(BaseModel):
    """Request model for portfolio allocation."""
    
    signals: List[SignalData] = Field(..., description="List of strategy signals")
    risk_profile: RiskProfile = Field(..., description="Risk profile")
    max_allocation_percent: float = Field(
        0.8, description="Maximum allocation percentage", ge=0.0, le=1.0
    )
    timestamp: datetime = Field(..., description="Request timestamp")


class PortfolioAllocationResponse(BaseModel):
    """Response model for portfolio allocation."""
    
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    allocations: List[AllocationItem] = Field(..., description="Allocation details")
    timestamp: datetime = Field(..., description="Response timestamp") 