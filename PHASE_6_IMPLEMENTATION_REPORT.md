# LEVI Phase 6 — Authentication and Persistence Implementation Report

## Summary

Implemented opt-in Supabase authentication contracts, session/JWT validation, FastAPI auth endpoints, PostgreSQL-compatible SQLAlchemy models, tenant-scoped repositories, an initial schema migration, and secret-safe audit logging. Existing paper-trading, alert-mode, file workspace, and in-memory evidence behavior remain unchanged and enabled by default.

## Starting Commit

`5d60dd9` — main after Phase 2A, Phase 2B, and Phase 3.

## Branch and Commit

Branch: `phase-6-auth-persistence`. The final SHA is recorded in the completion handoff. The branch remains local and is not pushed or merged.

## Files Created

- `levi/auth/{__init__.py,api.py,base.py,errors.py,jwt.py,middleware.py,models.py,service.py,sessions.py,supabase.py}`
- `levi/persistence/{__init__.py,audit.py,database.py,migration.py,models.py}`
- `levi/persistence/repositories/{__init__.py,base.py,users.py,profiles.py,trades.py,evidence.py,decisions.py,audit.py,sessions.py}`
- `levi/persistence/migrations/001_initial.sql`
- `tests/auth_helpers.py`
- `tests/test_auth_models_service.py`
- `tests/test_jwt_validation.py`
- `tests/test_supabase_auth.py`
- `tests/test_auth_api.py`
- `tests/test_persistence_repositories.py`
- `docs/PHASE_6_AUTH_PERSISTENCE.md`
- `PHASE_6_IMPLEMENTATION_REPORT.md`

## Files Modified

- `.env.example`
- `requirements.txt`
- `bot/status_api.py`

## Dependencies Added or Changed

Added SQLAlchemy 2, PyJWT, and the Psycopg 3 binary package. Existing Requests and FastAPI dependencies are reused. No Supabase SDK was added because the narrow GoTrue HTTP adapter is deterministic, injectable, and avoids a larger dependency surface.

## Authentication Coverage

Email signup/login, Google/GitHub authorization URLs, token verification, refresh, provider revocation, local fingerprint revocation, JWT signature/expiry/audience validation, bearer extraction, and `/api/auth` routes are covered. Authentication is disabled unless `LEVI_AUTH_ENABLED=true`.

## Persistence and Tenant Isolation

The ledger contains User, Profile, Trade, Evidence, Decision, Audit, and Session models. Every tenant-owned get/list/add/delete method requires a user ID. Tests prove another user cannot read or delete a record by knowing its ID. Persistence is disabled unless `LEVI_PERSISTENCE_ENABLED=true`; legacy in-memory paths are preserved.

## Security Checks

Tokens and passwords are not logged or persisted in plaintext. Audit fields are redacted. Missing configuration and invalid tokens fail closed. Provider errors do not expose response bodies. SQLAlchemy parameterization is used for all repository queries.

## Tests Executed and Results

All 46 focused Phase 6 tests passed. The complete repository suite passed with 232 tests, one expected Windows symlink-capability skip, and three existing FastAPI/TestClient deprecation warnings. All tests are offline and require no live Supabase or PostgreSQL instance. Python compilation and `git diff --check` also passed.

## Blockers

None for the implemented contracts. Live Supabase and PostgreSQL verification requires user-provided deployment credentials and infrastructure and is not claimed.

## Assumptions

Supabase GoTrue remains the authentication authority. PostgreSQL is the production database, SQLite is test-only, and durable migration of existing workspace/in-memory data is a later explicitly approved operation.

## Scope Exclusions Confirmed

No model, specialist-agent, trading, broker, dashboard, live-execution, deployment, or Phase 7 work was implemented.

## Recommended Next Action

Stop for review. Do not push or merge until explicitly authorized.
