"""Structural and freshness validation for quotes."""
import os
from .models import Quote, QuoteValidationResult


class QuoteValidator:
    def __init__(self, min_bid: float = 0.0, max_bid_ask_spread_pct: float | None = None,
                 max_age_seconds_options: int | None = None,
                 max_age_seconds_stocks: int | None = None):
        self.min_bid = min_bid
        self.max_spread_pct = float(max_bid_ask_spread_pct if max_bid_ask_spread_pct is not None else os.getenv("LEVI_MAX_BID_ASK_SPREAD_PCT", "5.0"))
        self.max_age_options = int(max_age_seconds_options if max_age_seconds_options is not None else os.getenv("LEVI_MAX_QUOTE_AGE_OPTIONS", "3"))
        self.max_age_stocks = int(max_age_seconds_stocks if max_age_seconds_stocks is not None else os.getenv("LEVI_MAX_QUOTE_AGE_STOCKS", "15"))

    def validate(self, quote: Quote, is_option: bool = False) -> QuoteValidationResult:
        errors, warnings = [], []
        if quote.bid <= self.min_bid: errors.append(f"bid must be > {self.min_bid}")
        if quote.ask <= quote.bid: errors.append(f"ask ({quote.ask}) must be > bid ({quote.bid})")
        if quote.bid_ask_spread_pct > self.max_spread_pct: errors.append(f"spread {quote.bid_ask_spread_pct:.2f}% exceeds {self.max_spread_pct}%")
        maximum = self.max_age_options if is_option else self.max_age_stocks
        if quote.age_seconds > maximum: errors.append(f"quote age {quote.age_seconds:.1f}s exceeds {maximum}s")
        if quote.volume == 0: warnings.append("volume is zero")
        return QuoteValidationResult(not errors, errors, warnings)
