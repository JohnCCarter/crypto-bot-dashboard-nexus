import time
import threading
from datetime import UTC, datetime
from typing import Optional

# Shared status for the trading bot
bot_status = {
    "running": False,
    "start_time": None,
    "last_update": None,
    "thread": None,
    "error": None,
}


def start_bot():
    """Startar tradingboten med faktisk trading logic."""
    if bot_status["running"]:
        return {"success": False, "message": "Bot is already running", "status": "running"}
    
    try:
        # Import here to avoid circular imports
        from backend.services.main_bot import main
        
        def bot_worker():
            """Worker function that runs the main bot logic."""
            try:
                while bot_status["running"]:
                    main()  # Run one trading cycle
                    if bot_status["running"]:  # Check if still should run
                        time.sleep(300)  # Wait 5 minutes between cycles
            except Exception as e:
                bot_status["error"] = str(e)
                bot_status["running"] = False
        
        # Start bot in background thread
        bot_thread = threading.Thread(target=bot_worker, daemon=True)
        bot_thread.start()
        
        now = time.time()
        bot_status["running"] = True
        bot_status["start_time"] = now
        bot_status["last_update"] = datetime.now(UTC).isoformat()
        bot_status["thread"] = bot_thread
        bot_status["error"] = None
        
        return {"success": True, "message": "Bot started with trading logic", "status": "running"}
        
    except Exception as e:
        bot_status["error"] = str(e)
        return {"success": False, "message": f"Failed to start bot: {str(e)}", "status": "error"}


def stop_bot():
    """Stoppar tradingboten."""
    if not bot_status["running"]:
        return {"success": False, "message": "Bot is not running", "status": "stopped"}
    
    bot_status["running"] = False
    bot_status["start_time"] = None
    bot_status["last_update"] = datetime.now(UTC).isoformat()
    
    # Wait for thread to finish (with timeout)
    if bot_status["thread"] and bot_status["thread"].is_alive():
        bot_status["thread"].join(timeout=5.0)
    
    bot_status["thread"] = None
    return {"success": True, "message": "Bot stopped successfully", "status": "stopped"}


def get_bot_status():
    """Returnerar nuvarande status för tradingboten, uptime och senaste uppdateringstid."""
    now = time.time()
    running = bot_status.get("running", False)
    if running and bot_status.get("start_time") is not None:
        uptime = now - bot_status["start_time"]
    else:
        uptime = 0.0
    
    # Check if thread is actually alive
    thread_alive = bool(bot_status["thread"] and bot_status["thread"].is_alive())
    
    # Update last_update timestamp on each status check
    bot_status["last_update"] = datetime.now(UTC).isoformat()
    
    status_info = {
        "status": "running" if running else "stopped",
        "uptime": uptime,
        "last_update": bot_status["last_update"],
        "thread_alive": thread_alive,
    }
    
    # Include error if any
    if bot_status.get("error"):
        status_info["error"] = bot_status["error"]
    
    return status_info
