# LEVI Phase 6 — Authentication and Persistence

## Architecture

Phase 6 adds opt-in multi-user authentication and durable PostgreSQL-compatible persistence without replacing existing paper-trading, alert, workspace, or in-memory registry behavior. `LEVI_AUTH_ENABLED` and `LEVI_PERSISTENCE_ENABLED` both default to `false`.

The provider-neutral `AuthProvider` boundary exposes signup, login, OAuth authorization, `verify_token`, `refresh_session`, and `revoke_session`. `SupabaseAuthAdapter` implements email/password and Google/GitHub authorization flows against Supabase GoTrue. Network transport is injectable and no credentials are stored by LEVI.

## Authentication

Routes are added to the existing FastAPI application:

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/oauth`
- `GET /api/auth/oauth/{provider}`
- `GET /api/auth/callback`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Protected requests use `Authorization: Bearer <token>`. Missing, expired, malformed, wrong-audience, and locally revoked tokens fail closed. Provider errors are converted to safe messages without response bodies or secrets. The local revocation set stores SHA-256 token fingerprints only; durable session rows store token hashes, never tokens.

## Persistence

SQLAlchemy models and the initial SQL migration cover users, profiles, trades, evidence, decisions, audit entries, and sessions. PostgreSQL is the production target; offline tests use SQLite. Every tenant-owned repository method requires `user_id`, and record selection/deletion combines record ID with that tenant ID. `UserRepository` is the identity-root exception and only looks up the authenticated user ID.

Current Phase 1–3 in-memory registries remain the default. Enabling persistence is an explicit deployment/migration decision; this sprint does not silently move or duplicate existing data.

## Configuration

```dotenv
LEVI_AUTH_ENABLED=false
LEVI_PERSISTENCE_ENABLED=false
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_JWT_SECRET=
LEVI_AUTH_AUDIENCE=authenticated
LEVI_AUTH_ISSUER=
DATABASE_URL=postgresql+psycopg://levi:change-me@localhost:5432/levi
```

Keep all real values in a secret manager. Never commit Supabase keys, JWT secrets, database passwords, access tokens, or refresh tokens.

## Schema and migration

`levi/persistence/migrations/001_initial.sql` provides the PostgreSQL baseline. `levi.persistence.migration.initialize_schema` provides a deterministic metadata initializer for controlled development and test environments. A later operational sprint may adopt Alembic without changing the models or repository contracts.

## Audit logging

Audit records are tenant-owned. The audit helper redacts password, token, access-token, refresh-token, and secret fields before persistence. Callers should record security-relevant actions, not raw request bodies.

## Testing

```bash
pytest tests/test_auth_models_service.py tests/test_jwt_validation.py tests/test_supabase_auth.py tests/test_auth_api.py tests/test_persistence_repositories.py -q
pytest tests -q
```

Tests use fake providers, fake HTTP responses, and SQLite. No Supabase or PostgreSQL credentials and no network access are required.

## Known exclusions

No dashboard changes, model changes, trading-strategy changes, broker changes, automatic execution, Phase 7 deployment work, credential UI, social-provider callback UI, database provisioning, or migration of existing workspace files is included.
