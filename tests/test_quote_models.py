from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import pytest
from levi.market_data.models import Quote, QuoteValidationResult

def q(**kw):
    data=dict(ticker="spy", bid=99, ask=101, last=100, volume=10, timestamp=datetime.now(timezone.utc), source="test")
    data.update(kw); return Quote.create(**data)
def test_quote_model_normalizes_ticker(): assert q().ticker == "SPY"
def test_quote_is_immutable():
    with pytest.raises(FrozenInstanceError): q().bid = 1
def test_quote_bid_ask_spread_calculation(): assert q().bid_ask_spread_pct == 2
def test_quote_age_calculation(): assert q(timestamp=datetime.now(timezone.utc)-timedelta(seconds=2)).age_seconds >= 1.9
def test_validation_result_model(): assert QuoteValidationResult(True, [], []).is_valid
