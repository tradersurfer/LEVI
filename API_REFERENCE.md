# API Reference

The default base URL is `http://localhost:8000`. FastAPI also exposes `/docs` and `/openapi.json`.

## Operations

- `GET /health` returns process health, version, and UTC timestamp.
- `GET /ready` validates deployment configuration. It returns 200 when ready or 503 with secret-safe error names.

## Existing status API

- `GET /state` returns the current detected state or `UNKNOWN`.
- `GET /signals` returns current signal state.
- `GET /trades` returns open paper trades and the blocklist.

## Evidence gate

`POST /api/what-you-need` accepts JSON: `{"user_id":"user-1","request_type":"trade_analysis","ticker":"SPY"}`. It returns required, optional, available, and missing evidence plus `can_proceed`.

## Evidence upload

`POST /api/evidence/upload` accepts multipart fields `user_id`, `source_name`, optional `declared_evidence_type`, optional `captured_at`, and `file`. Success is 201. Expected failures are 400, 404, 413, 415, and 422; internal failures return a path- and key-free 500 response.

No endpoint enables live or automatic trading.
