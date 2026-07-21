"""Market data source boundary and ordered fallback adapter."""
from typing import Protocol
from .models import Quote


class MarketDataSource(Protocol):
    def get_quote(self, ticker: str) -> Quote | None: ...
    def is_available(self) -> bool: ...
    def health_check(self) -> bool: ...


class MarketDataAdapter:
    def __init__(self, sources: list[MarketDataSource], validator=None, cache=None):
        self.sources, self.validator, self.cache = sources, validator, cache

    def get_quote(self, ticker: str, *, is_option: bool = False) -> Quote | None:
        symbol = ticker.strip().upper()
        if not symbol: return None
        if self.cache:
            cached = self.cache.get(symbol)
            if cached and (not self.validator or self.validator.validate(cached, is_option).is_valid): return cached
        for source in self.sources:
            try:
                if not source.is_available(): continue
                quote = source.get_quote(symbol)
                if quote and (not self.validator or self.validator.validate(quote, is_option).is_valid):
                    if self.cache: self.cache.set(symbol, quote)
                    return quote
            except Exception:
                continue
        return None
