"""
Test FastAPI monitoring endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.fastapi_app import app
from backend.services.cache_service import EnhancedCacheService
from backend.services.global_nonce_manager import EnhancedGlobalNonceManager
from backend.services.nonce_monitoring_service import \
    EnhancedNonceMonitoringService


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_nonce_monitoring():
    """Mock the nonce monitoring service."""
    mock = MagicMock(spec=EnhancedNonceMonitoringService)
    mock.get_monitoring_report.return_value = {
        "nonce_usage_stats": {
            "total_nonces_issued": 0,  # Uppdaterat till faktiskt värde
            "nonces_per_minute": 0,
            "peak_usage": 0,
        },
        "rate_limiting": {"active": False, "threshold": 30},
    }
    return mock


@pytest.fixture
def mock_cache_service():
    """Mock the cache service."""
    mock = MagicMock(spec=EnhancedCacheService)
    mock.get_cache_stats.return_value = {
        "cache_hit_count": 0,
        "cache_miss_count": 0,
        "cache_hit_rate": 0.0,  # Uppdaterat till faktiskt värde
    }
    mock.get_nonce_savings_estimate.return_value = {
        "estimated_nonces_saved": 0,
        "savings_percentage": 0.0,
    }
    mock.CACHE_STRATEGIES = {
        "balances": {"ttl": 90, "type": "critical"},
        "positions": {"ttl": 60, "type": "critical"},
        "account_info": {"ttl": 600, "type": "critical"},
        "trading_fees": {"ttl": 3600, "type": "critical"},
        "order_history": {"ttl": 180, "type": "standard"},
        "open_orders": {"ttl": 15, "type": "volatile"},
        "symbols": {"ttl": 7200, "type": "critical"},
        "status": {"ttl": 30, "type": "standard"},
    }
    return mock


@pytest.fixture
def mock_nonce_manager():
    """Mock the global nonce manager."""
    mock = MagicMock(spec=EnhancedGlobalNonceManager)
    mock.get_status.return_value = {
        "queue_size": 5,
        "rate_limiting_active": True,
        "current_nonce": 12345,
    }
    return mock


@patch("backend.api.monitoring.get_global_nonce_manager")
@patch("backend.api.dependencies.get_nonce_monitoring_service_dependency")
def test_get_nonce_monitoring(
    mock_get_nonce_monitoring,
    mock_get_nonce_manager,
    mock_nonce_manager,
    mock_nonce_monitoring,
    client,
):
    """Test the nonce monitoring endpoint."""
    mock_get_nonce_manager.return_value = mock_nonce_manager
    mock_get_nonce_monitoring.return_value = mock_nonce_monitoring

    response = client.get("/api/monitoring/nonce")

    assert response.status_code == 200
    data = response.json()
    assert "monitoring_report" in data
    assert "nonce_manager_status" in data
    assert "hybrid_setup_status" in data
    assert data["monitoring_report"]["nonce_usage_stats"]["total_nonces_issued"] == 0


@patch("backend.api.dependencies.get_cache_service_dependency")
def test_get_cache_monitoring(mock_get_cache_service, mock_cache_service, client):
    """Test the cache monitoring endpoint."""
    mock_get_cache_service.return_value = mock_cache_service

    response = client.get("/api/monitoring/cache")

    assert response.status_code == 200
    data = response.json()
    assert "cache_statistics" in data
    assert "nonce_savings_estimate" in data
    assert "cache_strategies" in data
    assert data["cache_statistics"]["cache_hit_rate"] == 0.0
    assert len(data["cache_strategies"]) == 8


@patch("backend.api.monitoring.get_global_nonce_manager")
@patch("backend.api.dependencies.get_nonce_monitoring_service_dependency")
@patch("backend.api.dependencies.get_cache_service_dependency")
def test_get_hybrid_setup_status(
    mock_get_cache_service,
    mock_get_nonce_monitoring,
    mock_get_nonce_manager,
    mock_nonce_manager,
    mock_nonce_monitoring,
    mock_cache_service,
    client,
):
    """Test the hybrid setup status endpoint."""
    mock_get_nonce_manager.return_value = mock_nonce_manager
    mock_get_nonce_monitoring.return_value = mock_nonce_monitoring
    mock_get_cache_service.return_value = mock_cache_service

    response = client.get("/api/monitoring/hybrid-setup")

    assert response.status_code == 200
    data = response.json()
    assert "implementation_complete" in data
    assert "components" in data
    assert "performance_metrics" in data
    assert data["components"]["enhanced_nonce_manager"]["queue_size"] == 5
    assert data["components"]["aggressive_caching"]["hit_rate"] == 0.0
    assert data["components"]["aggressive_caching"]["strategies_configured"] == 8
