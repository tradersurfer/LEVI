# LEVI

LEVI is an evidence-first trading analysis and paper-execution foundation. The public alpha provides validated user profiles, mode policies, encrypted evidence ingestion, a pre-analysis evidence gate, paper-only broker adapters, and quote validation.

> Paper trading only. LEVI is not financial advice and does not provide a live-trading path.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
copy .env.example .env  # use cp on macOS/Linux
python scripts/validate_env.py
uvicorn bot.status_api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`. See [Getting Started](GETTING_STARTED.md), [API Reference](API_REFERENCE.md), [Architecture](ARCHITECTURE.md), and [Security](SECURITY.md).

## Docker

```bash
docker compose up --build
python scripts/smoke_test.py
```

Production deployments must provide an evidence-encryption key and explicit CORS origins. Release assets are prepared for `v0.1.0-alpha`; no tag or public release is created by this branch.

## Development

```bash
pytest tests -q
python scripts/security_audit.py
python scripts/performance_baseline.py
```

Read [Contributing](CONTRIBUTING.md), [Troubleshooting](TROUBLESHOOTING.md), and the [FAQ](FAQ.md) before opening a change.
