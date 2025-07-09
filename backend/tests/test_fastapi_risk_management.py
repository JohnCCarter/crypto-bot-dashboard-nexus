"""Integration tests for FastAPI risk management endpoints."""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.fastapi_app import app
from backend.services.risk_manager_async import RiskManagerAsync
from backend.services.order_service_async import OrderServiceAsync
from backend.api.models import ProbabilityDataModel, OrderData, ResponseStatus, OrderSide, OrderType


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_risk_manager():
    """Mock for RiskManagerAsync."""
    risk_manager = AsyncMock(spec=RiskManagerAsync)
    
    # Setup mock return values
    risk_manager.assess_portfolio_risk.return_value = {
        "total_risk_score": 0.35,
        "risk_level": "moderate",
        "positions_risk": 0.3,
        "orders_risk": 0.4,
        "exposure_risk": 0.35,
        "recommendations": ["Consider reducing exposure to BTC"]
    }
    
    risk_manager.validate_order.return_value = {
        "valid": True,
        "errors": [],
        "risk_assessment": {
            "order_risk": 0.25,
            "impact_on_portfolio": 0.2,
            "recommended_stop_loss": 12500.0,
            "recommended_take_profit": 14500.0
        }
    }
    
    risk_manager.validate_order_with_probabilities.return_value = {
        "valid": True,
        "errors": [],
        "risk_assessment": {
            "order_risk": 0.25,
            "probability_risk": 0.3,
            "impact_on_portfolio": 0.2,
            "recommended_stop_loss": 12500.0,
            "recommended_take_profit": 14500.0,
            "confidence_level": "high"
        }
    }
    
    return risk_manager


@pytest.fixture
def mock_order_service():
    """Mock for OrderServiceAsync."""
    order_service = AsyncMock()
    
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
            }
        ]
    }
    
    order_service.get_open_orders.return_value = [
        {
            "id": "1",
            "symbol": "ETH/USD",
            "side": "buy",
            "type": "limit",
            "price": 2000.0,
            "amount": 1.0,
            "status": "open"
        }
    ]
    
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


async def test_assess_portfolio_risk(client, mock_risk_manager, mock_order_service):
    """Test the assess portfolio risk endpoint."""
    from backend.api.dependencies import get_risk_manager, get_order_service
    
    # Override dependencies
    app.dependency_overrides[get_risk_manager] = lambda: mock_risk_manager
    app.dependency_overrides[get_order_service] = lambda: mock_order_service
    
    # Mock fetch_positions_async
    from backend.services.positions_service_async import fetch_positions_async
    original_fetch_positions = fetch_positions_async
    
    try:
        # Mock fetch_positions_async to return test data
        async def mock_fetch_positions():
            return [
                {
                    "id": "1",
                    "symbol": "BTC/USD",
                    "side": "buy",
                    "amount": 0.1,
                    "entry_price": 13000.0,
                    "mark_price": 13500.0,
                    "pnl": 50.0,
                    "pnl_percentage": 3.85
                }
            ]
        
        # Replace the function temporarily
        import backend.services.positions_service_async
        backend.services.positions_service_async.fetch_positions_async = mock_fetch_positions
        response = client.get("/api/risk/assessment")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ResponseStatus.SUCCESS
        assert "risk_assessment" in data
        assert "total_risk_score" in data["risk_assessment"]
        assert "risk_level" in data["risk_assessment"]
        assert data["risk_assessment"]["risk_level"] in ["low", "moderate", "high", "critical"]
        
        # Verify mock calls
        mock_order_service.get_open_orders.assert_called_once()
        mock_risk_manager.assess_portfolio_risk.assert_called_once()
    finally:
        # Clean up
        app.dependency_overrides.clear()
        # Restore original function
        backend.services.positions_service_async.fetch_positions_async = original_fetch_positions


@patch("backend.api.dependencies.get_risk_manager")
@patch("backend.api.dependencies.get_order_service")
@patch("backend.api.dependencies.get_exchange_service")
async def test_validate_order(mock_get_exchange_service, mock_get_order_service, 
                             mock_get_risk_manager, client, mock_risk_manager, 
                             mock_order_service, mock_exchange_service):
    """Test the validate order endpoint."""
    mock_get_risk_manager.return_value = mock_risk_manager
    mock_get_order_service.return_value = mock_order_service
    mock_get_exchange_service.return_value = mock_exchange_service
    
    # Test without probability data
    order_data = {
        "symbol": "BTC/USD",
        "side": "buy",
        "type": "limit",
        "amount": 0.1,
        "price": 13000.0,
        "stop_price": None,
        "take_profit": 14000.0,
        "stop_loss": 12000.0
    }
    
    response = client.post("/api/risk/validate/order", json={"order_data": order_data})
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ResponseStatus.SUCCESS
    assert data["valid"] is True
    assert "risk_assessment" in data
    assert data["risk_assessment"]["order_risk"] == 0.25
    
    # Test with probability data
    order_with_probability = {
        **order_data,
        "probability_data": {
            "probability_buy": 0.7,
            "probability_sell": 0.2,
            "probability_hold": 0.1,
            "confidence": 0.8
        }
    }
    
    response = client.post("/api/risk/validate/order", json={"order_data": order_with_probability})
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ResponseStatus.SUCCESS
    assert data["valid"] is True
    assert "risk_assessment" in data
    assert data["risk_assessment"]["probability_risk"] == 0.3
    assert data["risk_assessment"]["confidence_level"] == "high"
    
    # Verify mock calls
    mock_exchange_service.fetch_balance_async.assert_called()
    mock_order_service.get_positions.assert_called()
    mock_risk_manager.validate_order.assert_called_once()
    mock_risk_manager.validate_order_with_probabilities.assert_called_once()


@patch("backend.api.dependencies.get_risk_manager")
async def test_get_risk_score(mock_get_risk_manager, client, mock_risk_manager):
    """Test the risk score endpoint."""
    mock_get_risk_manager.return_value = mock_risk_manager
    
    # Test query params
    response = client.get("/api/risk/score?symbol=BTC/USD&probability_buy=0.7&probability_sell=0.2&probability_hold=0.1&confidence=0.8")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ResponseStatus.SUCCESS
    assert data["symbol"] == "BTC/USD"
    assert "risk_score" in data
    assert "risk_level" in data
    assert "probability_data" in data
    assert data["probability_data"]["probability_buy"] == 0.7
    
    # Test with invalid probabilities (sum > 1.0)
    response = client.get("/api/risk/score?symbol=BTC/USD&probability_buy=0.7&probability_sell=0.5&probability_hold=0.1&confidence=0.8")
    
    # Should still work but with normalized probabilities
    assert response.status_code == 200


@patch("backend.api.dependencies.get_risk_manager")
@patch("backend.api.dependencies.get_order_service")
async def test_error_handling(mock_get_order_service, mock_get_risk_manager, 
                             client, mock_risk_manager, mock_order_service):
    """Test error handling in endpoints."""
    mock_get_risk_manager.return_value = mock_risk_manager
    mock_get_order_service.return_value = mock_order_service
    
    # Simulate an error in the risk manager
    mock_risk_manager.assess_portfolio_risk.side_effect = Exception("Test error")
    
    response = client.get("/api/risk/assessment")
    
    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Test error" in data["detail"]
