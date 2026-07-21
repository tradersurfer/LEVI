from datetime import datetime, timezone
from levi.market_data.session import MarketSession, SessionDetector
def dt(hour,minute=0): return datetime(2026,7,20,hour,minute,tzinfo=timezone.utc) # EDT = UTC-4
def test_detect_pre_market(): assert SessionDetector().detect(dt(12)) is MarketSession.PRE_MARKET
def test_detect_regular(): assert SessionDetector().detect(dt(14)) is MarketSession.REGULAR
def test_detect_after_hours(): assert SessionDetector().detect(dt(21)) is MarketSession.AFTER_HOURS
def test_detect_closed(): assert SessionDetector().detect(dt(1)) is MarketSession.CLOSED
def test_is_trading_hours(): assert SessionDetector().is_trading_hours(dt(14))
def test_weekend_closed(): assert SessionDetector().detect(datetime(2026,7,19,14,tzinfo=timezone.utc)) is MarketSession.CLOSED
