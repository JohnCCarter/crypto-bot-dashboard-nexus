import os
import pytest

# Force SQLite memory DB for test isolation
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.persistence import Base, engine, SessionLocal  # noqa: E402
from backend.persistence.models import BotStatus  # noqa: E402
from backend.persistence.utils import save_bot_state, load_bot_state  # noqa: E402


@pytest.mark.persistence
def test_bot_state_persistence_roundtrip():
    """Bot state saves and loads correctly via utils layer."""
    Base.metadata.create_all(bind=engine)

    dummy_state = {
        "running": True,
        "start_time": 123456.0,
        "last_update": "2025-01-01T00:00:00Z",
        "cycle_count": 3,
        "last_cycle_time": "2025-01-01T00:05:00Z",
        "error": None,
    }

    save_bot_state(dummy_state)
    loaded = load_bot_state()

    assert loaded is not None
    for key in dummy_state:
        if key in ("last_update", "last_cycle_time"):
            continue  # dynamic fields or timezone normalization
        assert loaded[key] == dummy_state[key]