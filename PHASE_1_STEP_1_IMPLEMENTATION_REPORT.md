# Phase 1, Step 1 Implementation Report

## Summary

Implemented the five approved foundations: validated user trading profiles, deterministic mode routing, isolated user workspace initialization, a vendor-neutral evidence contract and registry, and the pre-analysis `What You Need` contract. Added `POST /api/what-you-need` to the existing FastAPI application without changing LEVI's paper-trading, alert-mode, deterministic risk, execution, specialist-agent, model-routing, or dashboard behavior.

## Files created

- `levi/__init__.py`
- `levi/profiles/__init__.py`
- `levi/profiles/models.py`
- `levi/modes/__init__.py`
- `levi/modes/router.py`
- `levi/workspace/__init__.py`
- `levi/workspace/initializer.py`
- `levi/evidence/__init__.py`
- `levi/evidence/models.py`
- `levi/evidence/registry.py`
- `levi/contracts/__init__.py`
- `levi/contracts/what_you_need.py`
- `tests/test_phase_1_step_1.py`
- `docs/PHASE_1_STEP_1.md`
- `PHASE_1_STEP_1_IMPLEMENTATION_REPORT.md`

## Files modified

- `.env.example` — added only the three approved LEVI workspace/default-mode values.
- `.gitignore` — excluded the development `workspace/` directory.
- `README.md` — added a link to the phase document.
- `bot/status_api.py` — added the request model, evidence registry, and `POST /api/what-you-need` route.
- `requirements.txt` — made the Pydantic dependency explicit.
- `tests/test_levi_integration.py` — replaced a fixed, expired mock option date with a deterministic future date.

## Tests and checks run

1. `uv run --with-requirements requirements.txt python -m pytest tests/test_phase_1_step_1.py -q`
   - Result: 11 passed.
2. `uv run --with-requirements requirements.txt python -m pytest tests -q`
   - Final result: 31 passed.
3. `uv run --with-requirements requirements.txt python -m compileall -q levi bot`
   - Result: passed.
4. FastAPI import/route assertion for `POST /api/what-you-need`
   - Result: passed.
5. `git diff --check`
   - Result: passed.

## Test note

The first full-suite run found one stale existing fixture: `tests/test_levi_integration.py` used a fixed July 19, 2026 option expiration, which was expired when the suite ran on July 20, 2026. The fixture now generates an expiration 21 days from the test date. Runtime trading behavior was not changed.

## Blockers

None.

## Assumptions

- A validated profile stored at `${LEVI_WORKSPACE_ROOT}/users/{user_id}/PROFILE.json` is the current user-profile source for this step because authentication and database integration are explicitly excluded.
- The evidence registry is intentionally in-process for this contract-first step; durable evidence persistence and parsers belong to the next approved step.
- Non-negative account value and buying power in the validated profile count as available profile evidence. Market and chart evidence must still come from registered, traceable evidence records.
- User IDs are path-safe identifiers and may not contain path separators.
- No user workspace is initialized implicitly by the API; installation/onboarding code must explicitly call the initializer.

## Git diff summary

The implementation adds the isolated `levi/` package, one focused test module, one phase document, and this report. Existing runtime changes are limited to the single FastAPI endpoint and explicit Pydantic dependency. Configuration changes are limited to the three approved environment defaults and ignoring local workspace data. No trading, alert, risk, execution, agent, model-routing, or dashboard source file was changed.

## Exact next recommended step

Stop after this commit. After review and explicit approval, begin Phase 1, Step 2 by connecting the evidence ingestion lifecycle to durable storage and implementing the separately approved parser scope against the contracts shipped here.
