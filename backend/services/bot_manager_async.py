"""
Bot manager service - async version.

This module provides an asynchronous implementation of the bot manager service.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from backend.persistence.utils import load_bot_state, save_bot_state
from backend.services.main_bot_async import main_async

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
    """Asynchronous bot manager service with enhanced features."""

    def __init__(self, dev_mode: bool = False):
        """
        Initialize the bot manager with enhanced features.

        Args:
            dev_mode: Whether to run in development mode with reduced functionality
        """
        self.bot_state = AsyncBotState()
        self.operation_lock = asyncio.Lock()
        self.cycle_interval = 300  # 5 minutes between cycles
        self.dev_mode = dev_mode
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        self.performance_metrics = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "average_cycle_time": 0.0,
            "last_cycle_duration": 0.0,
        }

        if self.dev_mode:
            logger.info("BotManagerAsync initialized in DEVELOPMENT mode")
            # Shorter cycle interval in dev mode
            self.cycle_interval = 60
            self.retry_delay = 10  # Shorter retry delay in dev mode

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

            mode_info = " (DEVELOPMENT MODE)" if self.dev_mode else ""
            logger.info(
                f"Trading bot started successfully with async implementation{mode_info}"
            )
            return {
                "success": True,
                "message": f"Bot started with trading logic{mode_info}",
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

    async def graceful_shutdown(self, timeout: float = 30.0) -> Dict[str, Any]:
        """
        Perform a graceful shutdown of the bot with timeout.

        Args:
            timeout: Maximum time to wait for graceful shutdown in seconds

        Returns:
        --------
        Dict[str, Any]: Result of the shutdown operation
        """
        if not await self.bot_state.is_running():
            return {
                "success": True,
                "message": "Bot is not running",
                "status": "stopped",
            }

        logger.info(f"Starting graceful shutdown with {timeout}s timeout...")

        try:
            # Mark as stopping to prevent new operations
            await self.bot_state.set_running(False)

            # Get current task and wait for it to finish
            current_state = await self.bot_state.get_state()
            task = current_state.get("task")

            if task and not task.done():
                logger.info("Waiting for bot task to finish gracefully...")
                try:
                    await asyncio.wait_for(task, timeout=timeout)
                    logger.info("Bot task finished gracefully")
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Bot task did not finish within {timeout}s, cancelling..."
                    )
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.error("Bot task could not be cancelled gracefully")
                    except asyncio.CancelledError:
                        logger.info("Bot task cancelled successfully")

            await self.bot_state.set_task(None)
            logger.info("Graceful shutdown completed successfully")

            return {
                "success": True,
                "message": "Graceful shutdown completed",
                "status": "stopped",
            }

        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
            return {
                "success": False,
                "message": f"Error during graceful shutdown: {str(e)}",
                "status": "error",
            }

    async def reset_metrics(self) -> Dict[str, Any]:
        """
        Reset performance metrics.

        Returns:
        --------
        Dict[str, Any]: Result of the reset operation
        """
        try:
            self.performance_metrics = {
                "total_cycles": 0,
                "successful_cycles": 0,
                "failed_cycles": 0,
                "average_cycle_time": 0.0,
                "last_cycle_duration": 0.0,
            }
            logger.info("Performance metrics reset successfully")
            return {
                "success": True,
                "message": "Performance metrics reset successfully",
                "status": "reset",
            }
        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")
            return {
                "success": False,
                "message": f"Error resetting metrics: {str(e)}",
                "status": "error",
            }

    async def emergency_stop(self) -> Dict[str, Any]:
        """
        Emergency stop the bot immediately.

        Immediately stops the bot and cancels all pending operations.
        This is a safety feature for emergency situations.

        Returns:
        --------
        Dict[str, Any]: Result of the emergency stop operation
        """
        try:
            # Force stop without graceful shutdown
            await self.bot_state.set_running(False)

            # Cancel current task if running
            current_state = await self.bot_state.get_state()
            current_task = current_state.get("task")
            if current_task and not current_task.done():
                current_task.cancel()
                try:
                    await current_task
                except asyncio.CancelledError:
                    pass

            await self.bot_state.set_task(None)

            logger.warning("Bot emergency stopped")
            return {
                "success": True,
                "message": "Bot emergency stopped successfully",
                "status": "emergency_stopped",
            }
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            return {
                "success": False,
                "message": f"Error during emergency stop: {str(e)}",
                "status": "error",
            }

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive bot health information.

        Returns:
        --------
        Dict[str, Any]: Bot health information
        """
        try:
            current_state = await self.bot_state.get_state()
            running = current_state.get("running", False)

            # Calculate health metrics
            health_metrics = {
                "status": "healthy",
                "message": "Bot is operating normally",
                "running": running,
                "uptime": (
                    time.time() - current_state.get("start_time", time.time())
                    if running
                    else 0.0
                ),
                "last_cycle": current_state.get("last_update"),
                "performance": {
                    "total_cycles": self.performance_metrics["total_cycles"],
                    "success_rate": (
                        (
                            self.performance_metrics["successful_cycles"]
                            / self.performance_metrics["total_cycles"]
                        )
                        if self.performance_metrics["total_cycles"] > 0
                        else 0.0
                    ),
                    "average_cycle_time": self.performance_metrics[
                        "average_cycle_time"
                    ],
                },
                "warnings": [],
                "errors": [],
            }

            # Check for potential issues
            if running and self.performance_metrics["total_cycles"] > 0:
                success_rate = health_metrics["performance"]["success_rate"]
                if success_rate < 0.8:
                    health_metrics["status"] = "warning"
                    health_metrics["message"] = f"Low success rate: {success_rate:.2%}"
                    health_metrics["warnings"].append(
                        f"Success rate below 80%: {success_rate:.2%}"
                    )

                if self.performance_metrics["average_cycle_time"] > 300:  # 5 minutes
                    health_metrics["status"] = "warning"
                    health_metrics["message"] = "Slow cycle times detected"
                    health_metrics["warnings"].append(
                        "Average cycle time exceeds 5 minutes"
                    )

            # Check for errors
            if self.performance_metrics["errors"] > 0:
                health_metrics["status"] = "warning"
                health_metrics["message"] = (
                    f"Bot has encountered {self.performance_metrics['errors']} errors"
                )
                health_metrics["errors"].append(
                    f"Total errors: {self.performance_metrics['errors']}"
                )

            return health_metrics

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "error",
                "message": f"Error getting health status: {str(e)}",
                "running": False,
                "uptime": 0.0,
                "performance": {},
                "warnings": [],
                "errors": [str(e)],
            }

    async def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate bot configuration.

        Returns:
        --------
        Dict[str, Any]: Configuration validation results
        """
        try:
            validation_results = {
                "status": "valid",
                "message": "Configuration is valid",
                "checks": [],
                "warnings": [],
                "errors": [],
            }

            # Check if we can import required modules
            try:
                from backend.services.config_service import ConfigService

                config_service = ConfigService()
                validation_results["checks"].append("Config service: OK")
            except Exception as e:
                validation_results["status"] = "error"
                validation_results["errors"].append(f"Config service: {str(e)}")

            # Check if we can import trading services
            try:
                from backend.services.order_service_async import get_order_service_async
                from backend.services.risk_manager_async import get_risk_manager_async

                validation_results["checks"].append("Trading services: OK")
            except Exception as e:
                validation_results["status"] = "error"
                validation_results["errors"].append(f"Trading services: {str(e)}")

            # Check if we can import strategies
            try:
                from backend.strategies.ema_crossover_strategy import (
                    run_strategy as ema_strategy,
                )
                from backend.strategies.fvg_strategy import run_strategy as fvg_strategy
                from backend.strategies.rsi_strategy import run_strategy as rsi_strategy

                validation_results["checks"].append("Strategies: OK")
            except Exception as e:
                validation_results["status"] = "warning"
                validation_results["warnings"].append(f"Strategies: {str(e)}")

            # Update message based on results
            if validation_results["errors"]:
                validation_results["message"] = (
                    f"Configuration has {len(validation_results['errors'])} errors"
                )
            elif validation_results["warnings"]:
                validation_results["message"] = (
                    f"Configuration has {len(validation_results['warnings'])} warnings"
                )

            return validation_results

        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            return {
                "status": "error",
                "message": f"Error validating configuration: {str(e)}",
                "checks": [],
                "warnings": [],
                "errors": [str(e)],
            }

    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the trading bot with enhanced metrics.

        Returns:
        --------
        Dict[str, Any]: Bot status information with performance metrics
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

        # Calculate success rate
        total_cycles = self.performance_metrics["total_cycles"]
        successful_cycles = self.performance_metrics["successful_cycles"]
        success_rate = (
            (successful_cycles / total_cycles * 100) if total_cycles > 0 else 0.0
        )

        status_info = {
            "status": "running" if running else "stopped",
            "uptime": uptime,
            "last_update": current_state.get("last_update"),
            "thread_alive": task_alive,  # Keep name for compatibility
            "cycle_count": current_state.get("cycle_count", 0),
            "last_cycle_time": current_state.get("last_cycle_time"),
            "dev_mode": self.dev_mode,
            "performance": {
                "total_cycles": total_cycles,
                "successful_cycles": successful_cycles,
                "failed_cycles": self.performance_metrics["failed_cycles"],
                "success_rate": round(success_rate, 2),
                "average_cycle_time": round(
                    self.performance_metrics["average_cycle_time"], 2
                ),
                "last_cycle_duration": round(
                    self.performance_metrics["last_cycle_duration"], 2
                ),
            },
            "configuration": {
                "cycle_interval": self.cycle_interval,
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay,
            },
        }

        # Include error if any
        if current_state.get("error"):
            status_info["error"] = current_state["error"]

        return status_info

    async def _bot_worker(self) -> None:
        """Enhanced worker coroutine that runs the main bot logic with retry logic and performance tracking."""
        try:
            # Fix PYTHONPATH for correct imports
            current_file = os.path.abspath(__file__)
            parent_dir = os.path.dirname(current_file)
            backend_dir = os.path.dirname(parent_dir)
            workspace_root = os.path.dirname(backend_dir)
            if workspace_root not in sys.path:
                sys.path.insert(0, workspace_root)

            consecutive_failures = 0

            while await self.bot_state.is_running():
                cycle_start_time = time.time()
                cycle_success = False

                try:
                    if self.dev_mode:
                        # In dev mode, just simulate a cycle without calling main_async
                        logger.info(
                            "DEV MODE: Simulating bot cycle without executing trading logic"
                        )
                        await asyncio.sleep(2)  # Short sleep to simulate work
                        cycle_success = True
                    else:
                        # Run one trading cycle using the asynchronous main_async function
                        await main_async()
                        cycle_success = True

                    # Update performance metrics
                    cycle_duration = time.time() - cycle_start_time
                    self.performance_metrics["total_cycles"] += 1
                    self.performance_metrics["last_cycle_duration"] = cycle_duration

                    if cycle_success:
                        self.performance_metrics["successful_cycles"] += 1
                        consecutive_failures = 0  # Reset failure counter

                        # Update average cycle time
                        total_cycles = self.performance_metrics["total_cycles"]
                        current_avg = self.performance_metrics["average_cycle_time"]
                        self.performance_metrics["average_cycle_time"] = (
                            current_avg * (total_cycles - 1) + cycle_duration
                        ) / total_cycles

                    await self.bot_state.increment_cycle()
                    cycle_count = (await self.bot_state.get_state())["cycle_count"]

                    if cycle_success:
                        logger.info(
                            f"Bot cycle completed successfully. Total cycles: {cycle_count}, Duration: {cycle_duration:.2f}s"
                        )
                    else:
                        logger.warning(
                            f"Bot cycle failed. Total cycles: {cycle_count}, Duration: {cycle_duration:.2f}s"
                        )

                except Exception as cycle_error:
                    cycle_duration = time.time() - cycle_start_time
                    consecutive_failures += 1
                    self.performance_metrics["total_cycles"] += 1
                    self.performance_metrics["failed_cycles"] += 1
                    self.performance_metrics["last_cycle_duration"] = cycle_duration

                    logger.error(
                        f"Error in bot cycle (attempt {consecutive_failures}/{self.max_retries}): {cycle_error}"
                    )

                    # Check if we should stop due to too many consecutive failures
                    if consecutive_failures >= self.max_retries:
                        error_msg = f"Bot stopped due to {consecutive_failures} consecutive failures"
                        logger.error(error_msg)
                        await self.bot_state.set_error(error_msg)
                        break

                    # Wait before retry
                    logger.info(f"Waiting {self.retry_delay} seconds before retry...")
                    await asyncio.sleep(self.retry_delay)
                    continue

                # Check if still should run
                if await self.bot_state.is_running():
                    # Wait between cycles - shorter in dev mode
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


async def get_bot_manager_async(dev_mode: bool = False) -> BotManagerAsync:
    """
    Get or create a BotManagerAsync instance.

    Args:
        dev_mode: Whether to run in development mode with reduced functionality

    Returns:
    --------
    BotManagerAsync: The bot manager instance
    """
    global _bot_manager_instance

    if _bot_manager_instance is None:
        async with _init_lock:
            if _bot_manager_instance is None:
                _bot_manager_instance = BotManagerAsync(dev_mode=dev_mode)
    elif _bot_manager_instance.dev_mode != dev_mode:
        # If dev_mode changed, create a new instance
        async with _init_lock:
            _bot_manager_instance = BotManagerAsync(dev_mode=dev_mode)

    return _bot_manager_instance
