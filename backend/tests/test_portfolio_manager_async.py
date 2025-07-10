"""Tester för asynkron portföljhantering med PortfolioManagerAsync."""

import asyncio
from datetime import datetime
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch

import pytest

from backend.services.portfolio_manager_async import (
    CombinedSignal,
    PortfolioManagerAsync,
    StrategyWeight,
)
from backend.services.risk_manager_async import (
    ProbabilityData,
    RiskManagerAsync,
    RiskParameters,
)
from backend.strategies.sample_strategy import TradeSignal


@pytest.fixture
def mock_risk_manager():
    """Skapa en mockad RiskManagerAsync."""
    risk_manager = AsyncMock(spec=RiskManagerAsync)

    # Konfigurera mock-parametrar
    risk_manager.params = RiskParameters(
        max_position_size=0.1,
        max_leverage=2.0,
        stop_loss_pct=0.05,
        take_profit_pct=0.1,
        max_daily_loss=0.02,
        max_open_positions=5,
        min_signal_confidence=0.6,
        probability_weight=0.5,
    )

    # Konfigurera mock-metoder
    risk_manager.calculate_intelligent_position_size.return_value = (
        1000.0,  # Position size
        {
            "probability_factor": 0.8,
            "risk_adjustment": 0.9,
            "risk_score": 0.3,
            "position_size_factor": 1.2,
        },
    )

    risk_manager.assess_portfolio_risk.return_value = {
        "overall_risk_score": 0.4,
        "risk_level": "moderate",
        "position_count": 2,
        "total_exposure": 20000.0,
        "recommendations": ["Diversify further"],
    }

    return risk_manager


@pytest.fixture
def strategy_weights():
    """Skapa en lista med strategivikter."""
    return [
        StrategyWeight(
            strategy_name="ema_crossover",
            weight=0.5,
            min_confidence=0.6,
            enabled=True,
        ),
        StrategyWeight(
            strategy_name="rsi_strategy",
            weight=0.3,
            min_confidence=0.5,
            enabled=True,
        ),
        StrategyWeight(
            strategy_name="fvg_strategy",
            weight=0.2,
            min_confidence=0.7,
            enabled=True,
        ),
    ]


@pytest.fixture
def portfolio_manager(mock_risk_manager, strategy_weights):
    """Skapa en PortfolioManagerAsync-instans med mockade beroenden."""
    return PortfolioManagerAsync(mock_risk_manager, strategy_weights)


@pytest.fixture
def mock_strategy_signals():
    """Skapa mockat signaldata från olika strategier."""
    return {
        "ema_crossover": TradeSignal(
            action="buy",
            confidence=0.8,
            metadata={
                "probability_buy": 0.7,
                "probability_sell": 0.1,
                "probability_hold": 0.2,
                "ema_fast": 50,
                "ema_slow": 200,
            },
        ),
        "rsi_strategy": TradeSignal(
            action="hold",
            confidence=0.6,
            metadata={
                "probability_buy": 0.3,
                "probability_sell": 0.2,
                "probability_hold": 0.5,
                "rsi_value": 52,
            },
        ),
    }


class TestPortfolioManagerAsyncBasic:
    """Test grundläggande funktionalitet i PortfolioManagerAsync."""

    def test_initialization(self, portfolio_manager, strategy_weights):
        """Test att initiera PortfolioManagerAsync."""
        assert portfolio_manager.risk_manager is not None
        assert len(portfolio_manager.strategy_weights) == 3
        assert "ema_crossover" in portfolio_manager.strategy_weights
        assert portfolio_manager.strategy_weights["ema_crossover"].weight == 0.5

    def test_validate_weights_warning(self, mock_risk_manager):
        """Test att varning genereras vid ogiltiga vikter."""
        # Skapa vikter som summerar till mer än 1.0
        weights = [
            StrategyWeight(strategy_name="strat1", weight=0.6, enabled=True),
            StrategyWeight(strategy_name="strat2", weight=0.6, enabled=True),
        ]

        with patch(
            "backend.services.portfolio_manager_async.logging.warning"
        ) as mock_warn:
            pm = PortfolioManagerAsync(mock_risk_manager, weights)
            mock_warn.assert_called_once()
            assert "weights sum to" in mock_warn.call_args[0][0].lower()


class TestPortfolioManagerAsyncSignals:
    """Test signalbehandling i PortfolioManagerAsync."""

    @pytest.mark.asyncio
    async def test_combine_strategy_signals_success(
        self, portfolio_manager, mock_strategy_signals
    ):
        """Test att kombinera signaler från flera strategier."""
        combined_signal = await portfolio_manager.combine_strategy_signals(
            mock_strategy_signals, "BTC/USD", 50000.0
        )

        assert isinstance(combined_signal, CombinedSignal)
        assert combined_signal.action in ["buy", "sell", "hold"]
        assert 0.0 <= combined_signal.combined_confidence <= 1.0
        assert isinstance(combined_signal.combined_probabilities, ProbabilityData)
        assert len(combined_signal.individual_signals) == 2
        assert "ema_crossover" in combined_signal.individual_signals
        assert "rsi_strategy" in combined_signal.individual_signals
        assert "symbol" in combined_signal.metadata
        assert combined_signal.metadata["symbol"] == "BTC/USD"

    @pytest.mark.asyncio
    async def test_combine_strategy_signals_empty(self, portfolio_manager):
        """Test att kombinera signaler när inga signaler finns."""
        combined_signal = await portfolio_manager.combine_strategy_signals(
            {}, "BTC/USD", 50000.0
        )

        assert isinstance(combined_signal, CombinedSignal)
        assert combined_signal.action == "hold"
        assert combined_signal.combined_confidence == 0.5
        assert len(combined_signal.individual_signals) == 0
        assert "reason" in combined_signal.metadata
        assert "No strategy signals" in combined_signal.metadata["reason"]

    @pytest.mark.asyncio
    async def test_combine_strategy_signals_filter_low_confidence(
        self, portfolio_manager
    ):
        """Test att signaler med låg konfidens filtreras bort."""
        signals = {
            "ema_crossover": TradeSignal(
                action="buy",
                confidence=0.3,  # Under min_confidence för denna strategi (0.6)
                metadata={
                    "probability_buy": 0.7,
                    "probability_sell": 0.1,
                    "probability_hold": 0.2,
                },
            ),
        }

        combined_signal = await portfolio_manager.combine_strategy_signals(
            signals, "BTC/USD", 50000.0
        )

        # När alla signaler filtreras, bör en hold-signal genereras
        assert combined_signal.action == "hold"
        assert len(combined_signal.individual_signals) == 0
        assert "reason" in combined_signal.metadata
        assert "No valid signals" in combined_signal.metadata["reason"]

    @pytest.mark.asyncio
    async def test_combine_strategy_signals_unknown_strategy(self, portfolio_manager):
        """Test att okända strategier hanteras korrekt."""
        signals = {
            "unknown_strategy": TradeSignal(
                action="buy",
                confidence=0.8,
                metadata={
                    "probability_buy": 0.7,
                    "probability_sell": 0.1,
                    "probability_hold": 0.2,
                },
            ),
        }

        with patch(
            "backend.services.portfolio_manager_async.logging.warning"
        ) as mock_warn:
            combined_signal = await portfolio_manager.combine_strategy_signals(
                signals, "BTC/USD", 50000.0
            )

            mock_warn.assert_called_once()
            assert "unknown strategy" in mock_warn.call_args[0][0].lower()

            # När alla signaler filtreras, bör en hold-signal genereras
            assert combined_signal.action == "hold"
            assert len(combined_signal.individual_signals) == 0


class TestPortfolioManagerAsyncPositionSizing:
    """Test positionsstorleksberäkning i PortfolioManagerAsync."""

    @pytest.mark.asyncio
    async def test_calculate_portfolio_position_size(
        self, portfolio_manager, mock_risk_manager
    ):
        """Test att beräkna positionsstorlek baserat på kombinerad signal."""
        # Skapa en kombinerad signal
        combined_signal = CombinedSignal(
            action="buy",
            combined_confidence=0.8,
            combined_probabilities=ProbabilityData(
                probability_buy=0.7,
                probability_sell=0.1,
                probability_hold=0.2,
                confidence=0.8,
            ),
            individual_signals={
                "ema_crossover": TradeSignal(action="buy", confidence=0.8, metadata={})
            },
            metadata={"symbol": "BTC/USD"},
        )

        portfolio_value = 100000.0
        current_positions = {"ETH/USD": {"amount": 2.0, "entry_price": 3000.0}}
        symbol = "BTC/USD"

        # Beräkna positionsstorlek
        size, metadata = await portfolio_manager.calculate_portfolio_position_size(
            combined_signal, portfolio_value, current_positions, symbol
        )

        # Verifiera resultat
        assert size == 1000.0  # Från mock
        assert "symbol" in metadata
        assert metadata["symbol"] == "BTC/USD"
        assert "combined_signal_action" in metadata
        assert metadata["combined_signal_action"] == "buy"
        assert "portfolio_diversification_factor" in metadata

        # Verifiera att risk_manager.calculate_intelligent_position_size anropades
        mock_risk_manager.calculate_intelligent_position_size.assert_called_once()
        args = mock_risk_manager.calculate_intelligent_position_size.call_args[1]
        assert args["signal_confidence"] == 0.8
        assert args["portfolio_value"] == 100000.0
        assert args["probability_data"] is combined_signal.combined_probabilities

    @pytest.mark.asyncio
    async def test_calculate_diversification_factor(self, portfolio_manager):
        """Test beräkning av diversifieringsfaktor."""
        # Tomt portfölj = ingen diversifiering = faktor 1.0
        factor = await portfolio_manager._calculate_diversification_factor({})
        assert factor == 1.0

        # Fler positioner bör ge lägre faktor (mindre position per tillgång)
        positions = {f"sym{i}": {"amount": 1.0} for i in range(3)}
        factor = await portfolio_manager._calculate_diversification_factor(positions)
        assert factor < 1.0

        # Max antal positioner bör ge lägsta faktor
        positions = {f"sym{i}": {"amount": 1.0} for i in range(5)}
        factor = await portfolio_manager._calculate_diversification_factor(positions)
        assert factor == 0.5  # Min-värdet enligt implementationen


class TestPortfolioManagerAsyncTradeExecution:
    """Test handelsutförande i PortfolioManagerAsync."""

    @pytest.mark.asyncio
    async def test_should_execute_trade_valid(
        self, portfolio_manager, mock_risk_manager
    ):
        """Test att handel bör genomföras när villkoren är uppfyllda."""
        # Skapa en stark köpsignal
        combined_signal = CombinedSignal(
            action="buy",
            combined_confidence=0.9,
            combined_probabilities=ProbabilityData(
                probability_buy=0.8,
                probability_sell=0.1,
                probability_hold=0.1,
                confidence=0.9,
            ),
            individual_signals={
                "ema_crossover": TradeSignal(action="buy", confidence=0.9, metadata={})
            },
            metadata={"symbol": "BTC/USD"},
        )

        # Konfigurera mock för validering
        mock_risk_manager.validate_order_with_probabilities.return_value = {
            "valid": True,
            "errors": [],
            "risk_assessment": {"risk_score": 0.3},
        }

        # Testa om handel bör genomföras
        should_execute, metadata = await portfolio_manager.should_execute_trade(
            combined_signal, 100000.0, {}, "BTC/USD", 50000.0
        )

        assert should_execute is True
        assert "confidence" in metadata
        assert metadata["confidence"] == 0.9
        assert "risk_validation" in metadata
        assert metadata["risk_validation"]["valid"] is True

        # Verifiera att validate_order_with_probabilities anropades
        mock_risk_manager.validate_order_with_probabilities.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_execute_trade_invalid(
        self, portfolio_manager, mock_risk_manager
    ):
        """Test att handel inte bör genomföras när validering misslyckas."""
        # Skapa en signal
        combined_signal = CombinedSignal(
            action="buy",
            combined_confidence=0.7,
            combined_probabilities=ProbabilityData(
                probability_buy=0.6,
                probability_sell=0.2,
                probability_hold=0.2,
                confidence=0.7,
            ),
            individual_signals={},
            metadata={},
        )

        # Konfigurera mock för misslyckad validering
        mock_risk_manager.validate_order_with_probabilities.return_value = {
            "valid": False,
            "errors": ["Position size too large"],
            "risk_assessment": {"risk_score": 0.6},
        }

        # Testa om handel bör genomföras
        should_execute, metadata = await portfolio_manager.should_execute_trade(
            combined_signal, 100000.0, {}, "BTC/USD", 50000.0
        )

        assert should_execute is False
        assert "risk_validation" in metadata
        assert metadata["risk_validation"]["valid"] is False
        assert len(metadata["risk_validation"]["errors"]) > 0


class TestPortfolioManagerAsyncFactory:
    """Test för factory-funktioner relaterade till PortfolioManagerAsync."""

    @pytest.mark.asyncio
    async def test_get_portfolio_manager_async(self):
        """Test factory function get_portfolio_manager_async."""
        with patch(
            "backend.services.portfolio_manager_async.PortfolioManagerAsync"
        ) as mock_pm:

            # Skapa mock-instanser
            mock_risk_manager = AsyncMock(spec=RiskManagerAsync)
            mock_strategy_weights = [
                StrategyWeight(strategy_name="test_strategy", weight=1.0)
            ]

            mock_instance = AsyncMock(spec=PortfolioManagerAsync)
            mock_pm.return_value = mock_instance

            # Anropa factory function
            from backend.services.portfolio_manager_async import (
                get_portfolio_manager_async,
            )

            portfolio_manager = await get_portfolio_manager_async(
                risk_manager=mock_risk_manager, strategy_weights=mock_strategy_weights
            )

            # Verifiera att dependencies laddades korrekt
            mock_pm.assert_called_once_with(mock_risk_manager, mock_strategy_weights)

            # Verifiera att instansen returnerades
            assert portfolio_manager == mock_instance
