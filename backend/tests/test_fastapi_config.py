"""
Tests for FastAPI config endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from backend.fastapi_app import app
from backend.services.portfolio_manager import StrategyWeight


@pytest.fixture
def mock_config_service():
    """Create a mock config service."""
    mock_service = AsyncMock()
    
    # Setup mock responses
    mock_service.get_config_summary_async.return_value = {
        "config_file": "backend/config.json",
        "config_valid": True,
        "validation_errors": [],
        "enabled_strategies": ["ema_crossover", "rsi"],
        "total_strategy_count": 3,
        "risk_management": {
            "max_position_size": 0.1,
            "min_signal_confidence": 0.6,
            "probability_weight": 0.5,
        },
        "probability_framework": {
            "combination_method": "weighted_average",
            "dynamic_weights_enabled": True,
            "risk_threshold": 0.8,
        },
    }
    
    # Setup strategy weights
    strategy_weights = [
        StrategyWeight(
            strategy_name="ema_crossover",
            weight=0.6,
            min_confidence=0.6,
            enabled=True,
        ),
        StrategyWeight(
            strategy_name="rsi",
            weight=0.4,
            min_confidence=0.5,
            enabled=True,
        ),
        StrategyWeight(
            strategy_name="fvg",
            weight=0.0,
            min_confidence=0.5,
            enabled=False,
        ),
    ]
    mock_service.get_strategy_weights_async.return_value = strategy_weights
    
    # Setup strategy params
    mock_service.get_strategy_params_async.return_value = {
        "symbol": "BTC/USD",
        "timeframe": "1h",
        "ema_fast": 12,
        "ema_slow": 26,
        "weight": 0.6,
        "min_confidence": 0.6,
        "enabled": True,
    }
    
    # Setup update strategy weight
    mock_service.update_strategy_weight_async.return_value = True
    
    # Setup load config
    mock_config = MagicMock()
    mock_config.probability_settings = {
        "confidence_threshold_buy": 0.7,
        "confidence_threshold_sell": 0.7,
        "confidence_threshold_hold": 0.6,
        "risk_score_threshold": 0.8,
        "combination_method": "weighted_average",
        "enable_dynamic_weights": True,
    }
    mock_config.risk_config = {
        "min_signal_confidence": 0.6,
        "probability_weight": 0.5,
    }
    mock_service.load_config_async.return_value = mock_config
    
    # Setup update probability settings
    mock_service.update_probability_settings_async.return_value = True
    
    # Setup validate config
    mock_service.validate_config_async.return_value = []
    
    return mock_service


@pytest.fixture
def client(mock_config_service):
    """Create a test client with mocked dependencies."""
    
    app.dependency_overrides = {}
    
    # Override the get_config_service dependency
    def get_mock_config_service():
        return mock_config_service
    
    from backend.api.dependencies import get_config_service
    app.dependency_overrides[get_config_service] = get_mock_config_service
    
    return TestClient(app)


def test_get_config(client, mock_config_service):
    """Test GET /api/config endpoint."""
    response = client.get("/api/config")
    assert response.status_code == 200
    assert response.json() == mock_config_service.get_config_summary_async.return_value
    mock_config_service.get_config_summary_async.assert_called_once()


def test_update_config(client):
    """Test POST /api/config endpoint."""
    test_data = {
        "risk": {"max_position_size": 0.2},
        "strategy": {"ema_fast": 10},
    }
    response = client.post("/api/config", json=test_data)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["updated_fields"] == ["risk", "strategy"]


def test_get_config_summary(client, mock_config_service):
    """Test GET /api/config/summary endpoint."""
    response = client.get("/api/config/summary")
    assert response.status_code == 200
    assert response.json() == mock_config_service.get_config_summary_async.return_value
    mock_config_service.get_config_summary_async.assert_called()


def test_get_strategy_config(client, mock_config_service):
    """Test GET /api/config/strategies endpoint."""
    response = client.get("/api/config/strategies")
    assert response.status_code == 200
    
    # Check response structure
    result = response.json()
    assert "strategy_weights" in result
    assert "total_strategies" in result
    assert "enabled_strategies" in result
    
    # Check values
    assert len(result["strategy_weights"]) == 3
    assert result["total_strategies"] == 3
    assert result["enabled_strategies"] == 2
    
    # Check strategy weights
    weights = result["strategy_weights"]
    assert any(w["strategy_name"] == "ema_crossover" and w["weight"] == 0.6 for w in weights)
    assert any(w["strategy_name"] == "rsi" and w["weight"] == 0.4 for w in weights)
    assert any(w["strategy_name"] == "fvg" and w["enabled"] is False for w in weights)
    
    mock_config_service.get_strategy_weights_async.assert_called_once()


def test_get_strategy_params(client, mock_config_service):
    """Test GET /api/config/strategy/{strategy_name} endpoint."""
    response = client.get("/api/config/strategy/ema_crossover")
    assert response.status_code == 200
    
    result = response.json()
    assert result["strategy_name"] == "ema_crossover"
    assert "parameters" in result
    assert result["parameters"]["ema_fast"] == 12
    assert result["parameters"]["ema_slow"] == 26
    
    mock_config_service.get_strategy_params_async.assert_called_once_with("ema_crossover")


def test_update_strategy_weight(client, mock_config_service):
    """Test PUT /api/config/strategy/{strategy_name}/weight endpoint."""
    test_data = {"weight": 0.8}
    response = client.put("/api/config/strategy/ema_crossover/weight", json=test_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["message"] == "Updated ema_crossover weight to 0.8"
    assert result["strategy_name"] == "ema_crossover"
    assert result["new_weight"] == 0.8
    
    mock_config_service.update_strategy_weight_async.assert_called_once_with("ema_crossover", 0.8)


def test_update_strategy_weight_invalid(client):
    """Test PUT /api/config/strategy/{strategy_name}/weight endpoint with invalid weight."""
    test_data = {"weight": 1.5}  # Invalid weight > 1.0
    response = client.put("/api/config/strategy/ema_crossover/weight", json=test_data)
    assert response.status_code == 422  # FastAPI validation error
    assert "Input should be less than or equal to 1" in str(response.json())


def test_get_probability_config(client, mock_config_service):
    """Test GET /api/config/probability endpoint."""
    response = client.get("/api/config/probability")
    assert response.status_code == 200
    
    result = response.json()
    assert "probability_settings" in result
    assert "risk_config" in result
    
    # Check values
    assert result["probability_settings"]["confidence_threshold_buy"] == 0.7
    assert result["risk_config"]["min_signal_confidence"] == 0.6
    
    mock_config_service.load_config_async.assert_called_once()


def test_update_probability_config(client, mock_config_service):
    """Test PUT /api/config/probability endpoint."""
    test_data = {
        "probability_settings": {
            "confidence_threshold_buy": 0.8,
            "confidence_threshold_sell": 0.8,
            "confidence_threshold_hold": 0.7,
            "risk_score_threshold": 0.9,
        }
    }
    response = client.put("/api/config/probability", json=test_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["message"] == "Probability settings updated successfully"
    assert result["updated_settings"] == test_data["probability_settings"]
    
    mock_config_service.update_probability_settings_async.assert_called_once_with(
        test_data["probability_settings"]
    )


def test_update_probability_config_invalid(client):
    """Test PUT /api/config/probability endpoint with invalid values."""
    test_data = {
        "probability_settings": {
            "confidence_threshold_buy": 1.2,  # Invalid > 1.0
        }
    }
    response = client.put("/api/config/probability", json=test_data)
    assert response.status_code == 400  # API validation error
    assert "must be between 0.0 and 1.0" in str(response.json())


def test_validate_config(client, mock_config_service):
    """Test GET /api/config/validate endpoint."""
    response = client.get("/api/config/validate")
    assert response.status_code == 200
    
    result = response.json()
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["error_count"] == 0
    
    mock_config_service.validate_config_async.assert_called_once()


def test_validate_config_with_errors(client, mock_config_service):
    """Test GET /api/config/validate endpoint with validation errors."""
    # Mock validation errors
    mock_config_service.validate_config_async.return_value = [
        "max_position_size must be between 0 and 1",
        "At least one strategy must be enabled",
    ]
    
    response = client.get("/api/config/validate")
    assert response.status_code == 200
    
    result = response.json()
    assert result["valid"] is False
    assert len(result["errors"]) == 2
    assert result["error_count"] == 2
    
    mock_config_service.validate_config_async.assert_called_once()


def test_reload_config(client, mock_config_service):
    """Test POST /api/config/reload endpoint."""
    response = client.post("/api/config/reload")
    assert response.status_code == 200
    
    result = response.json()
    assert result["message"] == "Configuration reloaded successfully"
    assert result["config_valid"] is True
    assert result["validation_errors"] == []
    
    mock_config_service.load_config_async.assert_called_with(force_reload=True)
    mock_config_service.validate_config_async.assert_called_once()


def test_reload_config_with_errors(client, mock_config_service):
    """Test POST /api/config/reload endpoint with validation errors."""
    # Mock validation errors
    mock_config_service.validate_config_async.return_value = [
        "max_position_size must be between 0 and 1",
    ]
    
    response = client.post("/api/config/reload")
    assert response.status_code == 200
    
    result = response.json()
    assert result["message"] == "Configuration reloaded successfully"
    assert result["config_valid"] is False
    assert len(result["validation_errors"]) == 1
    
    mock_config_service.load_config_async.assert_called_with(force_reload=True)
    mock_config_service.validate_config_async.assert_called_once()


def test_error_handling(client, mock_config_service):
    """Test error handling in endpoints."""
    # Mock an exception
    mock_config_service.get_config_summary_async.side_effect = Exception("Test error")
    
    response = client.get("/api/config")
    assert response.status_code == 200  # Returns a valid ConfigSummary with error info
    assert "Test error" in str(response.json()["validation_errors"])
