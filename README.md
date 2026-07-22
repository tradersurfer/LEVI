<p align="center">
  <img src="docs/assets/levi-avatar.svg" width="140" align="right" alt="LEVI mascot" />
</p>

<p align="center">

██╗     ███████╗██╗   ██╗██╗
██║     ██╔════╝██║   ██║██║
██║     █████╗  ██║   ██║██║
██║     ██╔══╝  ╚██╗ ██╔╝██║
███████╗███████╗ ╚████╔╝ ██║
╚══════╝╚══════╝  ╚═══╝  ╚═╝

</p>

<p align="center"><i>AI options intelligence — paper trading only</i></p>

<p align="center">
<img src="https://img.shields.io/badge/Status-Public%20Alpha-orange?style=flat-square" alt="Public Alpha">
<img src="https://img.shields.io/badge/Paper%20Trading-Default-1B365D?style=flat-square" alt="Paper Trading Default">
<img src="https://img.shields.io/badge/Consensus-3%2F3-2F6FE4?style=flat-square" alt="3 of 3 Consensus">
<img src="https://img.shields.io/badge/Python-3.11-306998?style=flat-square" alt="Python 3.11">
<img src="https://img.shields.io/badge/License-Apache%202.0-lightgrey?style=flat-square" alt="Apache 2.0 License">
</p>

# LEVI

LEVI gathers evidence, applies deterministic risk rules, requires unanimous AI agreement from three independent specialist agents, and only then becomes eligible to place a **paper** trade.

No live execution. No exceptions in this release.

> Risk is decided before intelligence. Models never control risk — they only provide evidence.

---

## Install

**Requirements:** Python 3.11+, Node 18+ (for the dashboard), Docker (optional)

```bash
git clone https://github.com/tradersurfer/LEVI
cd LEVI

python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
cp .env.example .env       # Windows PowerShell: Copy-Item .env.example .env

python scripts/validate_env.py
python -m uvicorn bot.status_api:app --reload
```

Windows users can instead run `powershell -ExecutionPolicy Bypass -File scripts/install.ps1` from the repository root. The installer creates and uses this repository's `.venv`.

Or with Docker:

```bash
docker compose up --build
```

Paper trading is on by default: `TASTYTRADE_PAPER=true`, `LEVI_DEFAULT_EXECUTION_MODE=paper_trading`, `AUTO_EXECUTE=false`, and `RUN_BOT=false`. Live execution is not available in this release.

Evidence encryption requires a deployment-specific `LEVI_EVIDENCE_ENCRYPTION_KEY`. Authentication and persistence are opt-in through `LEVI_AUTH_ENABLED=false` and `LEVI_PERSISTENCE_ENABLED=false` defaults. See [.env.example](.env.example) for the complete configuration contract.

Full setup, dashboard install, and paper-broker configuration: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)

---

## What LEVI does

### Philosophy

```text
Deterministic policy
        ↓
Risk controls
        ↓
Evidence and specialist research
        ↓
3-of-3 consensus
        ↓
Paper-order eligibility
```

Models provide bounded analysis from supplied evidence. Python owns validation, risk vetoes, tenant isolation, and execution policy. Missing or weak evidence produces no trade.

### Architecture

```text
User profile + mode policy
            │
            ▼
Encrypted, user-scoped evidence ──► What You Need gate
            │
            ▼
SCOUT + ATLAS + LENS specialists
            │
            ▼
Unanimous consensus (3 / 3)
            │
            ▼
GUARDIAN deterministic risk veto
            │
            ▼
Paper-only LIMIT-order gateway
```

The FastAPI entrypoint is `bot/status_api.py`. Broker, market-data, evidence-storage, and model providers sit behind explicit interfaces. The dashboard is read-only and user-scoped; authentication and durable persistence are opt-in.

### Specialist agents and consensus

| Agent | Responsibility |
|---|---|
| **SCOUT** | Supplied sentiment, flow, news, and crowd-positioning evidence |
| **ATLAS** | Supplied macro, rates, volatility, regime, and catalyst evidence |
| **LENS** | Ticker-matched chart structure and validated quotes |
| **VOLT** | Deterministic Black–Scholes and liquidity diagnostics |
| **GUARDIAN** | Non-model risk checks and final veto authority |
| **SCRIBE** | Narrative summary without a vote |

SCOUT, ATLAS, and LENS must return the same bullish or bearish verdict at or above `LEVI_CONSENSUS_MIN_CONFIDENCE=0.70`. Neutral, blocked, insufficient, malformed, low-confidence, ownership-mismatched, or 2-to-1 outcomes do not approve. GUARDIAN can veto any unanimous result.

### Risk engine

These rules are deterministic and cannot be overridden by a model:

| Rule | Enforcement |
|---|---|
| Execution mode | Paper trading required |
| Order type | LIMIT only; market orders prohibited |
| Minimum DTE | Four days by default |
| Averaging down | Prohibited |
| Loss and position limits | Enforced from the validated user profile |
| Quote freshness | Three seconds for options; fifteen seconds for stocks |
| Buying power and approval | Required before eligibility |

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Security](docs/SECURITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Contributing](docs/CONTRIBUTING.md)
- [FAQ](docs/FAQ.md)

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).

---

**Paper trade first. Not financial advice.**
