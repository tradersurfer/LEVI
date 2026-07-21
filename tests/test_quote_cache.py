from datetime import datetime, timezone, timedelta
from levi.market_data.models import Quote
from levi.market_data.sources.cache import QuoteCache
def q(): return Quote.create(ticker="SPY",bid=1,ask=1.01,last=1,volume=1,timestamp=datetime.now(timezone.utc),source="x")
def test_cache_stores_and_retrieves(): c=QuoteCache(); c.set("spy",q()); assert c.get("SPY")
def test_cache_expires_old_quotes():
    c=QuoteCache(1); c._cache["SPY"]=(q(),datetime.now(timezone.utc)-timedelta(seconds=2)); assert c.get("SPY") is None
def test_cache_clear(): c=QuoteCache(); c.set("SPY",q()); c.clear(); assert c.get("SPY") is None
