"""Immutable market quote contracts."""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Quote:
    ticker: str
    bid: float
    ask: float
    last: float
    volume: int
    timestamp: datetime
    source: str
    age_seconds: float
    bid_ask_spread_pct: float

    @classmethod
    def create(cls, *, ticker: str, bid: float, ask: float, last: float,
               volume: int, timestamp: datetime, source: str,
               now: datetime | None = None) -> "Quote":
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        reference = now or datetime.now(timezone.utc)
        age = max(0.0, (reference - timestamp).total_seconds())
        midpoint = (bid + ask) / 2
        spread = ((ask - bid) / midpoint * 100) if midpoint > 0 else float("inf")
        return cls(ticker=ticker.strip().upper(), bid=float(bid), ask=float(ask),
                   last=float(last), volume=int(volume), timestamp=timestamp,
                   source=source, age_seconds=age, bid_ask_spread_pct=spread)


@dataclass(frozen=True)
class QuoteValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
