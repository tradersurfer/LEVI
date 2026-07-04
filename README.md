# LEVI Options Intelligence Agent

LEVI is a white-label options intelligence and execution platform that combines deterministic market-state and risk controls with specialist research agents and unanimous AI consensus. Operator names, account mappings, tier limits, and model settings live in `levi_config.json` and environment variables, keeping credentials and customer-specific configuration out of the codebase. Paper mode and API-only operation are the safe defaults.

> **Paper mode is on by default.** Keep `TASTYTRADE_PAPER=true`, `AUTO_EXECUTE=false`, and `RUN_BOT=false` until the system has been validated with your own configuration.

## Architecture

| Stage | Component | Responsibility |
|---|---|---|
| 1 | Market State | Detects regimes such as `BULL_TRAP`, `WATERFALL`, and `V_BOTTOM` from market data. |
| 2 | Risk Moat | Enforces position size, DTE, RSI, and state locks in Python before any model or execution call. |
| 3 | SCOUT / ATLAS / LENS | Adds sentiment, macro-regime, catalyst, and setup-quality context. |
| 4 | Consensus | Requires a 3/3 unanimous vote from Grok, Claude, and DeepSeek R1. |
| 5 | Execution | Routes approved trades as limit orders through the configured paper or live account. |

## Specialist Agents

| Agent | Role |
|---|---|
| SCOUT | Scans social sentiment and signal velocity. |
| ATLAS | Classifies the macro regime, trade bias, and upcoming catalysts. |
| LENS | Evaluates technical setup quality and decides whether deeper verification is needed. |
| TRACE | Performs focused evidence verification when LENS triggers it. |

## Consensus Network

LEVI uses Grok for sentiment and momentum, Claude for technical reasoning, and DeepSeek R1 as the final risk officer. A trade must pass the programmatic Risk Moat first and then receive a 3/3 unanimous consensus. Missing keys, failed responses, or any veto prevent execution.

## Quick Start

```bash
git clone <your-repository-url>
cd jeci-trading-suite

# Customize operator, tiers, and limits.
$EDITOR levi_config.json

# Create a local secrets file and fill in your own values.
cp .env.example .env

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q

# Deploy after authenticating the Railway CLI.
railway up
```

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `TASTYTRADE_PAPER` | `true` | Uses the paper-trading API when true. |
| `AUTO_EXECUTE` | `false` | Allows automatic order routing when explicitly enabled. |
| `CONSENSUS_REQUIRED` | `true` | Requires unanimous model consensus. |
| `RUN_BOT` | `false` | Starts the scan loop inside the API service when enabled. |
| `TT_USERNAME` | none | Broker username. |
| `TT_PASSWORD` | none | Broker password. |
| `ACCT_CORE` | none | Core tier account number. |
| `ACCT_SANDBOX` | none | Sandbox tier account number. |
| `ACCT_HODL` | none | Alerts-only tier account number. |
| `XAI_API_KEY` | none | Grok API credential. |
| `ANTHROPIC_API_KEY` | none | Claude API credential. |
| `DEEPSEEK_API_KEY` | none | OpenRouter credential for DeepSeek R1. |
| `PERPLEXITY_API_KEY` | none | Live-data verification credential used by specialist agents. |
| `GROK_MODEL` | `grok-4` | Grok model override. |
| `CLAUDE_MODEL` | `claude-sonnet-4-5` | Claude model override. |
| `DEEPSEEK_MODEL` | `deepseek/deepseek-r1` | DeepSeek model override. |
| `PERPLEXITY_MODEL` | `llama-3.1-sonar-large-128k-online` | Verification model override. |
| `AGENT_TIMEOUT_SEC` | `25` | Agent request timeout in seconds. |
| `LEVI_CONFIG_PATH` | `./levi_config.json` | White-label configuration path. |
| `PORT` | `8000` | FastAPI service port. |

## Non-Negotiables

- Limit orders only.
- No averaging down; stopped-out symbols are blocklisted for the session.
- Four DTE minimum for options entries.
- HODL is equity-alerts-only and never routes options orders.
- The Risk Moat runs before model consensus or execution.

## Run Locally

```bash
uvicorn bot.status_api:app --reload
```

The API starts without the trading loop unless `RUN_BOT=true` is explicitly set.
