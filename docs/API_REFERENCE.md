# API Reference

The default base URL is `http://localhost:8000`. FastAPI exposes interactive documentation at `/docs` and its schema at `/openapi.json`.

## Operations and status

- `GET /health`
- `GET /ready`
- `GET /state`
- `GET /signals`
- `GET /trades`

## Evidence

- `POST /api/what-you-need`
- `POST /api/evidence/upload`

## Dashboard

- `GET /api/dashboard/summary`
- `GET /api/dashboard/positions`
- `GET /api/dashboard/trades`
- `GET /api/dashboard/evidence`
- `GET /api/dashboard/decisions`
- `GET /api/dashboard/alerts`
- `GET /api/dashboard/setup-status`

Dashboard routes accept `user_id`. When `LEVI_AUTH_ENABLED=true`, the bearer identity must match that user ID.

## Authentication

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/oauth`
- `GET /api/auth/oauth/{provider}`
- `GET /api/auth/callback`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

No endpoint enables live or market-order execution.
