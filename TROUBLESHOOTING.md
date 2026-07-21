# Troubleshooting

## `/ready` returns 503

Run `python scripts/validate_env.py`. In production, set `LEVI_EVIDENCE_ENCRYPTION_KEY`, `LEVI_CORS_ORIGINS`, disable plaintext evidence, keep paper mode enabled, and keep automatic execution disabled.

## Evidence upload reports unsafe storage

Configure a valid Fernet key and restart the process. Do not enable plaintext storage in production.

## Container is unhealthy

Inspect `docker compose logs app`, then call `/health` and `/ready`. Confirm the workspace volume is writable by the non-root container user.

## Tests fail on Windows symlinks

One evidence-storage test may skip when the host cannot create symbolic links. A skip is not a storage-isolation failure.

## Yahoo quote unavailable

Yahoo is best-effort and delayed. Network failure returns no quote rather than bypassing validation.
