# LEVI v0.1.0-alpha Integration Report

## Summary

The integration branch verifies the seams between the Phase 4 specialist agents, Phase 5 dashboard, Phase 6 authentication and persistence, and Phase 7 release foundation. Contract drift and security gaps were corrected with scoped changes. Python and frontend regression suites pass. Docker verification remains blocked because Docker is not installed on this host.

## Branch and Starting Point

- Branch: `integration-v0.1.0-alpha`
- Starting commit: `7d74fb744c07936f88bda141ea8a506774edea45`
- `git pull --ff-only origin main`: not completed because the host could not connect to GitHub on port 443.
- The local branch was created from a clean `main` that tracked the locally recorded `origin/main` at `7d74fb7`.

## Job 1 — Phase 5 and Phase 4 Contract Verification

### Finding

The dashboard fixture and service expected `approve` verdict strings and reconstructed consensus locally. The real Phase 4 contract uses:

- `AgentDecision.decision_id`
- `AgentDecision.verdict` values: `bullish`, `bearish`, `neutral`, `block`, and `insufficient_evidence`
- `ConsensusDecision.approved` as the canonical approval result
- `ConsensusDecision.verdict` as the canonical consensus verdict

The prior dashboard heuristic did not match this contract.

### Fix

`DashboardService.decisions()` now accepts the real immutable dataclasses, converts their enums, timestamps, tuples, and mapping metadata into JSON-safe values, filters decisions by `user_id`, and consumes the real user-scoped `ConsensusDecision.approved` and `verdict`. It no longer reconstructs approval from invented vote strings.

### Verification

An integration test constructs real bearish `AgentDecision` objects for SCOUT, ATLAS, and LENS, evaluates them with the real `ConsensusEngine`, passes both real contracts through the dashboard service/API, and verifies `approved=true`, `decision="bearish"`, `decision_id`, and `verdict="bearish"` in the response.

## Job 2 — Phase 6 and Phase 5 Authentication Wiring

### Finding

Dashboard routes previously ignored `LEVI_AUTH_ENABLED`, never called `require_identity`, and always trusted the query-string `user_id`, even when authentication was enabled elsewhere in the application.

### Fix

A minimal conditional dashboard dependency now behaves as follows:

- `LEVI_AUTH_ENABLED=false`: preserves unauthenticated local single-user behavior.
- `LEVI_AUTH_ENABLED=true`: calls the existing fail-closed `require_identity` dependency and requires the authenticated identity's `user_id` to equal the requested `user_id`.
- Missing bearer credentials are rejected with 401 when the auth service is configured.
- Cross-user dashboard requests are rejected with 403.
- Missing auth-service configuration remains fail-closed through `require_identity` with 503.

The confirmed behavior and local-only limitation are documented in `docs/SECURITY.md`.

## Job 3 — Regression and Non-Blocking Fixes

### Quote Freshness

Guardian risk validation now uses the Phase 3 thresholds:

- Options: maximum age 3 seconds
- Other supported instruments: maximum age 15 seconds

A focused test confirms a four-second-old options quote is rejected.

### Audit Redaction

Audit sanitization now redacts `encryption_key` and every key ending in `_encryption_key`, including `LEVI_EVIDENCE_ENCRYPTION_KEY`. A persistence test verifies both forms are stored as `[REDACTED]`.

### Frontend Dependency Audit

Initial `npm audit` result:

- Package: `brace-expansion`
- Affected versions: `3.0.0 - 5.0.6`
- Severity: high
- Advisory: `GHSA-3jxr-9vmj-r5cp`
- Impact: denial of service through exponential-time expansion
- Fix: available through non-breaking `npm audit fix`

`npm audit fix` changed one transitive package in `dashboard/package-lock.json`. The final audit reports `found 0 vulnerabilities`. No major dependency upgrade was applied.

### Test Results

- Focused integration/security tests: `60 passed, 3 warnings`
- Full Python suite: `358 passed, 1 skipped, 3 warnings`
- Frontend tests: `18 passed, 0 failed`
- Frontend lint: passed
- Frontend production build: passed (`30 modules transformed`)
- Python compileall: passed
- `git diff --check`: passed

The Python warnings are the existing Starlette `httpx` deprecation and FastAPI `on_event` deprecations.

## Job 4 — Docker Execution

Docker verification could not be executed on this host.

Actual command attempted:

```text
docker version
docker compose version
```

Actual result for both commands:

```text
docker : The term 'docker' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

Consequently, these required operational checks remain unverified:

- `docker build -t levi:integration-test .`
- `docker compose -f docker-compose.yml up -d`
- `/health` and `/ready` responses from inside the running container
- effective container user is `levi`
- image contains no `.env`, `.git`, or workspace content

This was not skipped silently; Docker is unavailable in the execution environment.

## Files Changed

- `SECURITY.md`
- `docs/SECURITY.md`
- `dashboard/package-lock.json`
- `levi/dashboard/routes.py`
- `levi/dashboard/service.py`
- `levi/persistence/audit.py`
- `levi/risk/guardian_rules.py`
- `tests/test_dashboard_api.py`
- `tests/test_guardian_agent.py`
- `tests/test_persistence_repositories.py`
- `INTEGRATION_REPORT.md`

## Scope Confirmation

No new product feature, live trading path, model change, dashboard redesign, tag, GitHub release, or Phase 4+ sprint was started. The changes are limited to integration contract alignment, auth enforcement, security corrections, dependency remediation, tests, and documentation.

## Remaining Before v0.1.0-alpha Tagging

1. Run the required Docker build and compose verification on a Docker-capable host.
2. Verify container health/readiness, non-root execution, and image-content exclusions.
3. Review this integration commit.
4. Merge the reviewed integration branch to `main`.
5. Re-run release checks on merged `main` before creating the tag.

Do not tag or release until the Docker checks above have passed.
