import time
import threading
import sys
import os
from datetime import UTC, datetime
from typing import Optional, Dict, Any
import logging
from backend.persistence.utils import save_bot_state, load_bot_state  # NEW IMPORT

logger = logging.getLogger(__name__)


class ThreadSafeBotState:
    """Thread-safe bot state manager using locks for concurrent access."""

    def __init__(self):
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._state = {
            "running": False,
            "start_time": None,
            "last_update": None,
            "thread": None,
            "error": None,
            "cycle_count": 0,
            "last_cycle_time": None,
        }
        if persisted := load_bot_state():
            self._state |= persisted

    def get_state(self) -> Dict[str, Any]:
        """Get current state safely."""
        with self._lock:
            return self._state.copy()

    def set_running(self, running: bool) -> None:
        """Set running state safely."""
        with self._lock:
            self._state["running"] = running
            self._state["last_update"] = datetime.now(UTC).isoformat()
            if running:
                self._state["start_time"] = time.time()
                self._state["error"] = None
            else:
                self._state["start_time"] = None
        self._persist()

    def set_thread(self, thread: Optional[threading.Thread]) -> None:
        """Set thread reference safely."""
        with self._lock:
            self._state["thread"] = thread
        self._persist()

    def set_error(self, error: Optional[str]) -> None:
        """Set error state safely."""
        with self._lock:
            self._state["error"] = error
            self._state["last_update"] = datetime.now(UTC).isoformat()
            if error:
                self._state["running"] = False
        self._persist()

    def increment_cycle(self) -> None:
        """Increment cycle counter safely."""
        with self._lock:
            self._state["cycle_count"] += 1
            self._state["last_cycle_time"] = datetime.now(UTC).isoformat()
            self._state["last_update"] = datetime.now(UTC).isoformat()
        self._persist()

    def is_running(self) -> bool:
        """Check if bot is running safely."""
        with self._lock:
            return self._state["running"]

    def _persist(self):
        """Persist current state asynchronously (fire-and-forget)."""
        try:
            save_bot_state(self._state)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Failed to persist bot state: {exc}")


# Global thread-safe bot state instance
bot_state = ThreadSafeBotState()


def start_bot():
    """Startar tradingboten med faktisk trading logic."""
    if bot_state.is_running():
        return {
            "success": False,
            "message": "Bot is already running",
            "status": "running",
        }

    try:

        def bot_worker():
            """Worker function that runs the main bot logic with correct PYTHONPATH."""
            try:
                # Fix PYTHONPATH for threading context
                current_file = os.path.abspath(__file__)
                parent_dir = os.path.dirname(current_file)
                backend_dir = os.path.dirname(parent_dir)
                workspace_root = os.path.dirname(backend_dir)
                if workspace_root not in sys.path:
                    sys.path.insert(0, workspace_root)

                # Import here to avoid circular imports and ensure correct path
                from backend.services.main_bot import main

                while bot_state.is_running():
                    try:
                        main()  # Run one trading cycle
                        bot_state.increment_cycle()
                        logger.info(
                            f"Bot cycle completed. Total cycles: {bot_state.get_state()['cycle_count']}"
                        )
                    except Exception as cycle_error:
                        logger.error(f"Error in bot cycle: {cycle_error}")
                        bot_state.set_error(str(cycle_error))
                        break

                    if bot_state.is_running():  # Check if still should run
                        time.sleep(300)  # Wait 5 minutes between cycles

            except Exception as e:
                logger.error(f"Critical error in bot worker: {e}")
                bot_state.set_error(str(e))

        # Start bot in background thread
        bot_thread = threading.Thread(target=bot_worker, daemon=True)
        bot_thread.start()

        # Update state using thread-safe methods
        bot_state.set_running(True)
        bot_state.set_thread(bot_thread)

        logger.info("Trading bot started successfully with enhanced thread safety")
        return {
            "success": True,
            "message": "Bot started with trading logic",
            "status": "running",
        }

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        bot_state.set_error(str(e))
        return {
            "success": False,
            "message": f"Failed to start bot: {str(e)}",
            "status": "error",
        }


def stop_bot():
    """Stoppar tradingboten."""
    if not bot_state.is_running():
        return {"success": False, "message": "Bot is not running", "status": "stopped"}

    # Safely stop the bot
    bot_state.set_running(False)

    # Get current thread and wait for it to finish
    current_state = bot_state.get_state()
    if current_state["thread"] and current_state["thread"].is_alive():
        logger.info("Waiting for bot thread to finish...")
        current_state["thread"].join(timeout=5.0)
        if current_state["thread"].is_alive():
            logger.warning("Bot thread did not finish within timeout")

    bot_state.set_thread(None)
    logger.info("Trading bot stopped successfully")
    return {"success": True, "message": "Bot stopped successfully", "status": "stopped"}


def get_bot_status():
    """Returnerar nuvarande status för tradingboten, uptime och senaste uppdateringstid."""
    now = time.time()
    current_state = bot_state.get_state()

    running = current_state.get("running", False)
    if running and current_state.get("start_time") is not None:
        uptime = now - current_state["start_time"]
    else:
        uptime = 0.0

    # Check if thread is actually alive
    thread_alive = bool(current_state["thread"] and current_state["thread"].is_alive())

    status_info = {
        "status": "running" if running else "stopped",
        "uptime": uptime,
        "last_update": current_state.get("last_update"),
        "thread_alive": thread_alive,
        "cycle_count": current_state.get("cycle_count", 0),
        "last_cycle_time": current_state.get("last_cycle_time"),
    }

    # Include error if any
    if current_state.get("error"):
        status_info["error"] = current_state["error"]

    return status_info
