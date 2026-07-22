# Troubleshooting

## Python or Uvicorn resolves to the wrong environment

This usually means another project's global or virtual environment is still active. From the LEVI repository root, deactivate it and activate LEVI's own `.venv`:

```bash
deactivate 2>/dev/null || true
source .venv/bin/activate
python -c "import sys; print(sys.executable)"
command -v uvicorn
```

Windows PowerShell:

```powershell
deactivate
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
Get-Command uvicorn
```

`sys.executable` must point inside the current checkout's `.venv`. Prefer `python -m uvicorn bot.status_api:app --reload` so Uvicorn uses the same interpreter. If the environment belongs to another project or remains ambiguous, remove `.venv`, recreate it in this repository, and reinstall `requirements.txt`.

## `/ready` returns 503

Run `python scripts/validate_env.py`. In production, configure `LEVI_EVIDENCE_ENCRYPTION_KEY` and explicit `LEVI_CORS_ORIGINS`; keep plaintext evidence and automatic execution disabled and paper mode enabled.

## Evidence upload reports unsafe storage

Configure a valid Fernet key and restart the process. Do not enable plaintext storage in production.

## Container is unhealthy

Inspect `docker compose logs app`, then call `/health` and `/ready`. Confirm the workspace volume is writable by the non-root `levi` user.

## Tests skip a Windows symlink case

One evidence-storage test may skip when the host cannot create symbolic links. A skip is not a storage-isolation failure.

## Yahoo quote unavailable

Yahoo is best-effort and delayed. Network failure returns no quote rather than bypassing quote validation.
