from datetime import datetime, timedelta, timezone
from levi.market_data.models import Quote
from levi.market_data.validators import QuoteValidator
def make(age): return Quote.create(ticker="SPY",bid=100,ask=101,last=100,volume=1,timestamp=datetime.now(timezone.utc)-timedelta(seconds=age),source="x")
def test_quote_age_calculation(): assert make(2).age_seconds >= 1.9
def test_freshness_threshold_options(): assert QuoteValidator().validate(make(2),True).is_valid
def test_freshness_threshold_stocks(): assert QuoteValidator().validate(make(10)).is_valid
def test_stale_quote_rejected(): assert not QuoteValidator().validate(make(20)).is_valid
