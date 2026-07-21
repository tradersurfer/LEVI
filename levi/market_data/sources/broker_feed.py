"""Optional duck-typed broker quote source."""
from datetime import datetime, timezone
from ..models import Quote


class BrokerQuoteFeed:
    def __init__(self, broker): self.broker = broker
    def get_quote(self, ticker: str) -> Quote | None:
        try:
            getter = getattr(self.broker, "get_quote", None)
            if not callable(getter): return None
            raw = getter(ticker)
            if raw is None: return None
            if isinstance(raw, Quote): return raw
            value = raw if isinstance(raw, dict) else vars(raw)
            timestamp = value.get("timestamp") or datetime.now(timezone.utc)
            return Quote.create(ticker=ticker, bid=value["bid"], ask=value["ask"],
                                last=value.get("last", (value["bid"] + value["ask"]) / 2),
                                volume=value.get("volume", 0), timestamp=timestamp, source="broker")
        except (AttributeError, KeyError, TypeError, ValueError): return None
    def is_available(self) -> bool:
        try: return bool(self.broker.is_connected()) and callable(getattr(self.broker, "get_quote", None))
        except Exception: return False
    def health_check(self) -> bool: return self.is_available() and self.get_quote("SPY") is not None
