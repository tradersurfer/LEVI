from datetime import datetime, time, timezone
from enum import Enum
from zoneinfo import ZoneInfo


class MarketSession(str, Enum):
    PRE_MARKET="pre_market"; REGULAR="regular"; AFTER_HOURS="after_hours"; CLOSED="closed"


class SessionDetector:
    def __init__(self, timezone_str="America/New_York"): self.tz = ZoneInfo(timezone_str)
    def detect(self, dt=None):
        value = dt or datetime.now(timezone.utc)
        if value.tzinfo is None: value = value.replace(tzinfo=timezone.utc)
        local = value.astimezone(self.tz)
        if local.weekday() >= 5: return MarketSession.CLOSED
        clock = local.time()
        if time(4) <= clock < time(9,30): return MarketSession.PRE_MARKET
        if time(9,30) <= clock < time(16): return MarketSession.REGULAR
        if time(16) <= clock < time(20): return MarketSession.AFTER_HOURS
        return MarketSession.CLOSED
    def is_trading_hours(self, dt=None): return self.detect(dt) is MarketSession.REGULAR
