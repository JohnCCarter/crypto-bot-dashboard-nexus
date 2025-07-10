"""
Minimal WebSocket mock test utan anrop för att isolera problemet
"""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.websockets import WebSocket

# Konfigurera loggning med minimal nivå
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_websocket():
    """Skapar en mockad WebSocket för tester."""
    mock = MagicMock(spec=WebSocket)
    mock.send_json = AsyncMock()
    mock.send_text = AsyncMock()
    mock.receive_text = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_minimal_websocket_mock(mock_websocket):
    """
    Ett minimalt test som skapar WebSocket-mockar men inte gör några anrop.
    Detta testar om problemet är relaterat till WebSocket-importerna eller anropen.
    """
    # Importera WebSocket-funktioner men anropa dem inte
    from backend.api.websocket import ConnectionManager

    # Skapa en connection manager men anropa den inte
    manager = ConnectionManager("test")

    # Gör ett grundläggande assert
    assert isinstance(manager, ConnectionManager)
    assert mock_websocket.send_json is not None
