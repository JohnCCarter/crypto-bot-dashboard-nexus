"""
Bot manager service - async version.

This module provides an asynchronous implementation of the bot manager service.
"""

import logging
import os
import sys
import asyncio
import time
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from backend.persistence.utils import load_bot_state, save_bot_state
from backend.services.main_bot import main

logger = logging.getLogger(__name__)


class AsyncBotState:
    """Asynchronous bot state manager using asyncio locks for concurrent access."""

    def __init__(self):
        self._lock = asyncio.Lock()  # Asyncio lock for async context
        self._state = {
            "running": False,
            "start_time": None,
            "last_update": None,
            "task": None,  # asyncio.Task instead of thread
            "error": None,
            "cycle_count": 0,
            "last_cycle_time": None,
        }
        # Load persisted state if available
        if persisted := load_bot_state():
            self._state.update(persisted)

    async def get_state(self) -> Dict[str, Any]:
        """Get current state safely."""
        async with self._lock:
            return self._state.copy()

    async def set_running(self, running: bool) -> None:
        """Set running state safely."""
        async with self._lock:
            self._state["running"] = running
            self._state["last_update"] = datetime.now(UTC).isoformat()
            if running:
                self._state["start_time"] = time.time()
                self._state["error"] = None
            else:
                self._state["start_time"] = None
        await self._persist()

    async def set_task(self, task: Optional[asyncio.Task]) -> None:
        """Set task reference safely."""
        async with self._lock:
            self._state["task"] = task
        await self._persist()

    async def set_error(self, error: Optional[str]) -> None:
        """Set error state safely."""
        async with self._lock:
            self._state["error"] = error
            self._state["last_update"] = datetime.now(UTC).isoformat()
            if error:
                self._state["running"] = False
        await self._persist()

    async def increment_cycle(self) -> None:
        """Increment cycle counter safely."""
        async with self._lock:
            self._state["cycle_count"] += 1
            self._state["last_cycle_time"] = datetime.now(UTC).isoformat()
            self._state["last_update"] = datetime.now(UTC).isoformat()
        await self._persist()

    async def is_running(self) -> bool:
        """Check if bot is running safely."""
        async with self._lock:
            return self._state["running"]

    async def _persist(self):
        """Persist current state asynchronously."""
        try:
            # Create a copy of state that's safe to serialize
            state_to_save = self._state.copy()
            # Remove the task reference as it's not serializable
            state_to_save.pop("task", None)
            save_bot_state(state_to_save)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Failed to persist bot state: {exc}")


class BotManagerAsync:
    """Asynchronous bot manager service."""

    def __init__(self):
        """Initialize the bot manager."""
        self.bot_state = AsyncBotState()
        self.operation_lock = asyncio.Lock()
        self.cycle_interval = 300  # 5 minutes between cycles

    async def start_bot(self) -> Dict[str, Any]:
        """
        Start the trading bot with actual trading logic.
        
        Returns:
        --------
        Dict[str, Any]: Result of the start operation
        """
        async with self.operation_lock:
            if await self.bot_state.is_running():
                logger.warning("Bot is already running")
                return {
                    "success": False,
                    "message": "Bot is already running",
                    "status": "running",
                }

        try:
            # Create a task for the bot worker
            bot_task = asyncio.create_task(self._bot_worker())
            
            # Update state
            await self.bot_state.set_running(True)
            await self.bot_state.set_task(bot_task)
            
            logger.info("Trading bot started successfully with async implementation")
            return {
                "success": True,
                "message": "Bot started with trading logic",
                "status": "running",
            }
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            await self.bot_state.set_error(str(e))
            return {
                "success": False,
                "message": f"Failed to start bot: {str(e)}",
                "status": "error",
            }

    async def stop_bot(self) -> Dict[str, Any]:
        """
        Stop the trading bot.
        
        Returns:
        --------
        Dict[str, Any]: Result of the stop operation
        """
        async with self.operation_lock:
            if not await self.bot_state.is_running():
                logger.warning("Bot is not running")
                return {
                    "success": False,
                    "message": "Bot is not running",
                    "status": "stopped",
                }
        
        # Safely stop the bot
        await self.bot_state.set_running(False)
        
        # Get current task and cancel it if running
        current_state = await self.bot_state.get_state()
        task = current_state.get("task")
        if task and not task.done():
            logger.info("Cancelling bot task...")
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Bot task did not finish within timeout")
            except asyncio.CancelledError:
                logger.info("Bot task cancelled successfully")
        
        await self.bot_state.set_task(None)
        logger.info("Trading bot stopped successfully")
        return {
            "success": True,
            "message": "Bot stopped successfully",
            "status": "stopped",
        }

    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the trading bot.
        
        Returns:
        --------
        Dict[str, Any]: Bot status information
        """
        now = time.time()
        current_state = await self.bot_state.get_state()
        
        running = current_state.get("running", False)
        if running and current_state.get("start_time") is not None:
            uptime = now - current_state["start_time"]
        else:
            uptime = 0.0
        
        # Check if task is actually running
        task = current_state.get("task")
        task_alive = bool(task and not task.done())
        
        status_info = {
            "status": "running" if running else "stopped",
            "uptime": uptime,
            "last_update": current_state.get("last_update"),
            "thread_alive": task_alive,  # Keep name for compatibility
            "cycle_count": current_state.get("cycle_count", 0),
            "last_cycle_time": current_state.get("last_cycle_time"),
        }
        
        # Include error if any
        if current_state.get("error"):
            status_info["error"] = current_state["error"]
        
        return status_info

    async def _bot_worker(self) -> None:
        """Worker coroutine that runs the main bot logic."""
        try:
            # Fix PYTHONPATH for correct imports
            current_file = os.path.abspath(__file__)
            parent_dir = os.path.dirname(current_file)
            backend_dir = os.path.dirname(parent_dir)
            workspace_root = os.path.dirname(backend_dir)
            if workspace_root not in sys.path:
                sys.path.insert(0, workspace_root)
            
            while await self.bot_state.is_running():
                try:
                    # Run one trading cycle
                    # Note: main() is still synchronous, we'll need to adapt it later
                    # For now, we run it in an executor to avoid blocking
                    await asyncio.to_thread(main)
                    
                    await self.bot_state.increment_cycle()
                    cycle_count = (await self.bot_state.get_state())['cycle_count']
                    logger.info(f"Bot cycle completed. Total cycles: {cycle_count}")
                except Exception as cycle_error:
                    logger.error(f"Error in bot cycle: {cycle_error}")
                    await self.bot_state.set_error(str(cycle_error))
                    break
                
                # Check if still should run
                if await self.bot_state.is_running():
                    # Wait between cycles
                    await asyncio.sleep(self.cycle_interval)
        
        except asyncio.CancelledError:
            logger.info("Bot worker task was cancelled")
            raise
        except Exception as e:
            logger.error(f"Critical error in bot worker: {e}")
            await self.bot_state.set_error(str(e))


# Global bot manager instance
_bot_manager_instance = None
_init_lock = asyncio.Lock()


async def get_bot_manager_async() -> BotManagerAsync:
    """
    Get or create a BotManagerAsync instance.
    
    Returns:
    --------
    BotManagerAsync: The bot manager instance
    """
    global _bot_manager_instance
    
    if _bot_manager_instance is None:
        async with _init_lock:
            if _bot_manager_instance is None:
                _bot_manager_instance = BotManagerAsync()
    
    return _bot_manager_instance 