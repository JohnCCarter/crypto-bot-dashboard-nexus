from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, Float, String, DateTime
from . import Base


class BotStatus(Base):
    """Persistent representation of the trading bot runtime state."""

    __tablename__ = "bot_status"

    id = Column(Integer, primary_key=True, index=True, default=1)
    running = Column(Boolean, nullable=False, default=False)
    start_time = Column(Float)
    last_update = Column(DateTime, default=datetime.utcnow)
    cycle_count = Column(Integer, default=0)
    last_cycle_time = Column(DateTime)
    error = Column(String)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<BotStatus running={self.running} cycles={self.cycle_count} "
            f"error={self.error}>"
        )