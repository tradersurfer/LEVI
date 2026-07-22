# Getting Started

## 1. Enter the cloned repository

Always change into the LEVI repository before running an installer, Python, pip, or Uvicorn command:

```bash
git clone https://github.com/tradersurfer/LEVI
cd LEVI
```

Do not install LEVI from a shell that is still using another project's virtual environment. Deactivate it first, then create a fresh environment scoped to this checkout.

## 2. Create a repository-local virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

The active Python executable must resolve inside this repository's `.venv`. Windows users may instead run the guarded installer from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

The installer creates `.venv`, activates it for the installation process, installs dependencies with that environment's Python, and validates the environment. It refuses to run from another directory.

## 3. Install and configure

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Generate a Fernet evidence-encryption key and place it in `.env` as `LEVI_EVIDENCE_ENCRYPTION_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Never commit `.env` or its values. Safe defaults in `.env.example` include:

```dotenv
LEVI_WORKSPACE_ROOT=./workspace
LEVI_DEFAULT_EXECUTION_MODE=paper_trading
LEVI_DEFAULT_TRADING_MODE=swing_trading
LEVI_ALLOW_PLAINTEXT_EVIDENCE=false
TASTYTRADE_API_URL=https://api.cert.tastyworks.com
TASTYTRADE_PAPER=true
AUTO_EXECUTE=false
RUN_BOT=false
LEVI_AUTH_ENABLED=false
LEVI_PERSISTENCE_ENABLED=false
```

Paper-broker credentials use `TASTYTRADE_USERNAME`, `TASTYTRADE_PASSWORD`, and `TASTYTRADE_PAPER_ACCOUNT_ID`. Keep all real values in `.env` or a deployment secret manager.

## 4. Validate and run

```bash
python scripts/validate_env.py
python -m uvicorn bot.status_api:app --reload
```

Open `http://127.0.0.1:8000/docs`, then verify `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/ready`.

## Dashboard

```bash
cd dashboard
npm install
npm run dev
```

The default CORS configuration permits `http://localhost:3000` and `http://localhost:5173`.

## Docker

```bash
docker compose up --build
```

The container runs as the non-root `levi` user. The runtime workspace is mounted outside the image.

## Tests

```bash
pytest tests -q
python -m compileall -q levi bot
python scripts/security_audit.py
```

See [Troubleshooting](TROUBLESHOOTING.md) if Python or Uvicorn resolves outside `.venv`, readiness returns 503, or Docker reports an unhealthy container.
