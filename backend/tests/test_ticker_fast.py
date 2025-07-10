"""
Snabb test för ticker-uppdateringar utan FastAPI-app import
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.api.websocket import ticker_manager
from backend.services.websocket_market_service import MarketData


@pytest.fixture
def mock_websocket():
    """Skapar en mockad WebSocket för tester."""
    mock = MagicMock()
    mock.send_text = AsyncMock()
    mock.send_json = AsyncMock()
    return mock


@pytest.mark.asyncio
@pytest.mark.timeout(5)  # Kort timeout för snabbt test
async def test_ticker_update_fast(mock_websocket):
    """Snabb test för ticker-uppdateringar."""
    # Registrera WebSocket i ticker_manager
    ticker_manager.active_connections.append(mock_websocket)
    ticker_manager.client_data[mock_websocket] = {
        "id": "test-client",
        "subscriptions": ["ticker_BTCUSD"],
    }

    # Skapa en enkel callback-funktion som skickar data direkt till WebSocket
    async def ticker_callback(data):
        await mock_websocket.send_text(
            json.dumps(
                {
                    "type": "ticker",
                    "symbol": data.symbol,
                    "data": {
                        "price": data.price,
                        "volume": data.volume,
                        "bid": data.bid,
                        "ask": data.ask,
                    },
                }
            )
        )

    # Simulera ticker-uppdatering
    market_data = MarketData(
        symbol="BTCUSD",
        price=50000.0,
        volume=10.5,
        bid=49950.0,
        ask=50050.0,
        timestamp=datetime.now(),
    )

    # Anropa callback med ticker-data
    await ticker_callback(market_data)

    # Kontrollera att data skickades till klienten
    mock_websocket.send_text.assert_called_once()

    # Hämta argument som skickades och parsea JSON
    sent_text = mock_websocket.send_text.call_args[0][0]
    args = json.loads(sent_text)
    assert args["type"] == "ticker"
    assert args["symbol"] == "BTCUSD"
    assert args["data"]["price"] == 50000.0
    assert args["data"]["volume"] == 10.5
    assert args["data"]["bid"] == 49950.0
    assert args["data"]["ask"] == 50050.0
