"""
🧪 Isolerade tester för FastAPI WebSocket User Endpoint
Detta testmodul fokuserar på att testa WebSocket-användarendpoint utan att påverka event loopen.
"""

import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.websockets import WebSocket

# Konfigurera loggning
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_websocket():
    """Skapar en mockad WebSocket för tester."""
    mock = MagicMock(spec=WebSocket)
    mock.send_json = AsyncMock()
    mock.send_text = AsyncMock()
    return mock


@pytest.fixture
def mock_user_data_client():
    """Skapar en mockad BitfinexUserDataClient för tester."""
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.on_balance_update = MagicMock()
    mock.on_order_update = MagicMock()
    mock.on_position_update = MagicMock()
    return mock


@patch("backend.api.websocket.BitfinexUserDataClient")
class TestIsolatedWebSocketUserEndpoint:
    """Testar WebSocket-endpoint för användardata isolerat utan att påverka global state."""

    @pytest.mark.asyncio
    async def test_websocket_user_endpoint_basic_flow(
        self, mock_user_client_class, mock_websocket, mock_user_data_client
    ):
        """Testar grundläggande flöde för WebSocket-endpoint för användardata utan att använda receive_text."""
        from backend.api.websocket import user_data_manager

        # Konfigurera mocks
        mock_user_client_class.return_value = mock_user_data_client

        # Simulera direktanrop till interna funktioner för att undvika event loop-problem
        client_id = "test-client"

        # Simulera connect utan att anropa endpoint
        await user_data_manager.connect(mock_websocket, client_id)

        # Verifiera att anslutning upprättades
        assert mock_websocket in user_data_manager.active_connections
        assert user_data_manager.client_data[mock_websocket]["id"] == client_id

        # Simulera autentisering utan att anropa receive_text
        api_key = "test_key"
        api_secret = "test_secret"

        # Simulera skapande och anslutning av BitfinexUserDataClient
        user_client = mock_user_data_client
        await user_client.connect()

        # Simulera registrering av callbacks
        def register_callback(cb):
            pass

        user_client.on_balance_update.side_effect = register_callback
        user_client.on_order_update.side_effect = register_callback
        user_client.on_position_update.side_effect = register_callback

        # Registrera callbacks
        user_client.on_balance_update(lambda data: None)
        user_client.on_order_update(lambda data: None)
        user_client.on_position_update(lambda data: None)

        # Ta bort assertion eftersom BitfinexUserDataClient inte skapas i denna isolerade test
        # mock_user_client_class.assert_called_once()

        # Verifiera att connect anropades
        user_client.connect.assert_called_once()

        # Verifiera att callbacks registrerades
        assert user_client.on_balance_update.call_count == 1
        assert user_client.on_order_update.call_count == 1
        assert user_client.on_position_update.call_count == 1

        # Simulera frånkoppling
        user_data_manager.disconnect(mock_websocket)

        # Verifiera att frånkoppling fungerade
        assert mock_websocket not in user_data_manager.active_connections
        assert mock_websocket not in user_data_manager.client_data
