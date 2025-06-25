from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from . import SessionLocal, Base, engine
from .models import BotStatus

# Ensure tables exist (safe to call multiple times)
Base.metadata.create_all(bind=engine)


def save_bot_state(state: Dict[str, Any]) -> None:
    """Persist bot state to database (upsert id=1)."""
    session = SessionLocal()
    try:
        status: Optional[BotStatus] = session.get(BotStatus, 1)
        if status is None:
            status = BotStatus(id=1)
            session.add(status)

        status.running = state.get("running", False)
        status.start_time = state.get("start_time")
        # last_update always now; DB row has own timestamp but keep accurate copy
        status.last_update = datetime.utcnow()
        status.cycle_count = state.get("cycle_count", 0)
        lct = state.get("last_cycle_time")
        if isinstance(lct, str):
            try:
                lct_dt = datetime.fromisoformat(lct.replace("Z", "+00:00"))
            except ValueError:
                lct_dt = None
            status.last_cycle_time = lct_dt
        else:
            status.last_cycle_time = lct
        status.error = state.get("error")

        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        # Failing to persist should not crash the bot; log and continue
        print(f"[Warning] Failed to persist bot state: {exc}")
    finally:
        session.close()


def load_bot_state() -> Optional[Dict[str, Any]]:
    """Load bot state from database. Returns None if no record."""
    session = SessionLocal()
    try:
        status: Optional[BotStatus] = session.get(BotStatus, 1)
        if status is None:
            return None
        return {
            "running": status.running,
            "start_time": status.start_time,
            "last_update": status.last_update.isoformat() if status.last_update else None,
            "cycle_count": status.cycle_count,
            "last_cycle_time": status.last_cycle_time.isoformat() if status.last_cycle_time else None,
            "error": status.error,
        }
    finally:
        session.close()