"""
Bot control API endpoints for FastAPI.
"""

from fastapi import APIRouter, HTTPException, status
from backend.api.models import BotStatusResponse
from backend.services.bot_manager_async import get_bot_manager_async
from typing import Dict, Any

router = APIRouter(
    prefix="/api",
    tags=["bot-control"],
)

# GET /api/bot-status
@router.get("/bot-status", response_model=BotStatusResponse)
async def get_bot_status() -> Dict[str, Any]:
    """Get current bot status."""
    try:
        bot_manager = await get_bot_manager_async()
        status_result = await bot_manager.get_status()
        return status_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bot status: {str(e)}")

# POST /api/bot/start
@router.post("/bot/start")
async def start_bot() -> Dict[str, Any]:
    """Start the trading bot."""
    try:
        bot_manager = await get_bot_manager_async()
        result = await bot_manager.start_bot()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")

# POST /api/bot/stop
@router.post("/bot/stop")
async def stop_bot() -> Dict[str, Any]:
    """Stop the trading bot."""
    try:
        bot_manager = await get_bot_manager_async()
        result = await bot_manager.stop_bot()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}") 