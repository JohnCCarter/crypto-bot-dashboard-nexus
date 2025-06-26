import logging
import os
import traceback

from dotenv import load_dotenv

from backend.services.config_service import ConfigService
from backend.services.live_data_service import LiveDataService
from backend.services.notifications import Notifier
from backend.services.risk_manager import RiskManager, RiskParameters
from backend.services.trading_window import TradingWindow
from backend.strategies.ema_crossover_strategy import run_strategy as run_ema
from backend.strategies.fvg_strategy import run_strategy as run_fvg
from backend.strategies.rsi_strategy import run_strategy as run_rsi

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

email = os.getenv("EMAIL_ADDRESS")
password = os.getenv("SMTP_PASSWORD")


def main():
    """
    Main trading bot function - now with LIVE DATA integration!
    """
    logger.info("🚀 [TradingBot] Starting LIVE trading bot with real market data")

    config_service = ConfigService()
    config = config_service.load_config()
    # Strategiparametrar - using TradingConfig dataclass

    ema_params = config.strategy_config.copy()
    rsi_params = config.strategy_config.copy()
    fvg_params = config.strategy_config.copy()
    # Force paper trading symbol for automation testing
    symbol = "TESTBTC/TESTUSD"  # Paper trading symbol
    timeframe = "5m"  # Short timeframe for testing

    for params in (ema_params, rsi_params, fvg_params):
        params["symbol"] = symbol
        params["timeframe"] = timeframe

    logger.info(f"📊 [TradingBot] Trading symbol: {symbol}, timeframe: {timeframe}")

    # Initialize LIVE DATA SERVICE
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")

    logger.info("🔴 [TradingBot] Initializing live data service...")
    live_data = LiveDataService(
        exchange_id="bitfinex", api_key=api_key, api_secret=api_secret
    )

    # Riskparametrar
    risk_conf = config.risk_config

    risk_params = RiskParameters(
        max_position_size=risk_conf.get("risk_per_trade", 0.02),
        max_leverage=1,  # Lägg till i config vid behov
        stop_loss_pct=risk_conf.get("stop_loss_percent", 2.0) / 100,
        take_profit_pct=risk_conf.get("take_profit_percent", 4.0) / 100,
        max_daily_loss=risk_conf.get("max_daily_loss", 5.0) / 100,
        max_open_positions=risk_conf.get("max_open_positions", 5),
    )
    risk_manager = RiskManager(risk_params)

    # Trading window
    trading_window = TradingWindow(config.trading_window)

    # Notifications
    notif_conf = config.notifications

    notifier = Notifier(
        smtp_server=notif_conf.get("smtp_server", "smtp.example.com"),
        smtp_port=notif_conf.get("smtp_port", 465),
        sender=notif_conf.get("sender", email),
        receiver=notif_conf.get("receiver", email),
    )

    logger.info("✅ [TradingBot] All services initialized successfully")

    # Main trading logic with LIVE DATA
    if trading_window.is_within_window() and trading_window.can_trade():
        logger.info(
            "🕐 [TradingBot] Trading window is OPEN - proceeding with live analysis"
        )

        try:
            # 🚀 FETCH LIVE MARKET DATA (replaces mock data!)
            logger.info(f"📡 [TradingBot] Fetching LIVE market data for {symbol}...")

            market_context = live_data.get_live_market_context(
                symbol=symbol, timeframe=timeframe, limit=100
            )

            # Validate market conditions before trading
            is_valid, validation_message = live_data.validate_market_conditions(
                market_context
            )

            if not is_valid:
                logger.warning(
                    f"⚠️ [TradingBot] Market conditions not suitable: {validation_message}"
                )
                notifier.send(
                    f"Trading paused - Market conditions: {validation_message}"
                )
                return

            logger.info(
                f"✅ [TradingBot] Market validation passed: {validation_message}"
            )

            # Extract OHLCV data for strategies
            live_data_df = market_context["ohlcv_data"]
            current_price = market_context["current_price"]
            spread = market_context["spread"]
            volume_24h = market_context["volume_24h"]

            logger.info("📊 [TradingBot] LIVE market snapshot:")
            logger.info(f"   Current price: ${current_price:.2f}")
            logger.info(f"   24h volume: {volume_24h:.4f}")
            logger.info(f"   Spread: ${spread:.2f}")
            logger.info(f"   Data points: {len(live_data_df)} candles")
            logger.info(f"   Latest candle: {live_data_df.index[-1]}")

            # 📈 RUN STRATEGIES WITH LIVE DATA
            logger.info("🎯 [TradingBot] Running trading strategies with live data...")

            ema_signal = run_ema(live_data_df, ema_params)
            rsi_signal = run_rsi(live_data_df, rsi_params)
            fvg_signal = run_fvg(live_data_df, fvg_params)

            logger.info("📊 [TradingBot] Strategy signals generated:")
            logger.info(
                f"   EMA strategy: {ema_signal.action} (confidence: {ema_signal.confidence:.2f})"
            )
            logger.info(
                f"   RSI strategy: {rsi_signal.action} (confidence: {rsi_signal.confidence:.2f})"
            )
            logger.info(
                f"   FVG strategy: {fvg_signal.action} (confidence: {fvg_signal.confidence:.2f})"
            )

            # 💰 RISK MANAGEMENT WITH LIVE CONTEXT
            portfolio_value = 10000  # Should come from live portfolio API
            current_positions = {}  # Should come from live positions API

            # Calculate position sizes for each strategy
            ema_position_size = risk_manager.calculate_position_size(
                ema_signal.confidence, portfolio_value, current_positions
            )

            rsi_position_size = risk_manager.calculate_position_size(
                rsi_signal.confidence, portfolio_value, current_positions
            )

            fvg_position_size = risk_manager.calculate_position_size(
                fvg_signal.confidence, portfolio_value, current_positions
            )

            logger.info("💰 [TradingBot] Position sizes calculated:")
            logger.info(
                f"   EMA position: {ema_position_size:.6f} {symbol.split('/')[0]}"
            )
            logger.info(
                f"   RSI position: {rsi_position_size:.6f} {symbol.split('/')[0]}"
            )
            logger.info(
                f"   FVG position: {fvg_position_size:.6f} {symbol.split('/')[0]}"
            )

            # 🚨 TRADING EXECUTION LOGIC
            # This is where you would place actual orders using live data
            # For now, we'll log the decisions

            executing_trades = []

            # Check each strategy for actionable signals
            for strategy_name, signal, position_size in [
                ("EMA", ema_signal, ema_position_size),
                ("RSI", rsi_signal, rsi_position_size),
                ("FVG", fvg_signal, fvg_position_size),
            ]:
                if signal.action in ["buy", "sell"] and signal.confidence > 0.6:
                    executing_trades.append(
                        {
                            "strategy": strategy_name,
                            "action": signal.action,
                            "confidence": signal.confidence,
                            "position_size": position_size,
                            "entry_price": current_price,
                            "market_context": {
                                "spread": spread,
                                "volume_24h": volume_24h,
                                "volatility": market_context["volatility_pct"],
                            },
                        }
                    )

            if executing_trades:
                logger.info(
                    f"🚀 [TradingBot] EXECUTING {len(executing_trades)} trades based on live data:"
                )

                for trade in executing_trades:
                    logger.info(
                        f"   📈 {trade['strategy']}: {trade['action'].upper()} "
                        f"{trade['position_size']:.6f} @ ${trade['entry_price']:.2f} "
                        f"(confidence: {trade['confidence']:.2f})"
                    )

                # Register trade execution
                trading_window.register_trade()

                # Send notification with live market context
                notification_message = f"""
🚀 LIVE Trading Bot Execution:

📊 Market Data:
- Symbol: {symbol}
- Current Price: ${current_price:.2f}
- Volume 24h: {volume_24h:.4f}
- Spread: ${spread:.2f}

📈 Executed Trades:
{chr(10).join([f"- {t['strategy']}: {t['action'].upper()} {t['position_size']:.6f} @ ${t['entry_price']:.2f}" for t in executing_trades])}

🎯 Data Quality:
- OHLCV candles: {market_context['data_quality']['ohlcv_rows']}
- Orderbook levels: {market_context['data_quality']['orderbook_levels']}
- Real-time latency: {market_context['data_quality']['data_freshness_seconds']}s

⏰ Timestamp: {market_context['timestamp']}
                """.strip()

                notifier.send(notification_message)

            else:
                logger.info("📊 [TradingBot] No actionable signals - holding position")
                notifier.send(
                    f"Trading bot analyzed live data - no trades executed. "
                    f"Current price: ${current_price:.2f}"
                )

        except Exception as e:
            logger.error(f"❌ [TradingBot] Error during live trading execution: {e}")
            logger.error("❌ [TradingBot] Stack trace:", exc_info=True)
            notifier.send(f"Trading bot error: {e}")
            raise

    else:
        logger.info("🕐 [TradingBot] Outside trading window or max trades reached")
        notifier.send(
            "Trading bot checked - outside trading window or max trades reached."
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.error("❌ [TradingBot] Fatal error in main execution:")
        traceback.print_exc()
