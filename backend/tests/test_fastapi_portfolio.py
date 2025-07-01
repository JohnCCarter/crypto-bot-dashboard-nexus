"""Integration tests for FastAPI portfolio management endpoints."""

import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.fastapi_app import app
from backend.services.portfolio_manager_async import PortfolioManagerAsync
from backend.services.order_service_async import OrderServiceAsync
from backend.api.models import (
    SignalData, 
    StrategySignalRequest, 
    ResponseStatus, 
    PortfolioAllocationRequest,
    RiskProfile
)


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_portfolio_manager():
    """Mock for PortfolioManagerAsync."""
    portfolio_manager = AsyncMock(spec=PortfolioManagerAsync)
    
    # Setup mock return values
    portfolio_manager.calculate_allocation.return_value = [
        {
            "symbol": "BTC/USD",
            "percentage": 0.4,
            "amount": 4000.0,
            "action": "buy",
            "current_allocation": 0.3,
            "target_allocation": 0.4
        },
        {
            "symbol": "ETH/USD",
            "percentage": 0.3,
            "amount": 3000.0,
            "action": "buy",
            "current_allocation": 0.2,
            "target_allocation": 0.3
        },
        {
            "symbol": "cash",
            "percentage": 0.3,
            "amount": 3000.0,
            "action": "hold",
            "current_allocation": 0.5,
            "target_allocation": 0.3
        }
    ]
    
    portfolio_manager.process_strategy_signals.return_value = [
        {
            "symbol": "BTC/USD",
            "action": "buy",
            "strength": 0.7,
            "price": 13500.0,
            "quantity": 0.1,
            "reasoning": "Strong uptrend detected",
            "confidence": 0.8
        },
        {
            "symbol": "ETH/USD",
            "action": "hold",
            "strength": 0.5,
            "price": 2100.0,
            "quantity": 0,
            "reasoning": "Consolidation pattern",
            "confidence": 0.6
        }
    ]
    
    portfolio_manager.get_portfolio_status.return_value = {
        "total_value": 10000.0,
        "cash_value": 5000.0,
        "invested_value": 5000.0,
        "pnl_daily": 200.0,
        "pnl_total": 500.0,
        "risk_score": 0.4,
        "diversification_score": 0.7,
        "allocations": [
            {"symbol": "BTC/USD", "percentage": 0.3, "value": 3000.0},
            {"symbol": "ETH/USD", "percentage": 0.2, "value": 2000.0},
            {"symbol": "cash", "percentage": 0.5, "value": 5000.0}
        ]
    }
    
    portfolio_manager.rebalance_portfolio.return_value = {
        "rebalance_required": True,
        "trades_needed": [
            {"symbol": "BTC/USD", "action": "buy", "amount": 0.05, "price": 13500.0},
            {"symbol": "ETH/USD", "action": "buy", "amount": 0.5, "price": 2100.0}
        ],
        "new_allocation": [
            {"symbol": "BTC/USD", "percentage": 0.4, "value": 4000.0},
            {"symbol": "ETH/USD", "percentage": 0.3, "value": 3000.0},
            {"symbol": "cash", "percentage": 0.3, "value": 3000.0}
        ],
        "rebalance_cost": 5.0
    }
    
    return portfolio_manager


@pytest.fixture
def mock_order_service():
    """Mock for OrderServiceAsync."""
    order_service = AsyncMock(spec=OrderServiceAsync)
    
    # Setup mock return values
    order_service.get_positions.return_value = {
        "positions": [
            {
                "id": "1",
                "symbol": "BTC/USD",
                "side": "buy",
                "amount": 0.1,
                "entry_price": 13000.0,
                "mark_price": 13500.0,
                "pnl": 50.0,
                "pnl_percentage": 3.85
            },
            {
                "id": "2",
                "symbol": "ETH/USD",
                "side": "buy",
                "amount": 1.0,
                "entry_price": 2000.0,
                "mark_price": 2100.0,
                "pnl": 100.0,
                "pnl_percentage": 5.0
            }
        ]
    }
    
    order_service.get_open_orders.return_value = {
        "orders": [
            {
                "id": "1",
                "symbol": "BTC/USD",
                "side": "buy",
                "type": "limit",
                "price": 13000.0,
                "amount": 0.05,
                "status": "open"
            }
        ]
    }
    
    return order_service


@pytest.fixture
def mock_exchange_service():
    """Mock for ExchangeService."""
    exchange_service = MagicMock()
    
    # Setup mock return values
    exchange_service.fetch_balance_async.return_value = {
        "total": {"USD": 10000.0, "BTC": 0.1, "ETH": 1.0},
        "free": {"USD": 5000.0, "BTC": 0.05, "ETH": 0.5}
    }
    
    return exchange_service


@pytest.fixture
def sample_signals():
    """Create sample signals for testing."""
    return [
        {
            "symbol": "BTC/USD",
            "signal_type": "buy",
            "strength": 0.8,
            "confidence": 0.75,
            "timestamp": datetime.now().isoformat(),
            "source": "ema_crossover",
            "indicators": {
                "ema_short": 13200,
                "ema_long": 13100
            },
            "price": 13500.0
        },
        {
            "symbol": "ETH/USD",
            "signal_type": "hold",
            "strength": 0.5,
            "confidence": 0.6,
            "timestamp": datetime.now().isoformat(),
            "source": "rsi_strategy",
            "indicators": {
                "rsi": 55
            },
            "price": 2100.0
        }
    ]


@patch("backend.api.dependencies.get_portfolio_manager")
@patch("backend.api.dependencies.get_exchange_service")
async def test_allocate_portfolio(mock_get_exchange_service, mock_get_portfolio_manager,
                                 client, mock_portfolio_manager, mock_exchange_service, 
                                 sample_signals):
    """Test the allocate portfolio endpoint."""
    mock_get_portfolio_manager.return_value = mock_portfolio_manager
    mock_get_exchange_service.return_value = mock_exchange_service
    
    allocation_request = {
        "signals": sample_signals,
        "risk_profile": RiskProfile.MODERATE,
        "max_allocation_percent": 0.8,
        "timestamp": datetime.now().isoformat()
    }
    
    response = client.post("/api/portfolio/allocate", json=allocation_request)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ResponseStatus.SUCCESS
    assert "allocations" in data
    assert len(data["allocations"]) == 3
    assert data["allocations"][0]["symbol"] == "BTC/USD"
    assert data["allocations"][0]["percentage"] == 0.4
    
    # Verify mock calls
    mock_exchange_service.fetch_balance_async.assert_called_once()
    mock_portfolio_manager.calculate_allocation.assert_called_once()


@patch("backend.api.dependencies.get_portfolio_manager")
@patch("backend.api.dependencies.get_order_service")
async def test_process_strategy_signals(mock_get_order_service, mock_get_portfolio_manager,
                                       client, mock_portfolio_manager, mock_order_service,
                                       sample_signals):
    """Test the process strategy signals endpoint."""
    mock_get_portfolio_manager.return_value = mock_portfolio_manager
    mock_get_order_service.return_value = mock_order_service
    
    signal_request = {
        "signals": sample_signals,
        "timestamp": datetime.now().isoformat()
    }
    
    response = client.post("/api/portfolio/process-signals", json=signal_request)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ResponseStatus.SUCCESS
    assert "actions" in data
    assert len(data["actions"]) == 2
    assert data["actions"][0]["symbol"] == "BTC/USD"
    assert data["actions"][0]["action"] == "buy"
    
    # Verify mock calls
    mock_order_service.get_positions.assert_called_once()
    mock_portfolio_manager.process_strategy_signals.assert_called_once()


@patch("backend.api.dependencies.get_portfolio_manager")
@patch("backend.api.dependencies.get_order_service")
@patch("backend.api.dependencies.get_exchange_service")
async def test_get_portfolio_status(mock_get_exchange_service, mock_get_order_service,
                                   mock_get_portfolio_manager, client, 
                                   mock_portfolio_manager, mock_order_service,
                                   mock_exchange_service):
    """Test the get portfolio status endpoint."""
    mock_get_portfolio_manager.return_value = mock_portfolio_manager
    mock_get_order_service.return_value = mock_order_service
    mock_get_exchange_service.return_value = mock_exchange_service
    
    response = client.get("/api/portfolio/status")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ResponseStatus.SUCCESS
    assert "portfolio_status" in data
    assert data["portfolio_status"]["total_value"] == 10000.0
    assert data["portfolio_status"]["risk_score"] == 0.4
    assert len(data["portfolio_status"]["allocations"]) == 3
    
    # Verify mock calls
    mock_order_service.get_positions.assert_called_once()
    mock_order_service.get_open_orders.assert_called_once()
    mock_exchange_service.fetch_balance_async.assert_called_once()
    mock_portfolio_manager.get_portfolio_status.assert_called_once()


@patch("backend.api.dependencies.get_portfolio_manager")
@patch("backend.api.dependencies.get_order_service")
@patch("backend.api.dependencies.get_exchange_service")
async def test_rebalance_portfolio(mock_get_exchange_service, mock_get_order_service,
                                  mock_get_portfolio_manager, client, 
                                  mock_portfolio_manager, mock_order_service,
                                  mock_exchange_service):
    """Test the rebalance portfolio endpoint."""
    mock_get_portfolio_manager.return_value = mock_portfolio_manager
    mock_get_order_service.return_value = mock_order_service
    mock_get_exchange_service.return_value = mock_exchange_service
    
    response = client.post("/api/portfolio/rebalance")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ResponseStatus.SUCCESS
    assert "rebalance_results" in data
    assert data["rebalance_results"]["rebalance_required"] is True
    assert len(data["rebalance_results"]["trades_needed"]) == 2
    assert data["rebalance_results"]["rebalance_cost"] == 5.0
    
    # Verify mock calls
    mock_order_service.get_positions.assert_called_once()
    mock_exchange_service.fetch_balance_async.assert_called_once()
    mock_portfolio_manager.rebalance_portfolio.assert_called_once()


@patch("backend.api.dependencies.get_portfolio_manager")
@patch("backend.api.dependencies.get_exchange_service")
async def test_error_handling(mock_get_exchange_service, mock_get_portfolio_manager,
                             client, mock_portfolio_manager, mock_exchange_service,
                             sample_signals):
    """Test error handling in endpoints."""
    mock_get_portfolio_manager.return_value = mock_portfolio_manager
    mock_get_exchange_service.return_value = mock_exchange_service
    
    # Simulate an error in the portfolio manager
    mock_portfolio_manager.calculate_allocation.side_effect = Exception("Test error")
    
    allocation_request = {
        "signals": sample_signals,
        "risk_profile": RiskProfile.MODERATE,
        "max_allocation_percent": 0.8,
        "timestamp": datetime.now().isoformat()
    }
    
    response = client.post("/api/portfolio/allocate", json=allocation_request)
    
    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Test error" in data["detail"]


@patch("backend.api.dependencies.get_portfolio_manager")
@patch("backend.api.dependencies.get_exchange_service")
async def test_invalid_input(mock_get_exchange_service, mock_get_portfolio_manager,
                            client, mock_portfolio_manager, mock_exchange_service):
    """Test validation of invalid input."""
    mock_get_portfolio_manager.return_value = mock_portfolio_manager
    mock_get_exchange_service.return_value = mock_exchange_service
    
    # Missing required signals
    allocation_request = {
        "risk_profile": RiskProfile.MODERATE,
        "max_allocation_percent": 0.8,
        "timestamp": datetime.now().isoformat()
    }
    
    response = client.post("/api/portfolio/allocate", json=allocation_request)
    
    # Assertions - should get a validation error
    assert response.status_code == 422  # Unprocessable Entity
