"""
Tests for FastAPI portfolio endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from backend.fastapi_app import app
from backend.api.models import ResponseStatus


# Create a test client
client = TestClient(app)


@pytest.fixture
def mock_portfolio_manager():
    """Mock PortfolioManagerAsync for testing."""
    with patch("backend.api.portfolio.get_portfolio_manager") as mock:
        # Create a mock instance
        portfolio_manager = MagicMock()
        
        # Configure mock responses
        portfolio_manager.calculate_allocations.return_value = [
            {
                "symbol": "tBTCUSD",
                "allocation": 0.5,
                "weight": 0.5,
            }
        ]
        
        portfolio_manager.process_signals.return_value = [
            {
                "symbol": "tBTCUSD",
                "action": "buy",
                "amount": 0.1,
            }
        ]
        
        portfolio_manager.get_portfolio_status.return_value = {
            "total_value": 100000.0,
            "positions": [
                {
                    "symbol": "tBTCUSD",
                    "amount": 0.5,
                    "value": 18000.0,
                }
            ],
        }
        
        portfolio_manager.rebalance_portfolio.return_value = {
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
        
        # Return the mock service when the dependency is called
        mock.return_value = portfolio_manager
        yield portfolio_manager


@pytest.fixture
def mock_risk_manager():
    """Mock RiskManagerAsync for testing."""
    with patch("backend.api.portfolio.get_risk_manager") as mock:
        # Create a mock instance
        risk_manager = MagicMock()
        
        # Configure mock responses
        risk_manager.assess_portfolio_risk.return_value = {
            "total_risk_score": 0.5,
            "risk_factors": {
                "volatility": 0.3,
                "correlation": 0.2,
            },
        }
        
        # Return the mock service when the dependency is called
        mock.return_value = risk_manager
        yield risk_manager


@pytest.fixture
def mock_live_portfolio_service():
    """Mock LivePortfolioServiceAsync for testing."""
    with patch("backend.api.portfolio.get_live_portfolio_service") as mock:
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
        
        mock_service.get_live_portfolio_snapshot.return_value = portfolio_snapshot
        
        # Configure mock responses for get_portfolio_performance
        performance_metric = MagicMock()
        performance_metric.name = "Return"
        performance_metric.value = 2.1
        performance_metric.unit = "%"
        performance_metric.timestamp = datetime.now()
        
        mock_service.get_portfolio_performance.return_value = [performance_metric]
        
        # Configure mock responses for validate_trade
        trade_validation = MagicMock()
        trade_validation.is_valid = True
        trade_validation.message = "Trade is valid"
        trade_validation.available_balance = 25000.0
        trade_validation.required_balance = 18000.0
        trade_validation.max_trade_size = 0.69
        trade_validation.timestamp = datetime.now()
        
        mock_service.validate_trade.return_value = trade_validation
        
        # Return the mock service when the dependency is called
        mock.return_value = mock_service
        yield mock_service


def test_allocate_portfolio(mock_portfolio_manager, mock_risk_manager):
    """Test allocate_portfolio endpoint."""
    response = client.post(
        "/api/portfolio/allocate",
        json={
            "signals": [
                {
                    "symbol": "tBTCUSD",
                    "strength": 0.8,
                    "direction": "long",
                    "strategy": "ema_crossover",
                }
            ],
            "risk_profile": "moderate",
            "max_allocation_percent": 0.5,
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
    response = client.post(
        "/api/portfolio/process-signals",
        json={
            "signals": [
                {
                    "symbol": "tBTCUSD",
                    "strength": 0.8,
                    "direction": "long",
                    "strategy": "ema_crossover",
                }
            ],
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == ResponseStatus.SUCCESS
    assert "actions" in data
    assert len(data["actions"]) == 1
    
    # Verify the mock was called
    mock_portfolio_manager.process_signals.assert_called_once()


def test_get_portfolio_status(mock_portfolio_manager):
    """Test get_portfolio_status endpoint."""
    response = client.get("/api/portfolio/status")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == ResponseStatus.SUCCESS
    assert "portfolio_status" in data
    assert data["portfolio_status"]["total_value"] == 100000.0
    
    # Verify the mock was called
    mock_portfolio_manager.get_portfolio_status.assert_called_once()


def test_rebalance_portfolio(mock_portfolio_manager):
    """Test rebalance_portfolio endpoint."""
    response = client.post(
        "/api/portfolio/rebalance",
        json=[
            {
                "symbol": "tBTCUSD",
                "allocation": 0.6,
                "weight": 0.6,
            }
        ],
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == ResponseStatus.SUCCESS
    assert "rebalance_results" in data
    assert "trades" in data["rebalance_results"]
    
    # Verify the mock was called
    mock_portfolio_manager.rebalance_portfolio.assert_called_once()


def test_get_live_portfolio_snapshot(mock_live_portfolio_service):
    """Test get_live_portfolio_snapshot endpoint."""
    response = client.get("/api/portfolio/live/snapshot")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == ResponseStatus.SUCCESS
    assert "snapshot" in data
    assert data["snapshot"]["total_value"] == 100000.0
    assert data["snapshot"]["available_balance"] == 25000.0
    assert len(data["snapshot"]["positions"]) == 1
    assert data["snapshot"]["positions"][0]["symbol"] == "tBTCUSD"
    
    # Verify the mock was called
    mock_live_portfolio_service.get_live_portfolio_snapshot.assert_called_once()


def test_get_live_portfolio_snapshot_with_symbols(mock_live_portfolio_service):
    """Test get_live_portfolio_snapshot endpoint with specific symbols."""
    response = client.get("/api/portfolio/live/snapshot?symbols=tBTCUSD,tETHUSD")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == ResponseStatus.SUCCESS
    
    # Verify the mock was called with the right parameters
    mock_live_portfolio_service.get_live_portfolio_snapshot.assert_called_once()
    # Check that the symbols parameter was passed correctly
    call_args = mock_live_portfolio_service.get_live_portfolio_snapshot.call_args
    assert call_args is not None
    assert call_args[1].get("symbols") == ["tBTCUSD", "tETHUSD"]


def test_get_live_portfolio_performance(mock_live_portfolio_service):
    """Test get_live_portfolio_performance endpoint."""
    response = client.get("/api/portfolio/live/performance")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == ResponseStatus.SUCCESS
    assert "metrics" in data
    assert len(data["metrics"]) > 0
    
    # Verify the mock was called
    mock_live_portfolio_service.get_portfolio_performance.assert_called_once()
    # Default timeframe should be 24h
    call_args = mock_live_portfolio_service.get_portfolio_performance.call_args
    assert call_args is not None
    assert call_args[1].get("timeframe") == "24h"


def test_get_live_portfolio_performance_with_timeframe(mock_live_portfolio_service):
    """Test get_live_portfolio_performance endpoint with specific timeframe."""
    response = client.get("/api/portfolio/live/performance?timeframe=7d")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == ResponseStatus.SUCCESS
    
    # Verify the mock was called with the right parameters
    mock_live_portfolio_service.get_portfolio_performance.assert_called_once()
    # Check that the timeframe parameter was passed correctly
    call_args = mock_live_portfolio_service.get_portfolio_performance.call_args
    assert call_args is not None
    assert call_args[1].get("timeframe") == "7d"


def test_validate_live_trade(mock_live_portfolio_service):
    """Test validate_live_trade endpoint."""
    response = client.post(
        "/api/portfolio/live/validate-trade",
        params={
            "symbol": "tBTCUSD",
            "amount": 0.5,
            "trade_type": "buy",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == ResponseStatus.SUCCESS
    assert "validation_result" in data
    assert data["validation_result"]["is_valid"] is True
    
    # Verify the mock was called with the right parameters
    mock_live_portfolio_service.validate_trade.assert_called_once_with(
        symbol="tBTCUSD", amount=0.5, trade_type="buy"
    )


def test_validate_live_trade_invalid_type(mock_live_portfolio_service):
    """Test validate_live_trade endpoint with invalid trade type."""
    # Configure mock to raise ValueError for invalid trade_type
    mock_live_portfolio_service.validate_trade.side_effect = ValueError(
        "Invalid trade_type: invalid. Must be 'buy' or 'sell'"
    )
    
    response = client.post(
        "/api/portfolio/live/validate-trade",
        params={
            "symbol": "tBTCUSD",
            "amount": 0.5,
            "trade_type": "invalid",
        },
    )
    
    assert response.status_code == 400  # Bad Request
    data = response.json()
    
    assert "detail" in data
    assert "Invalid trade_type" in data["detail"]
