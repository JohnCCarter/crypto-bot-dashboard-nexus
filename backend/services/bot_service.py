bot_status = {"running": False}

def start_bot():
    """Startar tradingboten."""
    bot_status["running"] = True
    return {"message": "Bot started", "status": "running"}

def stop_bot():
    """Stoppar tradingboten."""
    bot_status["running"] = False
    return {"message": "Bot stopped", "status": "stopped"}

def get_bot_status():
    """Returnerar nuvarande status för tradingboten."""
    return {"status": "running" if bot_status["running"] else "stopped"} 