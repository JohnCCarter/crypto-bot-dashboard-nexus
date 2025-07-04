"""
Minimal WebSocket test utan beroenden för att isolera problemet
"""

import pytest


@pytest.mark.asyncio
async def test_minimal_websocket():
    """
    Ett minimalt test som använder asyncio men inget WebSocket.
    Detta testar om problemet är relaterat till asyncio eller WebSocket-specifikt.
    """
    # Bara ett enkelt asynkront test utan WebSocket-beroenden
    assert True 