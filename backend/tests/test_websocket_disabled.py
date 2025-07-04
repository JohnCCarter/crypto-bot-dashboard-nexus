"""
Test av WebSocket-funktionalitet med inaktiverade faktiska anslutningar.
Detta test använder miljövariabler för att inaktivera anslutningar och undvika terminalinteraktionsproblem.
"""

import os
import pytest
import logging
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi.websockets import WebSocket
from fastapi.testclient import TestClient

from backend.api.websocket import ConnectionManager
from backend.fastapi_app import app

# Konfigurera loggning med minimal nivå
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def disable_websocket_connections():
    """
    Inaktivera alla WebSocket-anslutningar genom att sätta miljövariabler.
    Denna fixture körs automatiskt före varje test.
    """
    # Spara gamla värden
    old_disable_websockets = os.environ.get("FASTAPI_DISABLE_WEBSOCKETS")
    old_disable_gnm = os.environ.get("FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER")
    
    # Sätt miljövariabler som inaktiverar WebSocket-funktionalitet
    os.environ["FASTAPI_DISABLE_WEBSOCKETS"] = "true"
    os.environ["FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER"] = "true"
    
    yield
    
    # Återställ gamla värden
    if old_disable_websockets:
        os.environ["FASTAPI_DISABLE_WEBSOCKETS"] = old_disable_websockets
    else:
        os.environ.pop("FASTAPI_DISABLE_WEBSOCKETS", None)
        
    if old_disable_gnm:
        os.environ["FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER"] = old_disable_gnm
    else:
        os.environ.pop("FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER", None)


@pytest.fixture
def mock_websocket():
    """Skapar en mockad WebSocket för tester."""
    mock = MagicMock(spec=WebSocket)
    mock.send_json = AsyncMock()
    mock.send_text = AsyncMock()
    mock.receive_text = AsyncMock()
    return mock


@pytest.fixture
def test_client():
    """TestClient för FastAPI app med WebSocket inaktiverad."""
    return TestClient(app)


class TestWebSocketDisabled:
    """Tester för WebSocket med inaktiverade anslutningar."""
    
    @pytest.mark.asyncio
    async def test_connection_manager_basic(self, mock_websocket):
        """Testar grundläggande ConnectionManager-funktionalitet."""
        manager = ConnectionManager("test")
        
        # Testa connect
        await manager.connect(mock_websocket, "test-client")
        assert mock_websocket in manager.active_connections
        assert manager.client_data[mock_websocket]["id"] == "test-client"
        
        # Testa add_subscription
        manager.add_subscription(mock_websocket, "test_subscription")
        assert "test_subscription" in manager.get_subscriptions(mock_websocket)
        
        # Testa remove_subscription
        manager.remove_subscription(mock_websocket, "test_subscription")
        assert "test_subscription" not in manager.get_subscriptions(mock_websocket)
        
        # Testa send_personal_message
        await manager.send_personal_message("test message", mock_websocket)
        mock_websocket.send_text.assert_called_once_with("test message")
        
        # Testa broadcast
        mock_websocket.send_text.reset_mock()
        await manager.broadcast("broadcast message")
        mock_websocket.send_text.assert_called_once_with("broadcast message")
        
        # Testa disconnect
        manager.disconnect(mock_websocket)
        assert mock_websocket not in manager.active_connections
        assert mock_websocket not in manager.client_data
    
    def test_websocket_routes_disabled(self, test_client):
        """Verifierar att WebSocket-routen inte är registrerad när WebSocket är inaktiverat."""
        # Hämta alla routes i appen
        routes = [route for route in app.routes]
        
        # Verifiera att WebSocket-routes inte är registrerade när de är inaktiverade
        ws_routes = [route for route in routes if route.path.startswith("/ws")]
        assert len(ws_routes) == 0, "WebSocket-routes bör vara inaktiverade" 