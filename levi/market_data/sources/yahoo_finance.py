"""Best-effort delayed Yahoo quote fallback."""
import logging
from datetime import datetime, timezone
import requests
from ..models import Quote

log = logging.getLogger(__name__)


class YahooFinanceSource:
    def __init__(self, session=None, base_url="https://query1.finance.yahoo.com", timeout=5):
        self.session, self.base_url, self.timeout = session or requests.Session(), base_url.rstrip("/"), timeout
    def get_quote(self, ticker: str) -> Quote | None:
        try:
            response = self.session.get(f"{self.base_url}/v7/finance/quote", params={"symbols": ticker.upper()}, timeout=self.timeout)
            response.raise_for_status()
            results = response.json()["quoteResponse"]["result"]
            if not results: return None
            row = results[0]
            timestamp = datetime.fromtimestamp(row.get("regularMarketTime", 0), timezone.utc)
            return Quote.create(ticker=row.get("symbol", ticker), bid=row["bid"], ask=row["ask"],
                                last=row.get("regularMarketPrice", 0), volume=row.get("regularMarketVolume", 0),
                                timestamp=timestamp, source="yahoo_delayed")
        except (requests.RequestException, KeyError, TypeError, ValueError, IndexError) as exc:
            log.warning("Yahoo quote unavailable for %s: %s", ticker, type(exc).__name__)
            return None
    def is_available(self): return True
    def health_check(self): return self.get_quote("SPY") is not None
