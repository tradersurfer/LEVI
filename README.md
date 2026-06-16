# JECI Trading Suite v2

Tri-tier options bot with state engine, tri-agent consensus, and programmatic risk moat.

> ⚠️ **PAPER MODE ON BY DEFAULT.** `TASTYTRADE_PAPER=true` and `AUTO_EXECUTE=false` ship as defaults. Validate thoroughly on paper before flipping either.

## Architecture

| Layer | What it does |
|---|---|
| `market_state.py` | Detects BULL_TRAP / WATERFALL / V_BOTTOM on SPY 15m data (no API key) |
| `consensus_engine.py` | Risk Moat (programmatic) → Grok + Claude in parallel → Gemini final veto |
| `jeci_options_bot.py` | Tri-tier scan loop, Tastytrade routing, limit orders only |
| `status_api.py` | FastAPI endpoints consumed by the dashboard |
| `dashboard/` | Vite + React terminal-style UI |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TASTYTRADE_PAPER` | `true` | `false` = live money |
| `AUTO_EXECUTE` | `false` | `true` = no confirm prompts |
| `CONSENSUS_REQUIRED` | `true` | `false` = moat-only mode |
| `TT_USERNAME` | — | Tastytrade login |
| `TT_PASSWORD` | — | Tastytrade password |
| `ACCT_TRADERSURFER` | — | Account number |
| `ACCT_ROBYHOOD` | — | Account number |
| `ACCT_HODL` | — | Account number |
| `XAI_API_KEY` | — | Grok agent |
| `ANTHROPIC_API_KEY` | — | Claude agent |
| `GOOGLE_API_KEY` | — | Gemini CRO |
| `RUN_BOT` | `false` | Start bot loop inside the API container |
| `PORT` | `8000` | API port |

## Local Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values

# Run tests first
pytest -q

# Run API server (bot loop disabled until RUN_BOT=true)
uvicorn bot.status_api:app --reload

# Dashboard
cd dashboard && npm install && npm run dev
```

## Railway Deploy

```bash
railway init
railway up

# Set secrets
railway variables set TASTYTRADE_PAPER=true AUTO_EXECUTE=false CONSENSUS_REQUIRED=true
railway variables set TT_USERNAME=xxx TT_PASSWORD=xxx
railway variables set XAI_API_KEY=xxx ANTHROPIC_API_KEY=xxx GOOGLE_API_KEY=xxx
railway variables set RUN_BOT=true
```

## OpenClaw Hookup

Point OpenClaw's webhook to `https://<your-railway-url>/state` for live state reads and `/signals` for tier signal feeds.

## Non-Negotiables

- Limit orders only — `place_order()` hardcodes `"order-type": "Limit"`
- No averaging down — stopped-out symbols are blocklisted for the session
- Risk Moat runs in Python before any LLM API call
- 4 DTE minimum, always
- HODL tier: equity alerts only, options banned in code
