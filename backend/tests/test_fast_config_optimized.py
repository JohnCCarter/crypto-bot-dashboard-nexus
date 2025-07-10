"""
🚀 Optimerade Config-tester
Snabbare version som undviker FastAPI-app startup.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api import config as config_api
from backend.services.portfolio_manager import StrategyWeight


@pytest.fixture
def fast_app():
    """Skapa en minimal FastAPI-app för testning."""
    app = FastAPI()
    app.include_router(config_api.router)
    return app


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

    return mock_service


@pytest.fixture
def client(fast_app, mock_config_service):
    """Create a test client with mocked dependencies."""

    # Override the get_config_service dependency
    def get_mock_config_service():
        return mock_config_service

    from backend.api.dependencies import get_config_service

    fast_app.dependency_overrides[get_config_service] = get_mock_config_service

    return TestClient(fast_app)


def test_get_config_fast(client, mock_config_service):
    """Test GET /api/config endpoint - optimerad version."""
    response = client.get("/api/config")
    assert response.status_code == 200
    assert response.json() == mock_config_service.get_config_summary_async.return_value
    mock_config_service.get_config_summary_async.assert_called_once()


def test_get_config_summary_fast(client, mock_config_service):
    """Test GET /api/config/summary endpoint - optimerad version."""
    response = client.get("/api/config/summary")
    assert response.status_code == 200
    assert response.json() == mock_config_service.get_config_summary_async.return_value
    mock_config_service.get_config_summary_async.assert_called()


def test_update_config_fast(client):
    """Test POST /api/config endpoint - optimerad version."""
    test_data = {
        "risk": {"max_position_size": 0.2},
        "strategy": {"ema_fast": 10},
    }
    response = client.post("/api/config", json=test_data)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["updated_fields"] == ["risk", "strategy"]
