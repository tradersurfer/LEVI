# LEVI Phase 8 — Live Agent Activity Streaming Implementation Report

## Summary

Phase 8 adds a minimum backend wire protocol for starting the existing LEVI specialist pipeline and observing its progress over a user-scoped WebSocket. It reuses the canonical Phase 4 agent decisions, GUARDIAN rules, consensus engine, Phase 1 evidence registry, Phase 5 authentication toggle, and existing FastAPI application.

## Starting Commit

`45139d9e7010fa93e4023f1de7b404633077987b` — `docs: README restructure, install hardening, Apache 2.0 license, repo cleanup`

## Branch and Commit

- Branch: `phase-8-agent-streaming`
- Commit message: `feat: ship Phase 8 live agent activity streaming (backend)`
- Commit SHA: reported at handoff after the single commit is created

## Files Created

- `levi/streaming/__init__.py`
- `levi/streaming/events.py`
- `levi/streaming/bus.py`
- `levi/streaming/runner.py`
- `levi/streaming/routes.py`
- `dashboard/src/dev/AgentStreamPreview.jsx`
- `tests/streaming_helpers.py`
- `tests/test_streaming_events.py`
- `tests/test_streaming_bus.py`
- `tests/test_agent_runner.py`
- `tests/test_analyze_endpoint.py`
- `tests/test_ws_agents_stream.py`
- `PHASE_8_IMPLEMENTATION_REPORT.md`

## Files Modified

- `bot/status_api.py`
- `dashboard/src/main.jsx`
- `tests/test_phase_7_release_engineering.py`

The Phase 7 documentation inventory test was aligned with the public documentation layout already committed in the Phase 8 base commit. No Phase 7 runtime behavior changed.

## Event Contract and Bus

- `AgentProgressEvent` is immutable, validates identity, sequence, timezone, confidence, symbol, and supported agent names, and reuses `AgentVerdict`.
- `EventBus` maintains an in-process set of `asyncio.Queue` subscribers per `user_id`.
- Events are delivered only to current subscribers for the owning user.
- Events published without a subscriber are deliberately dropped without error.
- The bus is non-durable. Restarts, disconnects, and periods without a subscriber lose events by design in this phase.

## Pipeline Runner

- Loads only evidence owned by the requesting user through `EvidenceRegistry.by_user`.
- Builds the canonical `AgentAnalysisRequest` from the validated user profile.
- Calls the real SCOUT, ATLAS, and LENS implementations.
- Evaluates the real deterministic GUARDIAN rules.
- Publishes the real `ConsensusDecision`; the final event is not reconstructed from vote counts.
- Calls the existing SCRIBE narrative contract after consensus evaluation because Phase 4 SCRIBE requires completed decisions and a completed `ConsensusDecision`.
- Uses `OpenRouterAdapter` only when the API key and all specialist model variables are configured.
- Otherwise reuses `MockLLMAdapter` with a deterministic, fail-safe insufficient-evidence response.
- Rejects a second active run for the same user with HTTP 409 while allowing different users to run concurrently.
- Default risk construction fails closed because this phase accepts no trade proposal, quote, limit price, or approval reference.

## API and WebSocket Integration

- `POST /api/agents/analyze` validates the profile and returns HTTP 202 with `{ "request_id": "..." }` immediately.
- `WS /ws/agents?user_id=...` streams JSON-safe `AgentProgressEvent` payloads.
- Both endpoints are permissive when `LEVI_AUTH_ENABLED=false`, matching the existing local dashboard behavior.
- When authentication is enabled, the authenticated identity must match the requested `user_id`; mismatches fail with HTTP 403.
- The existing FastAPI application is reused; no parallel application was created.

## Disposable Preview

- `/dev/agent-stream` is rendered only by Vite development builds.
- It is not linked from the production dashboard navigation.
- It opens the WebSocket before triggering analysis and renders raw event JSON only.
- Its source is explicitly marked disposable for replacement by a later design pass.

## Tests Executed

- Focused Phase 8 Python suite: 37 tests
- Complete Python repository suite
- Dashboard Node tests
- Dashboard ESLint
- Dashboard production build
- Python compile check
- Git whitespace check

## Test Results

- Focused Phase 8 suite: `37 passed`
- Dashboard tests: `18 passed`
- Dashboard lint: passed
- Dashboard production build: passed
- Full Python suite from a clean detached worktree: `395 passed, 1 skipped` (`396 collected`)

## Security and Isolation Checks

- Cross-user bus delivery is rejected by subscription scope.
- Evidence selection is user-scoped through the canonical registry.
- HTTP and WebSocket identity mismatch behavior is tested with authentication enabled.
- Safe errors expose exception type only, not exception text or local details.
- Symbols are bounded and validated before a task starts.
- The API never exposes evidence storage locations, credentials, or tokens.

## Blockers

No Phase 8 implementation blocker remains.

The local developer checkout contains an ignored `.env`, which the Phase 7 release audit correctly flags. Final full-suite verification is therefore run from a clean Git worktree rather than weakening the audit or deleting the user's local environment file.

## Assumptions

- Phase 4 SCRIBE remains a post-consensus narrator; changing it into a pre-analysis agent would redesign its existing contract.
- No quote or proposed order is accepted by the new trigger endpoint, so the default GUARDIAN request must fail closed.
- In-process task and event state is sufficient for the explicitly non-durable scope.

## Scope Exclusions Confirmed

- No production dashboard design work
- No event persistence or replay
- No database changes
- No new LLM provider
- No model-routing changes
- No live execution or order submission
- No changes to existing dashboard routes
- No merge or push

## Git Diff Summary

The final diff contains 16 files with only the streaming backend, existing-app route registration, disposable dev preview, focused tests, the base-commit documentation inventory correction, and this report.

## Recommended Next Action

Review the backend event contract and WebSocket behavior. After approval, push the branch and open a review without beginning production visual design or a later phase.
