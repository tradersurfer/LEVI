from datetime import datetime, timezone
from levi.market_data.adapter import MarketDataAdapter
from levi.market_data.models import Quote
from levi.market_data.validators import QuoteValidator
class S:
    def __init__(self, quote=None, available=True): self.quote,self.available,self.calls=quote,available,0
    def is_available(self): return self.available
    def get_quote(self,t): self.calls+=1; return self.quote
def q(bid=100,ask=101): return Quote.create(ticker="SPY",bid=bid,ask=ask,last=100,volume=1,timestamp=datetime.now(timezone.utc),source="x")
def test_adapter_tries_sources_in_order():
    a,b=S(None),S(q()); assert MarketDataAdapter([a,b]).get_quote("spy") and (a.calls,b.calls)==(1,1)
def test_adapter_returns_first_valid():
    a,b=S(q()),S(q()); assert MarketDataAdapter([a,b]).get_quote("SPY") and b.calls==0
def test_adapter_returns_none_if_all_fail(): assert MarketDataAdapter([S(),S()]).get_quote("SPY") is None
def test_adapter_respects_validator():
    a,b=S(q(100,120)),S(q()); assert MarketDataAdapter([a,b],QuoteValidator()).get_quote("SPY") is b.quote
def test_adapter_skips_unavailable_sources():
    a,b=S(q(),False),S(q()); MarketDataAdapter([a,b]).get_quote("SPY"); assert a.calls==0
