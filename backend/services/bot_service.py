import time
from datetime import UTC, datetime

# Shared status for the trading bot
bot_status = {
    "running": False,
    "start_time": None,
    "last_update": None,
}


def start_bot():
    """Startar tradingboten."""
    now = time.time()
    bot_status["running"] = True
    bot_status["start_time"] = now
    bot_status["last_update"] = datetime.now(UTC).isoformat()
    return {"message": "Bot started", "status": "running"}


def stop_bot():
    """Stoppar tradingboten."""
    bot_status["running"] = False
    bot_status["start_time"] = None
    bot_status["last_update"] = datetime.now(UTC).isoformat()
    return {"message": "Bot stopped", "status": "stopped"}


def get_bot_status():
    """Returnerar nuvarande status för tradingboten, uptime och senaste uppdateringstid."""
    now = time.time()
    running = bot_status.get("running", False)
    if running and bot_status.get("start_time") is not None:
        uptime = now - bot_status["start_time"]
    else:
        uptime = 0.0
    # Update last_update timestamp on each status check
    bot_status["last_update"] = datetime.now(UTC).isoformat()
    return {
        "status": "running" if running else "stopped",
        "uptime": uptime,
        "last_update": bot_status["last_update"],
    }
