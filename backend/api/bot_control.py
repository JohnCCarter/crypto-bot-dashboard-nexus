"""
Bot control API endpoints.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import BotManagerDependency, get_bot_manager
from backend.api.models import BotActionResponse, BotStatusResponse
from backend.services.event_logger import (
    EventType,
    event_logger,
    should_suppress_routine_log,
)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["bot-control"],
)

# Configure logging
logger = logging.getLogger(__name__)


@router.get("/bot-status", response_model=BotStatusResponse)
async def get_bot_status_route(
    bot_manager: BotManagerDependency = Depends(get_bot_manager),
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

        # Logga alltid dev_mode-information för debug
        dev_mode = bot_manager.dev_mode
        if dev_mode:
            logger.debug(
                f"Bot status retrieved in DEV MODE: {bot_status.get('status', 'unknown')}"
            )

        # Endast logga om det INTE är routine polling
        if not should_suppress_routine_log("/api/bot-status", "GET"):
            event_logger.log_event(
                EventType.API_ERROR,  # Korrekt event-typ från EventType enum
                f"Bot status retrieved: {bot_status.get('status', 'unknown')}",
            )

        return bot_status

    except Exception as e:
        # Fel ska alltid loggas
        event_logger.log_api_error("/api/bot-status", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot status: {str(e)}",
        )


@router.post("/bot/start", response_model=BotActionResponse)
async def start_bot_route(bot_manager: BotManagerDependency = Depends(get_bot_manager)):
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
            EventType.BOT_STARTED if result["success"] else EventType.API_ERROR,
            f"Bot start attempt: {result['message']}",
        )

        if not result["success"]:
            if result["status"] == "running":
                # Bot already running is not an error
                return result
            else:
                # Failed to start bot for other reasons
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["message"],
                )

        return result

    except HTTPException:
        raise
    except Exception as e:
        # Logga alla andra fel
        event_logger.log_api_error("/api/bot/start", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bot: {str(e)}",
        )


@router.post("/bot/stop", response_model=BotActionResponse)
async def stop_bot_route(bot_manager: BotManagerDependency = Depends(get_bot_manager)):
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
            EventType.BOT_STOPPED if result["success"] else EventType.API_ERROR,
            f"Bot stop attempt: {result['message']}",
        )

        if not result["success"]:
            if result["status"] == "stopped":
                # Bot already stopped is not an error
                return result
            else:
                # Failed to stop bot for other reasons
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["message"],
                )

        return result

    except HTTPException:
        raise
    except Exception as e:
        # Logga alla andra fel
        event_logger.log_api_error("/api/bot/stop", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop bot: {str(e)}",
        )


@router.post("/bot/shutdown", response_model=BotActionResponse)
async def graceful_shutdown_route(
    bot_manager: BotManagerDependency = Depends(get_bot_manager),
):
    """
    Perform graceful shutdown of the trading bot.

    Performs a graceful shutdown with timeout, allowing the bot to finish
    current operations before stopping.

    Returns:
    --------
    BotActionResponse: Result of the shutdown operation
    """
    try:
        result = await bot_manager.graceful_shutdown()

        # Logga alltid shutdown-försök
        event_logger.log_event(
            EventType.BOT_STOPPED if result["success"] else EventType.API_ERROR,
            f"Bot graceful shutdown attempt: {result['message']}",
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        # Logga alla andra fel
        event_logger.log_api_error("/api/bot/shutdown", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to shutdown bot: {str(e)}",
        )


@router.post("/bot/reset-metrics", response_model=BotActionResponse)
async def reset_metrics_route(
    bot_manager: BotManagerDependency = Depends(get_bot_manager),
):
    """
    Reset performance metrics for the trading bot.

    Resets all performance metrics including cycle counts, success rates,
    and timing information.

    Returns:
    --------
    BotActionResponse: Result of the reset operation
    """
    try:
        result = await bot_manager.reset_metrics()

        # Logga metrics reset
        event_logger.log_event(
            EventType.API_ERROR,  # Use API_ERROR for now since API_SUCCESS doesn't exist
            f"Bot metrics reset: {result['message']}",
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        # Logga alla andra fel
        event_logger.log_api_error("/api/bot/reset-metrics", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset metrics: {str(e)}",
        )


@router.post("/bot/emergency-stop", response_model=BotActionResponse)
async def emergency_stop_route(
    bot_manager: BotManagerDependency = Depends(get_bot_manager),
):
    """
    Emergency stop the trading bot.

    Immediately stops the bot and cancels all pending operations.
    This is a safety feature for emergency situations.

    Returns:
    --------
    BotActionResponse: Result of the emergency stop operation
    """
    try:
        result = await bot_manager.emergency_stop()

        # Logga alltid emergency stop-försök
        event_logger.log_event(
            EventType.BOT_STOPPED if result["success"] else EventType.API_ERROR,
            f"Bot emergency stop attempt: {result['message']}",
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        # Logga alla andra fel
        event_logger.log_api_error("/api/bot/emergency-stop", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to emergency stop bot: {str(e)}",
        )


@router.get("/bot/health", response_model=Dict[str, Any])
async def get_bot_health_route(
    bot_manager: BotManagerDependency = Depends(get_bot_manager),
):
    """
    Get comprehensive bot health information.

    Returns detailed health metrics including system status,
    performance indicators, and potential issues.

    Returns:
    --------
    Dict[str, Any]: Bot health information
    """
    try:
        health_info = await bot_manager.get_health_status()

        # Logga health check endast vid varningar eller fel
        if health_info.get("status") != "healthy":
            event_logger.log_event(
                EventType.API_ERROR,
                f"Bot health check: {health_info.get('status', 'unknown')} - {health_info.get('message', 'No message')}",
            )

        return health_info

    except Exception as e:
        # Logga alla fel
        event_logger.log_api_error("/api/bot/health", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot health: {str(e)}",
        )


@router.post("/bot/validate-config", response_model=Dict[str, Any])
async def validate_bot_config_route(
    bot_manager: BotManagerDependency = Depends(get_bot_manager),
):
    """
    Validate bot configuration.

    Performs comprehensive validation of bot configuration
    including strategy parameters, risk settings, and API credentials.

    Returns:
    --------
    Dict[str, Any]: Configuration validation results
    """
    try:
        validation_result = await bot_manager.validate_configuration()

        # Logga validation resultat
        event_logger.log_event(
            EventType.API_ERROR,  # Use API_ERROR for now
            f"Bot config validation: {validation_result.get('status', 'unknown')}",
        )

        return validation_result

    except Exception as e:
        # Logga alla fel
        event_logger.log_api_error("/api/bot/validate-config", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate bot configuration: {str(e)}",
        )
