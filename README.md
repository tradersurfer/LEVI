<p align="center">
  <img src="https://img.shields.io/badge/JECI%20GROUP-Options%20Intelligence%20Platform-1B365D?style=for-the-badge" alt="JECI Group">
</p>

# LEVI ⚡
### Options Intelligence & Execution Agent

<p align="center">
  <a href="https://jecigroup.com"><img src="https://img.shields.io/badge/Built%20by-JECI%20Group-D4AF37?style=for-the-badge" alt="JECI Group"></a>
  <img src="https://img.shields.io/badge/Status-Production-brightgreen?style=for-the-badge" alt="Production">
  <img src="https://img.shields.io/badge/Paper%20Mode-Default%20ON-orange?style=for-the-badge" alt="Paper Mode">
  <img src="https://img.shields.io/badge/Consensus-3%2F3%20Unanimous-1B365D?style=for-the-badge" alt="Consensus">
  <img src="https://img.shields.io/badge/Deploy-Railway-blueviolet?style=for-the-badge" alt="Railway">
</p>

---

**LEVI is a white-label options intelligence and execution platform.** Deterministic market-state detection and hardcoded risk controls run first — before any AI model is consulted. Four specialist research agents then build context. Then a 3/3 unanimous vote from Grok, Claude, and DeepSeek R1 is required before a single order routes.

No consensus, no trade. No exceptions.

> **Paper mode is on by default.** Keep `TASTYTRADE_PAPER=true`, `AUTO_EXECUTE=false`, and `RUN_BOT=false` until the system has been validated end-to-end with your own configuration.

---

## Architecture

```
Market Data (SPY 15m)
        ↓
┌─────────────────────────────────────────────────────┐
│  Stage 1 — MARKET STATE ENGINE                      │
│  Detects: BULL_TRAP · WATERFALL · V_BOTTOM          │
└──────────────────────────┬──────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│  Stage 2 — RISK MOAT  ← hardcoded Python, no LLM   │
│  Position size · DTE ≥ 4 · RSI locks · State locks  │
│  Stopped symbols blocklisted for session             │
└──────────────────────────┬──────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│  Stage 3 — SPECIALIST AGENTS                        │
│  SCOUT → ATLAS → LENS → (TRACE if triggered)        │
└──────────────────────────┬──────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│  Stage 4 — CONSENSUS NETWORK                        │
│  Grok · Claude · DeepSeek R1                        │
│  3/3 unanimous required — any veto = no trade       │
└──────────────────────────┬──────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│  Stage 5 — EXECUTION                                │
│  Limit orders only → configured paper or live acct  │
└─────────────────────────────────────────────────────┘
```

---

## Specialist Agents

| Agent | Role |
|---|---|
| **SCOUT** | Scans social sentiment and signal velocity — momentum and crowd positioning |
| **ATLAS** | Classifies macro regime, trade bias, and upcoming catalysts |
| **LENS** | Evaluates technical setup quality — decides whether deeper verification is needed |
| **TRACE** | Focused evidence verification, triggered by LENS when setup needs confirmation |

---

## Consensus Network

| Model | Role | Veto |
|---|---|---|
| **Grok** | Sentiment + momentum signal | ✅ Any dissent kills the trade |
| **Claude** | Technical reasoning + bias | ✅ Any dissent kills the trade |
| **DeepSeek R1** | Final Risk Officer — extended thinking | ✅ Any dissent kills the trade |

Missing API keys, failed responses, or any veto all produce the same result: no trade.

---

## Account Tiers

| Tier | Variable | Purpose |
|---|---|---|
| **Core** | `ACCT_CORE` | Primary trading account — full execution |
| **Sandbox** | `ACCT_SANDBOX` | Testing and thesis validation — strict size limits |
| **HODL** | `ACCT_HODL` | Equity alerts only — options orders never route here |

Tier limits, watchlists, and operator branding are configured in `levi_config.json`, not in code.

---

## Non-Negotiables

These rules are enforced in the Risk Moat — hardcoded Python. No LLM can override them.

| Rule | Value |
|---|---|
| Order type | Limit orders only — no market orders, ever |
| Minimum DTE | 4 days |
| Averaging down | Never — stopped symbols are blocklisted for the session |
| HODL tier | Equity alerts only — no options orders, no exceptions |
| Consensus | 3/3 unanimous required before any execution call |
| Risk Moat | Always runs before model consensus, always |

---

## White-Label Configuration

Operator identity, account mappings, tier limits, watchlists, and model overrides all live in `levi_config.json`. Credentials stay in `.env`. Nothing customer-specific touches the codebase.

```json
// levi_config.json — customize before deploying
{
  "operator": "Your Operator Name",
  "tiers": { ... },
  "watchlists": { ... },
  "limits": { ... }
}
```

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `TASTYTRADE_PAPER` | `true` | Paper API when true — **leave true until validated** |
| `AUTO_EXECUTE` | `false` | Enables live order routing — explicitly opt in |
| `CONSENSUS_REQUIRED` | `true` | Requires 3/3 unanimous — never disable |
| `RUN_BOT` | `false` | Starts the scan loop — set true only on Railway |
| `TT_USERNAME` | — | Broker username |
| `TT_PASSWORD` | — | Broker password |
| `ACCT_CORE` | — | Core tier account number |
| `ACCT_SANDBOX` | — | Sandbox tier account number |
| `ACCT_HODL` | — | Alerts-only tier account number |
| `XAI_API_KEY` | — | Grok API key |
| `ANTHROPIC_API_KEY` | — | Claude API key |
| `DEEPSEEK_API_KEY` | — | OpenRouter key for DeepSeek R1 |
| `PERPLEXITY_API_KEY` | — | Live-data verification (TRACE agent) |
| `GROK_MODEL` | `grok-4` | Grok model override |
| `CLAUDE_MODEL` | `claude-sonnet-4-5` | Claude model override |
| `DEEPSEEK_MODEL` | `deepseek/deepseek-r1` | DeepSeek model override |
| `PERPLEXITY_MODEL` | `llama-3.1-sonar-large-128k-online` | Verification model override |
| `AGENT_TIMEOUT_SEC` | `25` | Per-agent request timeout |
| `LEVI_CONFIG_PATH` | `./levi_config.json` | White-label config path |
| `PORT` | `8000` | FastAPI service port |

---

## Setup

```bash
git clone <your-repository-url>
cd levi

# 1 — Customize operator, tiers, watchlists, and limits
$EDITOR levi_config.json

# 2 — Configure credentials
cp .env.example .env
# Fill in broker credentials and API keys

# 3 — Install and test
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q

# 4 — Run locally (API only — no trading loop)
uvicorn bot.status_api:app --reload
```

The API starts without the trading loop unless `RUN_BOT=true` is explicitly set. Run locally with paper mode on until every stage validates correctly.

---

## Deploy to Railway

```bash
railway login
railway init
railway up
```

Set all `.env` values as Railway environment secrets. Never commit credentials. `RUN_BOT=true` activates the scan loop on deployment — only set this after full validation.

---

## Part of the JECI Group Stack

Built and maintained by [Adrian Jordan](https://github.com/tradersurfer) · [JECI Group](https://jecigroup.com)

**Related:**
- `bib-marketplace` *(private)* — BIB Marketplace, where LEVI becomes an installable product listing
- `agent-jeci` *(private)* — Chief Intelligence Agent, the orchestration layer above this system
- [`deepseek-multi-turn`](https://github.com/tradersurfer/deepseek-multi-turn) — Multi-turn DeepSeek-R1 conversation pattern used in the consensus network

> *Systems beat hustle. A machine you understand well enough to automate runs while you sleep.*
>
> *Not financial advice. Paper trade first. Always.*
