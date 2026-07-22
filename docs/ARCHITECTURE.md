# Architecture

LEVI is a modular FastAPI application. Profiles and mode routing define policy; user workspaces isolate context; encrypted evidence feeds the What You Need gate; specialist agents produce immutable decisions; unanimous consensus remains subject to the deterministic GUARDIAN veto. Eligible execution is paper-only and LIMIT-only.

`bot/status_api.py` is the API entrypoint. `/health` proves the process responds and `/ready` validates deployment configuration. Broker, market-data, storage, authentication, and persistence providers sit behind explicit interfaces. Authentication and PostgreSQL-compatible persistence are opt-in; local paper-trading behavior remains the default.

Docker runs as the non-root `levi` user. CI verifies image construction, health, readiness, non-root execution, an empty runtime workspace, and exclusion of `.env` and `.git` content.
