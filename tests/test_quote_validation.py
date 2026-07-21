from datetime import datetime, timezone
from levi.market_data.models import Quote
from levi.market_data.validators import QuoteValidator

def q(bid=100, ask=101, age=0, volume=1): return Quote("SPY",bid,ask,100,volume,datetime.now(timezone.utc),"x",age,((ask-bid)/((ask+bid)/2)*100 if ask+bid else float("inf")))
def test_validator_rejects_zero_bid(): assert not QuoteValidator().validate(q(bid=0)).is_valid
def test_validator_rejects_ask_below_bid(): assert not QuoteValidator().validate(q(ask=99)).is_valid
def test_validator_rejects_wide_spread(): assert not QuoteValidator().validate(q(ask=110)).is_valid
def test_validator_rejects_stale_quote(): assert not QuoteValidator().validate(q(age=16)).is_valid
def test_validator_accepts_valid_quote(): assert QuoteValidator().validate(q()).is_valid
def test_validator_options_vs_stocks_age():
    v=QuoteValidator(); assert not v.validate(q(age=4), True).is_valid and v.validate(q(age=4)).is_valid
def test_validator_warning_zero_volume(): assert QuoteValidator().validate(q(volume=0)).warnings == ["volume is zero"]
