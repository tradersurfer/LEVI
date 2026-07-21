# LEVI Phase 4 — Specialist Agent Network Implementation Report

## Summary

Added six bounded specialists, canonical decision and consensus contracts, an injectable OpenRouter JSON adapter with offline mock, deterministic Black–Scholes analytics, and fail-closed Guardian rules. Legacy bot behavior remains unchanged and no execution path was connected.

## Starting Commit

`5d60dd9` — approved main containing Phases 1 through 3.

## Branch and Commit

Branch: `phase-4-specialist-agents`. Final commit is recorded in the completion handoff. The branch remains local and unpushed.

## Files Created

Canonical modules under `levi/agents`, `levi/llm`, `levi/greeks`, and `levi/risk`; four prompt resources; nine Phase 4 test modules plus a test helper; `docs/PHASE_4_SPECIALIST_AGENTS.md`; and this report.

## Files Modified

`.env.example` only. Existing root `agents/` and `bot/consensus_engine.py` were not rewritten.

## Models Configured

SCOUT, ATLAS, LENS, and SCRIBE model IDs are environment-configured with no hardcoded changing model identifier. OpenRouter has a 30-second default timeout and one bounded retry. No real key is committed.

## Deterministic Components

VOLT calculates call/put value, delta, gamma, daily theta, vega, rho, intrinsic/extrinsic value, moneyness, break-even, and spread/liquidity diagnostics. GUARDIAN enforces paper mode, minimum DTE, risk and loss limits, position concentration, no averaging down, LIMIT-only orders, valid/fresh quotes, supported profile combinations, buying power, and approval references.

## Consensus Behavior

Approval requires unanimous matching bullish or bearish SCOUT/ATLAS/LENS verdicts at or above 0.70 and an allowed Guardian result. Neutral, insufficient, block, missing, malformed, timeout, low-confidence, ownership mismatch, and 2-to-1 decisions fail closed. Guardian veto overrides unanimity.

## Tests

60 focused tests pass. The complete branch suite passes with 246 passed and 1 skipped (the existing Windows symlink capability skip), with three pre-existing FastAPI/Starlette deprecation warnings. Python compilation and whitespace validation pass.

## Blockers

No implementation blocker. Live OpenRouter verification was intentionally not performed and requires a user-provided key and selected model IDs.

## Assumptions

The canonical Phase 4 network is not wired into the legacy bot until an approved integration phase. Hosted agents analyze only pre-ingested evidence and do not fetch current data.

## Scope Exclusions

No live trading, order submission, direct data fetching, dashboard, authentication, persistence, model fine-tuning, or Phase 5–7 work was added to this branch.

## Git Diff Summary

New typed specialist, LLM, Greeks, risk, prompt, test, and documentation files plus Phase 4 environment placeholders.
