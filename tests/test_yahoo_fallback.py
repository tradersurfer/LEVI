import requests
from levi.market_data.sources.yahoo_finance import YahooFinanceSource
class R:
    def raise_for_status(self): pass
    def json(self): return {"quoteResponse":{"result":[{"symbol":"SPY","bid":100,"ask":101,"regularMarketPrice":100.5,"regularMarketVolume":99,"regularMarketTime":1784649600}]}}
class Session:
    def get(self,*a,**k): return R()
def test_yahoo_fetches_quote(): assert YahooFinanceSource(Session()).get_quote("SPY").ticker == "SPY"
def test_yahoo_is_available(): assert YahooFinanceSource(Session()).is_available()
def test_yahoo_health_check(): assert YahooFinanceSource(Session()).health_check()
def test_yahoo_returns_none_on_network_error():
    class Bad:
        def get(self,*a,**k): raise requests.ConnectionError()
    assert YahooFinanceSource(Bad()).get_quote("SPY") is None
def test_yahoo_quote_is_delayed(): assert "delayed" in YahooFinanceSource(Session()).get_quote("SPY").source
def test_yahoo_empty_result_returns_none():
    class EmptyR(R):
        def json(self): return {"quoteResponse":{"result":[]}}
    class Empty:
        def get(self,*a,**k): return EmptyR()
    assert YahooFinanceSource(Empty()).get_quote("SPY") is None
