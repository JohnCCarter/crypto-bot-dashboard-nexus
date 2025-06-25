#!/usr/bin/env python3
"""
🔗 Backend WebSocket Integration Test
Testar integration mellan Bitfinex WebSocket och trading bot backend

Detta verktyg testar:
1. WebSocket market service funktionalitet
2. LiveDataService med real-time data
3. Trading strategies med live WebSocket data
4. Risk management med real-time priser
5. Integration med trading bot logic
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
import json

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Import backend services
try:
    from backend.services.live_data_service import LiveDataService
    from backend.services.websocket_market_service import BitfinexWebSocketClient
    from backend.strategies.ema_crossover_strategy import run_strategy as run_ema
    from backend.strategies.rsi_strategy import run_strategy as run_rsi
    from backend.services.risk_manager import RiskManager, RiskParameters
    from backend.services.config_service import ConfigService
except ImportError as e:
    print(f"❌ Failed to import backend modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BackendWebSocketIntegrationTest:
    def __init__(self):
        self.live_data_service = None
        self.websocket_client = None
        self.risk_manager = None
        self.test_symbols = ["tBTCUSD", "tETHUSD"]

    async def initialize_services(self):
        """Initialisera backend services"""
        try:
            logger.info("🔧 Initializing backend services...")

            # Load configuration
            config_service = ConfigService()
            config = config_service.load_config()

            # Initialize LiveDataService
            api_key = os.getenv("BITFINEX_API_KEY")
            api_secret = os.getenv("BITFINEX_API_SECRET")

            self.live_data_service = LiveDataService(
                exchange_id="bitfinex", api_key=api_key, api_secret=api_secret
            )

            # Initialize WebSocket client
            self.websocket_client = BitfinexWebSocketClient()

            # Initialize risk manager
            risk_conf = config.risk_config
            risk_params = RiskParameters(
                max_position_size=risk_conf.get("risk_per_trade", 0.02),
                max_leverage=1,
                stop_loss_pct=risk_conf.get("stop_loss_percent", 2.0) / 100,
                take_profit_pct=risk_conf.get("take_profit_percent", 4.0) / 100,
                max_daily_loss=risk_conf.get("max_daily_loss", 5.0) / 100,
                max_open_positions=risk_conf.get("max_open_positions", 5),
            )
            self.risk_manager = RiskManager(risk_params)

            logger.info("✅ Backend services initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            return False

    async def test_live_data_service(self):
        """Testa LiveDataService"""
        print("\n🔬 TESTING LIVE DATA SERVICE")
        print("-" * 50)

        success_count = 0
        total_tests = 0

        for symbol in self.test_symbols:
            try:
                total_tests += 1
                logger.info(f"Testing LiveDataService for {symbol}...")

                # Test OHLCV data fetch
                ohlcv_data = self.live_data_service.fetch_live_ohlcv(
                    symbol=symbol, timeframe="5m", limit=50
                )

                if len(ohlcv_data) >= 40:  # Should get at least 40 candles
                    print(
                        f"✅ {symbol}: OHLCV data fetched ({len(ohlcv_data)} candles)"
                    )
                    print(f"   Latest price: ${ohlcv_data['close'].iloc[-1]:.2f}")
                    success_count += 1
                else:
                    print(
                        f"❌ {symbol}: Insufficient OHLCV data ({len(ohlcv_data)} candles)"
                    )

                # Test ticker data
                ticker = self.live_data_service.fetch_live_ticker(symbol)
                if ticker and "last" in ticker:
                    print(f"✅ {symbol}: Ticker data fetched (${ticker['last']:.2f})")
                else:
                    print(f"❌ {symbol}: Invalid ticker data")

                # Test market context
                market_context = self.live_data_service.get_live_market_context(
                    symbol=symbol, timeframe="5m", limit=50
                )

                if market_context and "current_price" in market_context:
                    print(f"✅ {symbol}: Market context complete")
                    print(f"   Current price: ${market_context['current_price']:.2f}")
                    print(f"   Spread: ${market_context['spread']:.2f}")
                    print(f"   Volume 24h: {market_context['volume_24h']:.2f}")
                else:
                    print(f"❌ {symbol}: Incomplete market context")

            except Exception as e:
                print(f"❌ {symbol}: LiveDataService test failed - {e}")

            # Small delay between symbols
            await asyncio.sleep(1)

        print(
            f"\n📊 LiveDataService Results: {success_count}/{total_tests} symbols passed"
        )
        return success_count == total_tests

    async def test_websocket_service(self):
        """Testa BitfinexWebSocketClient"""
        print("\n🌐 TESTING WEBSOCKET CLIENT")
        print("-" * 50)

        try:
            # Test WebSocket connection
            logger.info("Testing WebSocket client...")

            # Connect WebSocket client
            await self.websocket_client.connect()

            # Set up data collection
            received_ticker_data = {}
            received_orderbook_data = {}

            async def ticker_callback(data):
                received_ticker_data["tBTCUSD"] = data

            async def orderbook_callback(data):
                received_orderbook_data["tBTCUSD"] = data

            # Subscribe to BTC/USD
            await self.websocket_client.subscribe_ticker("tBTCUSD", ticker_callback)
            await self.websocket_client.subscribe_orderbook(
                "tBTCUSD", orderbook_callback
            )

            # Wait for data
            logger.info("Waiting for WebSocket data...")
            await asyncio.sleep(10)

            # Check received data
            if received_ticker_data:
                print("✅ WebSocket ticker data received")
                ticker = received_ticker_data.get("tBTCUSD")
                if ticker:
                    print(f"   BTC/USD: ${ticker.price:.2f}")
            else:
                print("❌ No WebSocket ticker data received")

            if received_orderbook_data:
                print("✅ WebSocket orderbook data received")
                orderbook = received_orderbook_data.get("tBTCUSD")
                if orderbook and "bids" in orderbook:
                    print(f"   Bid levels: {len(orderbook.get('bids', []))}")
                    print(f"   Ask levels: {len(orderbook.get('asks', []))}")
            else:
                print("❌ No WebSocket orderbook data received")

            # Disconnect WebSocket client
            await self.websocket_client.disconnect()

            return bool(received_ticker_data and received_orderbook_data)

        except Exception as e:
            logger.error(f"❌ WebSocket client test failed: {e}")
            return False

    async def test_strategy_integration(self):
        """Testa trading strategies med live data"""
        print("\n🎯 TESTING STRATEGY INTEGRATION WITH LIVE DATA")
        print("-" * 50)

        try:
            # Get live market data for BTC/USD
            symbol = "BTC/USD"
            market_context = self.live_data_service.get_live_market_context(
                symbol=symbol, timeframe="5m", limit=100
            )

            live_data_df = market_context["ohlcv_data"]
            current_price = market_context["current_price"]

            print(f"📊 Testing strategies with {len(live_data_df)} candles")
            print(f"📊 Current price: ${current_price:.2f}")

            # Test EMA strategy
            ema_params = {
                "symbol": symbol,
                "timeframe": "5m",
                "fast_period": 12,
                "slow_period": 26,
                "confidence_threshold": 0.6,
            }

            ema_signal = run_ema(live_data_df, ema_params)
            print(
                f"✅ EMA Strategy: {ema_signal.action} (confidence: {ema_signal.confidence:.2f})"
            )

            # Test RSI strategy
            rsi_params = {
                "symbol": symbol,
                "timeframe": "5m",
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70,
                "confidence_threshold": 0.6,
            }

            rsi_signal = run_rsi(live_data_df, rsi_params)
            print(
                f"✅ RSI Strategy: {rsi_signal.action} (confidence: {rsi_signal.confidence:.2f})"
            )

            # Test risk management
            portfolio_value = 10000
            current_positions = {}

            ema_position_size = self.risk_manager.calculate_position_size(
                ema_signal.confidence, portfolio_value, current_positions
            )

            rsi_position_size = self.risk_manager.calculate_position_size(
                rsi_signal.confidence, portfolio_value, current_positions
            )

            print(f"💰 EMA position size: {ema_position_size:.6f} BTC")
            print(f"💰 RSI position size: {rsi_position_size:.6f} BTC")

            # Check if strategies are actionable
            actionable_signals = 0
            if ema_signal.action in ["buy", "sell"] and ema_signal.confidence > 0.6:
                actionable_signals += 1
                print(f"🚀 EMA signal is actionable: {ema_signal.action}")

            if rsi_signal.action in ["buy", "sell"] and rsi_signal.confidence > 0.6:
                actionable_signals += 1
                print(f"🚀 RSI signal is actionable: {rsi_signal.action}")

            print(f"📈 Actionable signals: {actionable_signals}/2")

            return True

        except Exception as e:
            logger.error(f"❌ Strategy integration test failed: {e}")
            return False

    async def test_data_quality_validation(self):
        """Testa data kvalitetsvalidering"""
        print("\n✅ TESTING DATA QUALITY VALIDATION")
        print("-" * 50)

        try:
            # Get market context for validation
            market_context = self.live_data_service.get_live_market_context(
                symbol="BTC/USD", timeframe="5m", limit=100
            )

            # Run validation
            is_valid, validation_message = (
                self.live_data_service.validate_market_conditions(market_context)
            )

            print(f"📋 Market validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")
            print(f"📋 Validation message: {validation_message}")

            # Check data quality metrics
            quality = market_context["data_quality"]
            print(f"📊 OHLCV rows: {quality['ohlcv_rows']}")
            print(f"📊 Orderbook levels: {quality['orderbook_levels']}")
            print(f"📊 Ticker complete: {quality['ticker_complete']}")
            print(f"📊 Data freshness: {quality['data_freshness_seconds']}s")

            # Check spread and volatility
            spread_pct = (
                market_context["spread"] / market_context["current_price"]
            ) * 100
            print(f"📊 Spread: {spread_pct:.3f}%")
            print(f"📊 Volatility: {market_context['volatility_pct']:.2f}%")

            return is_valid

        except Exception as e:
            logger.error(f"❌ Data quality validation test failed: {e}")
            return False

    async def run_integration_test(self):
        """Kör komplett integration test"""
        print("🔗 BACKEND WEBSOCKET INTEGRATION TEST")
        print("=" * 60)

        test_results = []

        # Initialize services
        if not await self.initialize_services():
            print("❌ Failed to initialize services")
            return False

        # Run tests
        test_results.append(("LiveDataService", await self.test_live_data_service()))
        test_results.append(("WebSocketClient", await self.test_websocket_service()))
        test_results.append(
            ("Strategy Integration", await self.test_strategy_integration())
        )
        test_results.append(
            ("Data Quality Validation", await self.test_data_quality_validation())
        )

        # Print results
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST RESULTS")
        print("=" * 60)

        passed_tests = 0
        total_tests = len(test_results)

        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:.<30} {status}")
            if result:
                passed_tests += 1

        print("-" * 60)
        print(f"Overall result: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Backend WebSocket integration is working correctly")
            return True
        else:
            print("⚠️ SOME INTEGRATION TESTS FAILED")
            print("❌ Backend WebSocket integration needs attention")
            return False


async def main():
    """Main test function"""
    # Check if we can import required modules
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        print("⚠️ python-dotenv not found, environment variables may not load")

    # Create test instance
    test = BackendWebSocketIntegrationTest()

    try:
        # Run integration test
        success = await test.run_integration_test()

        if success:
            print("\n🚀 Ready for live trading with WebSocket data!")
        else:
            print("\n🔧 Backend integration needs fixes before live trading")

    except KeyboardInterrupt:
        print("\n⏹️ Test stopped by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Test exception:")


if __name__ == "__main__":
    asyncio.run(main())
