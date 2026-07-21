# Architecture

LEVI is a modular FastAPI application. Profiles and mode routing define policy; workspaces isolate user context; evidence parsers and encrypted storage feed the What You Need gate. Paper broker and market-data adapters remain behind protocols.

`bot/status_api.py` is the single API entrypoint. `/health` proves the process responds and `/ready` validates deployment configuration. Docker runs as non-root. Compose supplies local app and PostgreSQL topology without adding persistence behavior.

Release automation runs tests, compilation, audits, and image construction. Publication is tag-gated. Authentication, persistence, dashboard redesign, mobile packaging, hosted vision, and live execution remain deferred.
