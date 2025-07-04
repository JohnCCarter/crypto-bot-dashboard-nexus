"""
Bot control API endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from backend.api.models import BotStatusResponse, BotActionResponse
from backend.api.dependencies import get_bot_manager, BotManagerDependency
from backend.services.event_logger import (
    event_logger, should_suppress_routine_log, EventType
)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["bot-control"],
)


@router.get("/bot-status", response_model=BotStatusResponse)
async def get_bot_status_route(
    bot_manager: BotManagerDependency = Depends(get_bot_manager)
):
    """
    Get current bot status.
    
    Returns information about the trading bot's current state, 
    including running status, uptime, and cycle information.
    
    Returns:
    --------
    BotStatusResponse: Current bot status
    """
    try:
        bot_status = await bot_manager.get_status()
        
        # Endast logga om det INTE är routine polling
        if not should_suppress_routine_log("/api/bot-status", "GET"):
            event_logger.log_event(
                EventType.API_ERROR,  # Using available type
                f"Bot status retrieved: {bot_status.get('status', 'unknown')}"
            )

        return bot_status
        
    except Exception as e:
        # Fel ska alltid loggas
        event_logger.log_api_error("/api/bot-status", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot status: {str(e)}"
        )


@router.post("/bot/start", response_model=BotActionResponse)
async def start_bot_route(
    bot_manager: BotManagerDependency = Depends(get_bot_manager)
):
    """
    Start the trading bot.
    
    Starts the trading bot if it is not already running.
    
    Returns:
    --------
    BotActionResponse: Result of the start operation
    """
    try:
        result = await bot_manager.start_bot()
        
        # Logga alltid start-försök, framgångsrika eller ej
        event_logger.log_event(
            EventType.BOT_STARTED if result['success'] else EventType.API_ERROR,
            f"Bot start attempt: {result['message']}"
        )
        
        if not result['success']:
            if result['status'] == 'running':
                # Bot already running is not an error
                return result
            else:
                # Failed to start bot for other reasons
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result['message']
                )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        # Logga alla andra fel
        event_logger.log_api_error("/api/bot/start", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bot: {str(e)}"
        )


@router.post("/bot/stop", response_model=BotActionResponse)
async def stop_bot_route(
    bot_manager: BotManagerDependency = Depends(get_bot_manager)
):
    """
    Stop the trading bot.
    
    Stops the trading bot if it is running.
    
    Returns:
    --------
    BotActionResponse: Result of the stop operation
    """
    try:
        result = await bot_manager.stop_bot()
        
        # Logga alltid stopp-försök
        event_logger.log_event(
            EventType.BOT_STOPPED if result['success'] else EventType.API_ERROR,
            f"Bot stop attempt: {result['message']}"
        )
        
        if not result['success']:
            if result['status'] == 'stopped':
                # Bot already stopped is not an error
                return result
            else:
                # Failed to stop bot for other reasons
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result['message']
                )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        # Logga alla andra fel
        event_logger.log_api_error("/api/bot/stop", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop bot: {str(e)}"
        ) 