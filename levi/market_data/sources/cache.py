from datetime import datetime, timedelta, timezone
import os


class QuoteCache:
    def __init__(self, ttl_seconds: int | None = None):
        self.ttl = timedelta(seconds=int(ttl_seconds if ttl_seconds is not None else os.getenv("LEVI_QUOTE_CACHE_TTL_SECONDS", "60")))
        self._cache = {}
    def get(self, ticker):
        key = ticker.upper()
        value = self._cache.get(key)
        if not value: return None
        quote, cached_at = value
        if datetime.now(timezone.utc) - cached_at > self.ttl:
            del self._cache[key]; return None
        return quote
    def set(self, ticker, quote): self._cache[ticker.upper()] = (quote, datetime.now(timezone.utc))
    def clear(self): self._cache.clear()
