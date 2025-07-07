from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.services.exchange import ExchangeService
from backend.fastapi_app import app


@pytest.fixture(scope="session")
def fastapi_app():
    """
    Skapa en FastAPI-app en gång per test-session.
    Detta undviker att skapa app för varje test.
    """
    return app


@pytest.fixture
def test_client(fastapi_app):
    """
    Skapa en TestClient med optimerad konfiguration.
    """
    # Sätt miljövariabler för snabbare testning
    import os
    os.environ["FASTAPI_DISABLE_WEBSOCKETS"] = "true"
    os.environ["FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER"] = "true"
    os.environ["FASTAPI_DEV_MODE"] = "true"
    
    return TestClient(fastapi_app)


@pytest.fixture
def exchange_service_mock():
    """
    Provides a mocked ExchangeService instance where time.time() is patched
    to ensure the nonce always increments, preventing 'Nonce is too small' errors.
    """
    with patch("time.time") as mock_time:
        # Start with a realistic timestamp and increment it on each call
        mock_time.side_effect = (
            i for i in range(int(1700000000), int(1700000000) + 1000)
        )

        # Provide dummy credentials as they are required by the constructor
        service = ExchangeService(
            exchange_id="bitfinex", api_key="test_key", api_secret="test_secret"
        )
        yield service


@pytest.fixture(scope="session")
def mock_services():
    """
    Mock alla tjänster en gång per session för snabbare testning.
    """
    with patch("backend.services.websocket_market_service.get_websocket_client") as mock_ws_market, \
         patch("backend.services.websocket_user_data_service.get_websocket_user_data_service") as mock_ws_user, \
         patch("backend.services.bot_manager_async.get_bot_manager_async") as mock_bot_manager, \
         patch("backend.services.global_nonce_manager.get_global_nonce_manager") as mock_nonce_manager:
        
        # Konfigurera mock-returnerade värden
        mock_ws_market.return_value = None
        mock_ws_user.return_value = None
        mock_bot_manager.return_value = None
        mock_nonce_manager.return_value = None
        
        yield {
            "ws_market": mock_ws_market,
            "ws_user": mock_ws_user,
            "bot_manager": mock_bot_manager,
            "nonce_manager": mock_nonce_manager
        }
