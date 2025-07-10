"""
Tests for FastAPI portfolio endpoints.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.models import ResponseStatus
from backend.fastapi_app import app

# Create a test client
client = TestClient(app)


@pytest.fixture
def mock_portfolio_manager():
    """Mock PortfolioManagerAsync for testing."""
    from backend.api.dependencies import get_portfolio_manager

    # Create a mock instance with AsyncMock for async methods
    portfolio_manager = MagicMock()

    # Configure mock responses using AsyncMock
    portfolio_manager.calculate_allocations = AsyncMock(
        return_value=[
            {
                "symbol": "tBTCUSD",
                "percentage": 50.0,
                "amount": 50000.0,
                "action": "buy",
                "current_allocation": 40.0,
                "target_allocation": 50.0,
            }
        ]
    )

    portfolio_manager.process_signals = AsyncMock(
        return_value=[
            {
                "symbol": "tBTCUSD",
                "action": "buy",
                "amount": 0.1,
            }
        ]
    )

    portfolio_manager.get_portfolio_status = AsyncMock(
        return_value={
            "total_value": 100000.0,
            "positions": [
                {
                    "symbol": "tBTCUSD",
                    "amount": 0.5,
                    "value": 18000.0,
                }
            ],
        }
    )

    portfolio_manager.rebalance_portfolio = AsyncMock(
        return_value={
            "trades": [
                {
                    "symbol": "tBTCUSD",
                    "action": "buy",
                    "amount": 0.1,
                }
            ],
            "new_allocations": [
                {
                    "symbol": "tBTCUSD",
                    "allocation": 0.6,
                    "weight": 0.6,
                }
            ],
        }
    )

    # Override the dependency
    app.dependency_overrides[get_portfolio_manager] = lambda: portfolio_manager

    yield portfolio_manager

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def mock_risk_manager():
    """Mock RiskManagerAsync for testing."""
    from backend.api.dependencies import get_risk_manager

    # Create a mock instance with AsyncMock for async methods
    risk_manager = MagicMock()

    # Configure mock responses using AsyncMock
    risk_manager.assess_portfolio_risk = AsyncMock(
        return_value={
            "total_risk_score": 0.5,
            "risk_factors": {
                "volatility": 0.3,
                "correlation": 0.2,
            },
        }
    )

    # Override the dependency
    app.dependency_overrides[get_risk_manager] = lambda: risk_manager

    yield risk_manager

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def mock_live_portfolio_service():
    """Mock LivePortfolioServiceAsync for testing."""
    from backend.api.portfolio import get_live_portfolio_service

    # Create a mock instance
    mock_service = MagicMock()

    # Configure mock responses for get_live_portfolio_snapshot
    portfolio_position = MagicMock()
    portfolio_position.symbol = "tBTCUSD"
    portfolio_position.amount = 0.5
    portfolio_position.entry_price = 35000.0
    portfolio_position.current_price = 36000.0
    portfolio_position.unrealized_pnl = 500.0
    portfolio_position.unrealized_pnl_pct = 2.85
    portfolio_position.market_value = 18000.0
    portfolio_position.timestamp = datetime.now()

    portfolio_snapshot = MagicMock()
    portfolio_snapshot.total_value = 100000.0
    portfolio_snapshot.available_balance = 25000.0
    portfolio_snapshot.positions = [portfolio_position]
    portfolio_snapshot.total_unrealized_pnl = 500.0
    portfolio_snapshot.total_unrealized_pnl_pct = 2.85
    portfolio_snapshot.timestamp = datetime.now()
    portfolio_snapshot.market_data_quality = "high"

    # Configure mock responses using AsyncMock
    mock_service.get_live_portfolio_snapshot = AsyncMock(
        return_value=portfolio_snapshot
    )

    performance_metric = MagicMock()
    performance_metric.name = "Return"
    performance_metric.value = 2.1
    performance_metric.unit = "%"
    performance_metric.timestamp = datetime.now()
    mock_service.get_portfolio_performance = AsyncMock(
        return_value=[performance_metric]
    )

    trade_validation = MagicMock()
    trade_validation.is_valid = True
    trade_validation.message = "Trade is valid"
    trade_validation.available_balance = 25000.0
    trade_validation.required_balance = 18000.0
    trade_validation.max_trade_size = 0.69
    trade_validation.timestamp = datetime.now()
    mock_service.validate_trade = AsyncMock(return_value=trade_validation)

    # Override the dependency
    app.dependency_overrides[get_live_portfolio_service] = lambda: mock_service

    yield mock_service

    # Clean up
    app.dependency_overrides.clear()


def test_allocate_portfolio(mock_portfolio_manager, mock_risk_manager):
    """Test allocate_portfolio endpoint."""
    # Uppdaterad testdata för att matcha SignalData-modellen
    response = client.post(
        "/api/portfolio/allocate",
        json={
            "signals": [
                {
                    "symbol": "tBTCUSD",
                    "signal_type": "buy",
                    "strength": 0.8,
                    "confidence": 0.7,
                    "timestamp": datetime.now().isoformat(),
                    "source": "sample_strategy",
                    "indicators": {"ema_short": 35000, "ema_long": 34000},
                    "price": 35000.0,
                }
            ],
            "risk_profile": "moderate",
            "max_allocation_percent": 0.5,
            "timestamp": datetime.now().isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ResponseStatus.SUCCESS
    assert "allocations" in data
    assert len(data["allocations"]) == 1

    # Verify the mock was called with the right parameters
    mock_portfolio_manager.calculate_allocations.assert_called_once()


def test_process_strategy_signals(mock_portfolio_manager):
    """Test process_strategy_signals endpoint."""
    # Uppdaterad testdata för att matcha SignalData-modellen
    response = client.post(
        "/api/portfolio/process-signals",
        json={
            "signals": [
                {
                    "symbol": "tBTCUSD",
                    "signal_type": "buy",
                    "strength": 0.8,
                    "confidence": 0.7,
                    "timestamp": datetime.now().isoformat(),
                    "source": "sample_strategy",
                    "indicators": {"ema_short": 35000, "ema_long": 34000},
                    "price": 35000.0,
                }
            ],
            "timestamp": datetime.now().isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ResponseStatus.SUCCESS
    assert "actions" in data
    assert len(data["actions"]) == 1

    # Verify the mock was called with the right parameters
    mock_portfolio_manager.process_signals.assert_called_once()


def test_get_portfolio_status(mock_portfolio_manager):
    """Test get_portfolio_status endpoint."""
    response = client.get("/api/portfolio/status")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ResponseStatus.SUCCESS
    assert "portfolio_status" in data

    # Uppdaterad assertion för att matcha faktisk implementation
    # Portfolio status returnerar faktiska värden från mock, inte hårdkodade
    portfolio_status = data["portfolio_status"]
    assert "total_value" in portfolio_status
    assert "positions" in portfolio_status

    # Verify the mock was called
    mock_portfolio_manager.get_portfolio_status.assert_called_once()


def test_rebalance_portfolio(mock_portfolio_manager):
    """Test rebalance_portfolio endpoint."""
    # Uppdaterad testdata för att matcha AllocationItem-modellen
    response = client.post(
        "/api/portfolio/rebalance",
        json=[
            {
                "symbol": "tBTCUSD",
                "percentage": 0.6,
                "amount": 0.1,
                "action": "buy",
                "current_allocation": 0.5,
                "target_allocation": 0.6,
            }
        ],
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ResponseStatus.SUCCESS
    assert "rebalance_results" in data

    # Verify the mock was called with the right parameters
    mock_portfolio_manager.rebalance_portfolio.assert_called_once()


def test_get_live_portfolio_snapshot(mock_live_portfolio_service):
    """Test get_live_portfolio_snapshot endpoint."""
    response = client.get("/api/portfolio/live/snapshot")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ResponseStatus.SUCCESS
    assert "snapshot" in data

    # Uppdaterad assertion för att matcha faktisk implementation
    # Snapshot returnerar faktiska värden från mock, inte hårdkodade
    snapshot = data["snapshot"]
    assert "total_value" in snapshot
    assert "available_balance" in snapshot
    assert "positions" in snapshot

    # Verify the mock was called
    mock_live_portfolio_service.get_live_portfolio_snapshot.assert_called_once()


def test_get_live_portfolio_snapshot_with_symbols(mock_live_portfolio_service):
    """Test get_live_portfolio_snapshot endpoint with symbols filter."""
    response = client.get("/api/portfolio/live/snapshot?symbols=tBTCUSD,tETHUSD")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ResponseStatus.SUCCESS
    assert "snapshot" in data

    # Uppdaterad assertion för att matcha faktisk implementation
    snapshot = data["snapshot"]
    assert "total_value" in snapshot
    assert "available_balance" in snapshot
    assert "positions" in snapshot

    # Verify the mock was called
    mock_live_portfolio_service.get_live_portfolio_snapshot.assert_called_once()


def test_get_live_portfolio_performance(mock_live_portfolio_service):
    """Test get_live_portfolio_performance endpoint."""
    response = client.get("/api/portfolio/live/performance")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ResponseStatus.SUCCESS
    # Uppdaterad assertion för att matcha faktisk response format
    assert "performance_metrics" in data  # Istället för "metrics"

    # Verify the mock was called
    mock_live_portfolio_service.get_portfolio_performance.assert_called_once()


def test_get_live_portfolio_performance_with_timeframe(mock_live_portfolio_service):
    """Test get_live_portfolio_performance endpoint with timeframe."""
    response = client.get("/api/portfolio/live/performance?timeframe=7d")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ResponseStatus.SUCCESS
    # Uppdaterad assertion för att matcha faktisk response format
    assert "performance_metrics" in data  # Istället för "metrics"

    # Verify the mock was called
    mock_live_portfolio_service.get_portfolio_performance.assert_called_once()


def test_validate_live_trade(mock_live_portfolio_service):
    """Test validate_live_trade endpoint."""
    response = client.post(
        "/api/portfolio/live/validate-trade?symbol=tBTCUSD&amount=0.5&trade_type=buy"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ResponseStatus.SUCCESS
    # Uppdaterad assertion för att matcha faktisk response format
    assert "validation" in data  # Istället för "validation_result"

    # Verify the mock was called
    mock_live_portfolio_service.validate_trade.assert_called_once()


def test_validate_live_trade_invalid_type(mock_live_portfolio_service):
    """Test validate_live_trade endpoint with invalid trade type."""
    response = client.post(
        "/api/portfolio/live/validate-trade?symbol=tBTCUSD&amount=0.5&trade_type=invalid"
    )

    assert response.status_code == 400
    data = response.json()

    # Uppdaterad assertion för att matcha faktisk error message
    assert "Invalid trade type" in data["detail"]  # Istället för "Invalid trade_type"
