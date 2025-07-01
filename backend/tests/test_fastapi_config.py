"""Tests for FastAPI config endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.fastapi_app import app
from backend.services.config_service import ConfigService
from unittest.mock import patch, MagicMock

client = TestClient(app)


@pytest.fixture
def mock_config_service():
    """Mock config service for testing."""
    with patch("backend.api.dependencies.config_service") as mock:
        # Konfigurera mock-metoder
        mock.get_config_summary_async = MagicMock()
        mock.get_config_summary_async.return_value = {
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
        
        mock.load_config_async = MagicMock()
        mock.load_config_async.return_value = MagicMock(
            probability_settings={
                "confidence_threshold_buy": 0.7,
                "confidence_threshold_sell": 0.7,
                "confidence_threshold_hold": 0.6,
                "risk_score_threshold": 0.8,
            },
            risk_config={
                "min_signal_confidence": 0.6,
                "probability_weight": 0.5,
            }
        )
        
        mock.get_strategy_weights_async = MagicMock()
        mock.get_strategy_weights_async.return_value = [
            MagicMock(
                strategy_name="ema_crossover",
                weight=0.4,
                min_confidence=0.6,
                enabled=True
            ),
            MagicMock(
                strategy_name="rsi",
                weight=0.3,
                min_confidence=0.5,
                enabled=True
            ),
            MagicMock(
                strategy_name="fvg",
                weight=0.2,
                min_confidence=0.5,
                enabled=False
            ),
        ]
        
        mock.get_strategy_params_async = MagicMock()
        mock.get_strategy_params_async.return_value = {
            "symbol": "BTC/USD",
            "timeframe": "1h",
            "ema_fast": 12,
            "ema_slow": 26,
            "weight": 0.4,
            "min_confidence": 0.6,
            "enabled": True,
        }
        
        mock.update_strategy_weight_async = MagicMock()
        mock.update_strategy_weight_async.return_value = True
        
        mock.update_probability_settings_async = MagicMock()
        mock.update_probability_settings_async.return_value = True
        
        mock.validate_config_async = MagicMock()
        mock.validate_config_async.return_value = []
        
        yield mock


def test_get_config(mock_config_service):
    """Test get_config endpoint."""
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["config_valid"] is True
    assert "enabled_strategies" in data
    assert "risk_management" in data
    assert "probability_framework" in data


def test_get_config_summary(mock_config_service):
    """Test get_config_summary endpoint."""
    response = client.get("/api/config/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["config_valid"] is True
    assert "enabled_strategies" in data
    assert "risk_management" in data
    assert "probability_framework" in data


def test_get_strategy_config(mock_config_service):
    """Test get_strategy_config endpoint."""
    response = client.get("/api/config/strategies")
    assert response.status_code == 200
    data = response.json()
    assert "strategy_weights" in data
    assert "total_strategies" in data
    assert "enabled_strategies" in data
    assert data["total_strategies"] == 3
    assert data["enabled_strategies"] == 2


def test_get_strategy_params(mock_config_service):
    """Test get_strategy_params endpoint."""
    response = client.get("/api/config/strategy/ema_crossover")
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_name"] == "ema_crossover"
    assert "parameters" in data
    assert data["parameters"]["symbol"] == "BTC/USD"
    assert data["parameters"]["timeframe"] == "1h"
    assert data["parameters"]["ema_fast"] == 12
    assert data["parameters"]["ema_slow"] == 26


def test_update_strategy_weight(mock_config_service):
    """Test update_strategy_weight endpoint."""
    response = client.put(
        "/api/config/strategy/ema_crossover/weight",
        json={"weight": 0.5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Updated ema_crossover weight to 0.5"
    assert data["strategy_name"] == "ema_crossover"
    assert data["new_weight"] == 0.5


def test_get_probability_config(mock_config_service):
    """Test get_probability_config endpoint."""
    response = client.get("/api/config/probability")
    assert response.status_code == 200
    data = response.json()
    assert "probability_settings" in data
    assert "risk_config" in data
    assert data["probability_settings"]["confidence_threshold_buy"] == 0.7
    assert data["probability_settings"]["confidence_threshold_sell"] == 0.7
    assert data["probability_settings"]["confidence_threshold_hold"] == 0.6
    assert data["probability_settings"]["risk_score_threshold"] == 0.8


def test_update_probability_config(mock_config_service):
    """Test update_probability_config endpoint."""
    response = client.put(
        "/api/config/probability",
        json={
            "probability_settings": {
                "confidence_threshold_buy": 0.8,
                "confidence_threshold_sell": 0.8,
                "confidence_threshold_hold": 0.7,
                "risk_score_threshold": 0.9,
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Probability settings updated successfully"
    assert "updated_settings" in data


def test_validate_config(mock_config_service):
    """Test validate_config endpoint."""
    response = client.get("/api/config/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["errors"] == []
    assert data["error_count"] == 0


def test_reload_config(mock_config_service):
    """Test reload_config endpoint."""
    response = client.post("/api/config/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Configuration reloaded successfully"
    assert data["config_valid"] is True
    assert data["validation_errors"] == [] 