"""
Live Portfolio Service - Kopplar live marknadsdata till portfolio management
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from backend.services.balance_service import fetch_balances
from backend.services.live_data_service import LiveDataService

logger = logging.getLogger(__name__)


@dataclass
class LivePosition:
    """Representation av en live position med marknadsdata"""

    symbol: str
    amount: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    market_value: float
    timestamp: datetime


@dataclass
class LivePortfolioSnapshot:
    """Komplett portfolio snapshot med live marknadsdata"""

    total_value: float
    available_balance: float
    positions: List[LivePosition]
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    timestamp: datetime
    market_data_quality: Dict[str, bool]


class LivePortfolioService:
    """Service för att hantera portfolio med live marknadsdata"""

    def __init__(self, exchange_config: Dict = None):
        """
        Initialize live portfolio service

        Args:
            exchange_config: Exchange configuration for live data
        """
        if exchange_config is None:
            exchange_config = {}

        self.live_data = LiveDataService(
            exchange_id=exchange_config.get("exchange_id", "bitfinex"),
            api_key=exchange_config.get("api_key"),
            api_secret=exchange_config.get("api_secret"),
        )

        logger.info("LivePortfolioService initialized")

    def get_balance(self):
        """Get balance using the existing balance service function"""
        try:
            balance_data = fetch_balances()
            # Extract 'free' balances which are available for trading
            result = {}
            for currency, data in balance_data.get("info", {}).items():
                free_amount = data.get("free", 0)
                if free_amount > 0:
                    result[currency] = free_amount
            return result
        except Exception as e:
            logger.error(
                f"❌ [LivePortfolio] CRITICAL: Failed to fetch live balances: {e}. "
                f"NO MOCK DATA will be provided for trading safety."
            )
            # Return empty dict instead of mock data for trading safety
            # This ensures trading bot knows balance data is unavailable
            return {}

    def get_live_portfolio_snapshot(
        self, symbols: List[str] = None
    ) -> LivePortfolioSnapshot:
        """
        Hämta komplett portfolio snapshot med live pricing

        Args:
            symbols: List of symbols to get live data for

        Returns:
            LivePortfolioSnapshot with current market values
        """
        try:
            logger.info("📊 [LivePortfolio] Generating live portfolio snapshot...")

            if symbols is None:
                symbols = ["BTC/USD", "ETH/USD"]  # Default symbols

            # Get current balances
            balances = self.get_balance()
            logger.info(f"💰 [LivePortfolio] Current balances: {balances}")

            # Get live positions with market pricing
            live_positions = []
            total_unrealized_pnl = 0
            market_data_quality = {}

            for symbol in symbols:
                try:
                    # Get live market context
                    market_context = self.live_data.get_live_market_context(symbol)
                    current_price = market_context["current_price"]

                    # Check if we have a position in this symbol
                    base_currency = symbol.split("/")[0]
                    position_amount = balances.get(base_currency, 0)

                    if position_amount > 0:
                        # Calculate position metrics
                        # Note: This assumes we bought at some previous price
                        # In real implementation, this would come from order history
                        entry_price = current_price * 0.95  # Mock entry price for demo

                        market_value = position_amount * current_price
                        cost_basis = position_amount * entry_price
                        unrealized_pnl = market_value - cost_basis
                        unrealized_pnl_pct = (
                            (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                        )

                        position = LivePosition(
                            symbol=symbol,
                            amount=position_amount,
                            entry_price=entry_price,
                            current_price=current_price,
                            unrealized_pnl=unrealized_pnl,
                            unrealized_pnl_pct=unrealized_pnl_pct,
                            market_value=market_value,
                            timestamp=datetime.now(),
                        )

                        live_positions.append(position)
                        total_unrealized_pnl += unrealized_pnl

                        logger.info(
                            f"📈 [LivePortfolio] {symbol}: {position_amount:.6f} @ ${current_price:.2f} "
                            f"(PnL: ${unrealized_pnl:.2f})"
                        )

                    market_data_quality[symbol] = True

                except Exception as e:
                    logger.error(
                        f"❌ [LivePortfolio] Failed to get live data for {symbol}: {e}"
                    )
                    market_data_quality[symbol] = False
                    continue

            # Calculate total portfolio value
            total_position_value = sum(pos.market_value for pos in live_positions)
            cash_balance = balances.get("USD", 0)
            total_value = total_position_value + cash_balance

            # Calculate total PnL percentage
            total_cost_basis = total_position_value - total_unrealized_pnl
            total_unrealized_pnl_pct = (
                (total_unrealized_pnl / total_cost_basis) * 100
                if total_cost_basis > 0
                else 0
            )

            snapshot = LivePortfolioSnapshot(
                total_value=total_value,
                available_balance=cash_balance,
                positions=live_positions,
                total_unrealized_pnl=total_unrealized_pnl,
                total_unrealized_pnl_pct=total_unrealized_pnl_pct,
                timestamp=datetime.now(),
                market_data_quality=market_data_quality,
            )

            logger.info("✅ [LivePortfolio] Portfolio snapshot generated:")
            logger.info(f"   Total Value: ${total_value:.2f}")
            logger.info(f"   Cash Balance: ${cash_balance:.2f}")
            logger.info(f"   Positions Value: ${total_position_value:.2f}")
            logger.info(
                f"   Total PnL: ${total_unrealized_pnl:.2f} ({total_unrealized_pnl_pct:.2f}%)"
            )

            return snapshot

        except Exception as e:
            logger.error(
                f"❌ [LivePortfolio] Failed to generate portfolio snapshot: {e}"
            )
            raise

    def get_position_value(self, symbol: str, amount: float) -> Dict:
        """
        Beräkna aktuellt värde för en specifik position

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            amount: Position amount

        Returns:
            Dict with position valuation
        """
        try:
            logger.info(
                f"💰 [LivePortfolio] Calculating position value for {amount:.6f} {symbol}"
            )

            # Get live price
            ticker = self.live_data.fetch_live_ticker(symbol)
            current_price = ticker["last"]

            # Calculate position metrics
            market_value = amount * current_price

            result = {
                "symbol": symbol,
                "amount": amount,
                "current_price": current_price,
                "market_value": market_value,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"✅ [LivePortfolio] Position value: ${market_value:.2f}")

            return result

        except Exception as e:
            logger.error(f"❌ [LivePortfolio] Failed to calculate position value: {e}")
            raise

    def validate_trading_capacity(
        self, symbol: str, trade_amount: float, trade_type: str
    ) -> Dict:
        """
        Validera om vi kan utföra en trade baserat på live portfolio

        Args:
            symbol: Trading pair
            trade_amount: Amount to trade
            trade_type: 'buy' or 'sell'

        Returns:
            Dict with validation results
        """
        try:
            logger.info("🛡️ [LivePortfolio] Validating trading capacity...")
            # Get current portfolio
            snapshot = self.get_live_portfolio_snapshot([symbol])

            # Get current market price
            ticker = self.live_data.fetch_live_ticker(symbol)
            current_price = ticker["last"]
            trade_value = trade_amount * current_price

            validation_result = {
                "valid": False,
                "reason": "",
                "available_balance": snapshot.available_balance,
                "current_price": current_price,
                "trade_value": trade_value,
            }

            if trade_type.lower() == "buy":
                # Check if we have enough cash
                if snapshot.available_balance >= trade_value:
                    validation_result["valid"] = True
                    validation_result["reason"] = "Sufficient balance for purchase"
                else:
                    validation_result["reason"] = (
                        f"Insufficient balance: need ${trade_value:.2f}, have ${snapshot.available_balance:.2f}"
                    )

            elif trade_type.lower() == "sell":
                # Check if we have enough of the asset
                current_position = 0

                for pos in snapshot.positions:
                    if pos.symbol == symbol:
                        current_position = pos.amount
                        break

                if current_position >= trade_amount:
                    validation_result["valid"] = True
                    validation_result["reason"] = "Sufficient position for sale"
                else:
                    validation_result["reason"] = (
                        f"Insufficient position: need {trade_amount:.6f}, have {current_position:.6f}"
                    )

            logger.info(
                f"✅ [LivePortfolio] Validation result: {validation_result['valid']} - {validation_result['reason']}"
            )

            return validation_result

        except Exception as e:
            logger.error(f"❌ [LivePortfolio] Trading capacity validation failed: {e}")
            raise

    def get_portfolio_performance_metrics(self, timeframe: str = "24h") -> Dict:
        """
        Beräkna portfolio performance metrics med live data

        Args:
            timeframe: Time period for performance calculation

        Returns:
            Dict with performance metrics
        """
        try:
            logger.info(
                f"📊 [LivePortfolio] Calculating performance metrics for {timeframe}"
            )

            # Get current snapshot
            current_snapshot = self.get_live_portfolio_snapshot()

            # For now, return basic metrics
            # In full implementation, this would compare with historical snapshots
            metrics = {
                "current_value": current_snapshot.total_value,
                "unrealized_pnl": current_snapshot.total_unrealized_pnl,
                "unrealized_pnl_pct": current_snapshot.total_unrealized_pnl_pct,
                "cash_allocation_pct": (
                    current_snapshot.available_balance / current_snapshot.total_value
                )
                * 100,
                "position_count": len(current_snapshot.positions),
                "largest_position": (
                    max([pos.market_value for pos in current_snapshot.positions])
                    if current_snapshot.positions
                    else 0
                ),
                "timestamp": current_snapshot.timestamp.isoformat(),
            }

            logger.info(f"✅ [LivePortfolio] Performance metrics calculated")

            return metrics

        except Exception as e:
            logger.error(f"❌ [LivePortfolio] Performance calculation failed: {e}")
            raise
