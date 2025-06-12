import datetime
from typing import Optional


class TradingWindow:
    def __init__(self, config: dict):
        self.start_hour = config.get("start_hour", 0)
        self.end_hour = config.get("end_hour", 24)
        self.max_trades_per_day = config.get("max_trades_per_day", 5)
        self._trades_today = 0
        self._last_trade_date: Optional[datetime.date] = None

    def is_within_window(self) -> bool:
        now = datetime.datetime.now()
        return self.start_hour <= now.hour < self.end_hour

    def can_trade(self) -> bool:
        today = datetime.date.today()
        if self._last_trade_date != today:
            self._trades_today = 0
            self._last_trade_date = today
        return self._trades_today < self.max_trades_per_day

    def register_trade(self):
        today = datetime.date.today()
        if self._last_trade_date != today:
            self._trades_today = 0
            self._last_trade_date = today
        self._trades_today += 1 