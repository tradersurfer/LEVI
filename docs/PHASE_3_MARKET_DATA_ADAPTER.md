# LEVI Phase 3 — Market Data Adapter

## Architecture

`MarketDataAdapter` requests sources in configured order and returns the first quote accepted by `QuoteValidator`. `BrokerQuoteFeed` is optional and duck-typed, so Phase 3 remains independently usable. `YahooFinanceSource` is the delayed, best-effort fallback. `QuoteCache` avoids redundant calls.

## Quote contract and validation

`Quote` is immutable and contains ticker, bid, ask, last, volume, capture timestamp, source, calculated age, and midpoint-based spread percentage. Validation requires bid above zero, ask above bid, spread at or below the configured limit, and freshness within the instrument limit. Zero volume is a warning.

Defaults are 3 seconds for options, 15 seconds for stocks, and 5 percent maximum spread. Invalid quotes are skipped so the fallback chain can continue.

## Sources

- Broker: used only when a connected adapter exposes `get_quote`; missing support fails gracefully.
- Yahoo: uses the public quote endpoint through a bounded HTTP request and returns `None` on unavailable or malformed responses. Its source is explicitly marked `yahoo_delayed`.

Yahoo availability does not guarantee quote freshness. The validator remains authoritative.

## Caching

The in-memory, case-insensitive cache defaults to a 60-second TTL. Cached quotes are revalidated before use. It is process-local and non-durable.

## Market sessions

`SessionDetector` converts aware datetimes to US Eastern time and identifies pre-market (04:00–09:30), regular (09:30–16:00), after-hours (16:00–20:00), and closed periods. Weekends are closed. Exchange holidays and early closes are not modeled.

## Configuration

```dotenv
LEVI_MARKET_DATA_PRIMARY_SOURCE=broker
LEVI_MARKET_DATA_FALLBACK_SOURCE=yahoo
LEVI_QUOTE_CACHE_TTL_SECONDS=60
LEVI_MAX_QUOTE_AGE_OPTIONS=3
LEVI_MAX_QUOTE_AGE_STOCKS=15
LEVI_MAX_BID_ASK_SPREAD_PCT=5.0
```

## Tests

```bash
pytest tests/test_quote_models.py tests/test_quote_validation.py tests/test_market_data_adapter.py tests/test_broker_feed.py tests/test_yahoo_fallback.py tests/test_quote_cache.py tests/test_market_session.py tests/test_data_freshness.py -q
pytest tests -q
```

All source tests are offline and use deterministic fakes.

## Security and operational limitations

Yahoo is an unofficial, delayed public endpoint and may change or throttle. Errors log only exception classes, not response bodies. This sprint adds no credentials, persistence, WebSocket, hosted model, OCR, UI, authentication, or execution behavior. Quotes are informational inputs and do not generate trades.

## Future extension

A separately approved sprint may add an exchange calendar, persistent/distributed cache, WebSocket source, or formal quote method to the broker protocol. Those changes can implement the existing `MarketDataSource` boundary.
