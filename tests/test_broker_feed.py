from datetime import datetime, timezone
from levi.market_data.sources.broker_feed import BrokerQuoteFeed
class Broker:
    def __init__(self, connected=True, value=None): self.connected,self.value=connected,value
    def is_connected(self): return self.connected
    def get_quote(self,t): return self.value
def raw(): return {"bid":100,"ask":101,"last":100.5,"volume":2,"timestamp":datetime.now(timezone.utc)}
def test_broker_feed_fetches_quote(): assert BrokerQuoteFeed(Broker(value=raw())).get_quote("SPY").source == "broker"
def test_broker_feed_is_available_when_connected(): assert BrokerQuoteFeed(Broker(value=raw())).is_available()
def test_broker_feed_health_check(): assert BrokerQuoteFeed(Broker(value=raw())).health_check()
def test_broker_feed_returns_none_on_unsupported(): assert BrokerQuoteFeed(Broker(value=None)).get_quote("SPY") is None
def test_broker_feed_graceful_without_quote_method(): assert not BrokerQuoteFeed(object()).is_available()
