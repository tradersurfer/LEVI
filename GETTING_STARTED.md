# Getting Started

## Requirements

- Python 3.11+
- Git
- Docker Desktop (optional)

Create a virtual environment, install `requirements.txt`, copy `.env.example` to `.env`, and run `python scripts/validate_env.py`. Generate the evidence key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`; never commit it.

Run locally with `uvicorn bot.status_api:app --reload`. Check `/health`, `/ready`, and `/docs`. `RUN_BOT=false`, `AUTO_EXECUTE=false`, and `TASTYTRADE_PAPER=true` are the safe defaults.

For containers, run `docker compose up --build`. The local Compose file starts LEVI and PostgreSQL for forward-compatible development, although the Phase 7 application does not add database persistence. Use `docker compose -f docker-compose.prod.yml config` to validate production configuration.

Run `pytest tests -q` before making changes. See `TROUBLESHOOTING.md` if readiness returns 503.
