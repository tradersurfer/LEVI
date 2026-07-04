<p align="center">

```
██╗     ███████╗██╗   ██╗██╗
██║     ██╔════╝██║   ██║██║
██║     █████╗  ██║   ██║██║
██║     ██╔══╝  ╚██╗ ██╔╝██║
███████╗███████╗ ╚████╔╝ ██║
╚══════╝╚══════╝  ╚═══╝  ╚═╝

AI Options Intelligence Engine
```

</p>

<p align="center">
<i>Deterministic risk engine • Multi-agent research • AI consensus execution</i>
</p>

<p align="center">
<img src="https://img.shields.io/badge/Built%20by-JECI%20AI-1B365D?style=flat-square">
<img src="https://img.shields.io/badge/Status-Production-success?style=flat-square">
<img src="https://img.shields.io/badge/Paper%20Trading-Default-orange?style=flat-square">
<img src="https://img.shields.io/badge/Consensus-3%2F3-blue?style=flat-square">
<img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square">
</p>

---

# LEVI

**LEVI** is a deterministic options intelligence and execution engine built around one principle:

> **Risk is decided before intelligence.**

Every trade passes through a hardcoded market-state engine and a deterministic risk layer before a single LLM is asked for an opinion.

If Grok, Claude, and DeepSeek R1 do not unanimously agree, **the trade simply does not exist.**

No consensus.

No execution.

No exceptions.

---

## Philosophy

```
Deterministic Logic
        ↓
Risk Controls
        ↓
Specialist Research
        ↓
AI Consensus
        ↓
Execution
```

Models never control risk.

Models only provide evidence.

Python owns execution.

---

# Architecture

```text
             SPY / Options Data
                     │
                     ▼
┌────────────────────────────────────────────┐
│ MARKET STATE ENGINE                        │
│ Bull Trap • Waterfall • V Bottom           │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────┐
│ RISK MOAT                                 │
│ Position sizing                           │
│ DTE validation                            │
│ RSI locks                                 │
│ Symbol cooldowns                          │
│ Hardcoded Python only                     │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────┐
│ SPECIALIST AGENTS                          │
│                                            │
│ SCOUT                                      │
│ ATLAS                                      │
│ LENS                                       │
│ TRACE (conditional)                        │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────┐
│ CONSENSUS NETWORK                          │
│                                            │
│ Grok                                       │
│ Claude                                     │
│ DeepSeek R1                               │
│                                            │
│ 3 / 3 REQUIRED                             │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────┐
│ LIMIT ORDER EXECUTION                      │
└────────────────────────────────────────────┘
```

---

# Specialist Agents

| Agent | Responsibility |
|-------|----------------|
| **SCOUT** | Social sentiment, options flow, momentum |
| **ATLAS** | Macro environment and catalyst analysis |
| **LENS** | Technical structure and setup quality |
| **TRACE** | Deep verification when confidence is insufficient |

---

# Consensus Layer

Three independent reasoning systems evaluate every candidate.

| Model | Responsibility |
|--------|----------------|
| **Grok** | Market sentiment |
| **Claude** | Technical reasoning |
| **DeepSeek R1** | Risk validation |

Any disagreement immediately cancels execution.

```
1 Yes
1 No

Result:
NO TRADE
```

Failure is considered a valid trading decision.

---

# Risk Engine

These rules cannot be overridden.

| Rule | Enforcement |
|------|-------------|
| Market Orders | Never |
| Minimum DTE | 4 Days |
| Averaging Down | Disabled |
| Session Blocklist | Enabled |
| Consensus | Mandatory |
| Paper Mode | Default |

The AI does not vote on these.

Python enforces them.

---

# Account Tiers

| Tier | Purpose |
|------|---------|
| Core | Full execution |
| Sandbox | Validation & testing |
| HODL | Alerts only |

Everything is configured through

```
levi_config.json
```

No customer configuration lives inside the application.

---

# Configuration

```
.env
```

contains credentials.

```
levi_config.json
```

contains

- Operator branding
- Account mappings
- Watchlists
- Position limits
- Feature flags

The code never changes between operators.

---

# Setup

```bash
git clone https://github.com/tradersurfer/LEVI
cd LEVI

python -m venv .venv

source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt

pytest

uvicorn bot.status_api:app --reload
```

Paper mode remains enabled until explicitly disabled.

---

# Deployment

```bash
railway login
railway init
railway up
```

Production credentials should only exist as Railway Secrets.

Never commit `.env`.

---

# Project Stack

```
LEVI
├── Market State Engine
├── Risk Moat
├── Specialist Agents
├── Consensus Network
└── Execution Engine
```

Part of the **JECI Group AI Infrastructure**.

### Related Projects

- **Agent JECI** → Executive orchestration layer
- **BIB Marketplace** → White-label deployment platform
- **DeepSeek Multi-Turn** → Structured reasoning framework

---

> **"Markets reward discipline more than intelligence. LEVI is designed so discipline happens first."**

**Paper trade first. Not financial advice.**