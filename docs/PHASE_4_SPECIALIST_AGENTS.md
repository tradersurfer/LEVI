# LEVI Phase 4 — Specialist Agent Network

Phase 4 introduces canonical, immutable specialist contracts under `levi/agents`. It does not replace the legacy bot agents or connect consensus to execution.

## Contracts

`AgentAnalysisRequest` binds a user, symbol, trading mode, instrument, supplied Phase 1 evidence, optional Phase 3 quote, and portfolio context. Construction rejects evidence owned by another user. `AgentDecision` records a bounded verdict, confidence, reasoning, evidence IDs, warnings, timing, and metadata. `ConsensusDecision` is the stable output consumed by later API and dashboard integration.

## Specialists

- SCOUT analyzes only supplied sentiment, flow, news, or crowd-positioning evidence.
- ATLAS analyzes only supplied macro, rates, regime, volatility, or catalyst evidence.
- LENS analyzes only supplied chart evidence matching the requested ticker.
- VOLT performs deterministic Black–Scholes calculations and liquidity diagnostics.
- GUARDIAN applies deterministic paper-mode, DTE, loss, position, order, quote, buying-power, and approval rules.
- SCRIBE summarizes structured decisions without adding evidence or casting a vote.

Hosted specialists use the injected `LLMAdapter`. `OpenRouterAdapter` requires a configured model ID, requests structured JSON, uses bounded retries/timeouts, and fails safely. Tests use `MockLLMAdapter`; the default suite makes no network calls.

## Consensus

SCOUT, ATLAS, and LENS must return the same bullish or bearish verdict, each at or above `LEVI_CONSENSUS_MIN_CONFIDENCE` (default `0.70`). Missing, neutral, blocked, insufficient, malformed, low-confidence, ownership-mismatched, or 2-to-1 outcomes do not approve. GUARDIAN veto always wins. Consensus is deterministic except for generated identifiers/timestamps, which do not affect the result.

## VOLT conventions

Time is expressed in years using a 365-day convention. Theta is per calendar day; vega is per one volatility point; rho is per one rate point. Results are labeled `calculated_black_scholes` and are diagnostics, not broker-reported Greeks.

## Configuration

```dotenv
OPENROUTER_API_KEY=
LEVI_SCOUT_MODEL=
LEVI_ATLAS_MODEL=
LEVI_LENS_MODEL=
LEVI_SCRIBE_MODEL=
LEVI_LLM_TIMEOUT_SECONDS=30
LEVI_LLM_MAX_RETRIES=1
LEVI_CONSENSUS_MIN_CONFIDENCE=0.70
```

Model IDs are deliberately deployment configuration and are not hardcoded.

## Testing

Run the nine `test_*agent.py`, `test_consensus_engine.py`, `test_openrouter_adapter.py`, and `test_black_scholes.py` Phase 4 files, then `pytest tests -q`.

## Exclusions

No direct social/macro fetching, browsing, live trading, order submission, dashboard, authentication, database, fine-tuning, or cross-phase integration is included.
