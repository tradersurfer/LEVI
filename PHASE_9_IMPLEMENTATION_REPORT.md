# LEVI Phase 9 — Agent Activity Implementation Report

## Summary

Phase 9 completes the agent activity path from the real backend pipeline to a designed dashboard page. VOLT now emits deterministic informational diagnostics between LENS and GUARDIAN, final consensus events preserve approval and GUARDIAN blocking independently, one adapter owns all wire-to-view translation, SCRIBE is shown after the risk gate as the outcome narrative, and `/agent-activity` renders the live stream rather than raw event JSON.

## Starting Commit and Branch

- Starting branch: `phase-8-agent-streaming`
- Starting commit: `0d34b8ced64707f8ffa888e58dd1ce9def33aa67`
- Implementation branch: `phase-9-agent-activity`
- Commit message: `feat: ship Phase 9 agent activity — VOLT integration, SCRIBE repositioning, live stream wiring`
- Commit SHA: reported in the completion handoff after the single commit is created

## Pre-Work Reconciliation Findings

### 1. VOLT backend status

Confirmed missing. `levi/streaming/events.py` omitted `VOLT` from `_AGENT_NAMES`, and `PipelineRunner` constructed only SCOUT, ATLAS, and LENS. Phase 4 `VoltAgent` accepts `BlackScholesInputs` and returns a deterministic `BlackScholesResult`; it does not accept `AgentAnalysisRequest` or return `AgentDecision`.

Resolution: preserve the Phase 4 VOLT API, extract complete Black–Scholes inputs only from user-owned evidence, call the real `VoltAgent`, and wrap its result as an informational, non-voting `AgentDecision`. Missing or invalid inputs produce `insufficient_evidence`; no market values are invented.

### 2. SCRIBE execution order

Confirmed correct in the backend and unchanged:

`SCOUT → ATLAS → LENS → VOLT → GUARDIAN → consensus.evaluate() → SCRIBE.summarize() → final CONSENSUS event`

SCRIBE requires completed specialist decisions and the real `ConsensusDecision`, so it remains post-consensus evaluation. The frontend was corrected to place SCRIBE after `GuardianGate` and directly before `ConsensusBanner` as the closing outcome narrative.

### 3. Frontend conventions and asset path

- The real frontend is `dashboard/`; no parallel `frontend/` directory was created.
- Dashboard uses JavaScript/JSX. It has no `tsconfig`, TypeScript source, or TSX Vite configuration. The supplied design was integrated as `.js` and `.jsx`; no TypeScript tooling was added.
- The canonical mascot existed at `docs/assets/levi-avatar.svg`. Because Vite serves dashboard assets from `dashboard/public`, it was copied to `dashboard/public/assets/levi-avatar.svg` and is referenced as `/assets/levi-avatar.svg`.

## Files Created

- `dashboard/public/assets/levi-avatar.svg`
- `dashboard/src/components/agent-activity/AgentActivityEmptyState.jsx`
- `dashboard/src/components/agent-activity/AgentActivityErrorState.jsx`
- `dashboard/src/components/agent-activity/AgentActivityPanel.jsx`
- `dashboard/src/components/agent-activity/AgentNode.jsx`
- `dashboard/src/components/agent-activity/ConsensusBanner.jsx`
- `dashboard/src/components/agent-activity/GuardianGate.jsx`
- `dashboard/src/components/agent-activity/VotingCluster.jsx`
- `dashboard/src/components/agent-activity/agentActivity.css`
- `dashboard/src/components/agent-activity/agentActivity.types.js`
- `dashboard/src/components/agent-activity/agentActivity.utils.js`
- `dashboard/src/components/agent-activity/index.js`
- `dashboard/src/lib/agentActivityAdapter.js`
- `dashboard/src/lib/agentActivityConnection.js`
- `dashboard/tests/agent-activity.test.js`
- `tests/test_phase_9_agent_activity.py`
- `PHASE_9_IMPLEMENTATION_REPORT.md`

## Files Modified

- `levi/streaming/events.py`
- `levi/streaming/runner.py`
- `dashboard/src/dev/AgentStreamPreview.jsx`
- `dashboard/src/main.jsx`
- `bot/status_api.py`
- `dashboard/src/components/agent-activity/AgentActivityPanel.jsx`

No `/api/dashboard/*` route, authentication service, persistence module, broker code, execution code, or live-trading code changed.

## VOLT Integration

- `VOLT` is a valid streaming agent name.
- It emits `queued`, `running`, and `complete` after LENS and before GUARDIAN.
- Complete Black–Scholes values are accepted from evidence metadata, parsed payload, or a nested `black_scholes_inputs` object.
- DTE is converted using the existing 365-day convention only when explicitly supplied.
- Missing values fail safely as insufficient evidence.
- `ConsensusEngine.required` remains exactly `("SCOUT", "ATLAS", "LENS")`; VOLT cannot affect approval.

## Final Consensus Event

The final event is constructed directly from the real `ConsensusDecision`:

```python
await emit(
    "CONSENSUS",
    AgentStatus.COMPLETE if consensus.approved else AgentStatus.BLOCKED,
    verdict=consensus.verdict,
    confidence=consensus.confidence,
    summary="Consensus approved" if consensus.approved else "; ".join(consensus.warnings),
    approved=consensus.approved,
    guardian_blocked=consensus.guardian_blocked,
)
```

`approved` and `guardian_blocked` are distinct nullable boolean fields in `AgentProgressEvent` and distinct keys in the WebSocket payload. Neither is reconstructed from `status` by the frontend.

## Exact Adapter Mapping

All status translation exists in the named export `mapConsensusStatus`:

```javascript
export function mapConsensusStatus(payload = {}) {
  if (payload.guardian_blocked === true) return 'blocked'
  if (payload.approved === true) return 'approved'
  if (payload.connectionError === true || payload.status === 'error') return 'error'

  const agents = Array.isArray(payload.agents) ? payload.agents : []
  const hasRun = Boolean(payload.request_id || payload.requestId)
  if (!hasRun && agents.length === 0) return 'idle'

  const byName = new Map(agents.map((agent) => [agent.agentName, agent]))
  const allComplete = AGENT_NAMES.every((name) => TERMINAL_STATUSES.has(byName.get(name)?.status))
  if (allComplete) return 'not_approved'
  if (hasRun || agents.some((agent) => ['queued', 'running'].includes(agent.status))) return 'pending'
  return 'idle'
}
```

No component contains a second consensus heuristic.

## Critical GUARDIAN Precedence Test

The required payload was tested with `approved: false` and `guardian_blocked: true`. `mapConsensusStatus` returned `blocked`, not `not_approved`. The backend wire test also confirmed the final blocked payload contains both `approved: false` and `guardian_blocked: true` independently.

## Live Page Wiring

- `/agent-activity` renders the designed activity panel in production and development builds.
- The former raw-event preview now opens the user-scoped WebSocket, triggers `POST /api/agents/analyze`, sends each event through `applyAgentProgressEvent`, and renders `AgentActivityPanel`.
- The page retains `/dev/agent-stream` as a development-only compatibility path.
- Optional bearer authorization is applied to the HTTP trigger through `VITE_LEVI_ACCESS_TOKEN` when supplied.
- `GET /api/config` exposes only the non-secret `auth_enabled` runtime capability.
- When authentication is enabled, the page does not attempt the unsupported browser WebSocket and renders: "Live agent streaming requires authenticated WebSockets, which aren't supported yet. Disable authentication for local paper trading, or check back for browser-compatible auth support."
- Ordinary configuration, network, and WebSocket failures retain the distinct generic connection-error message.
- No raw event `<pre>` remains.

## Tests Executed

- Phase 8 plus Phase 9 focused backend suite
- New Phase 9 backend tests
- New adapter/design tests
- Complete Python repository suite
- Complete dashboard Node suite
- Dashboard ESLint
- Dashboard production build
- Python compile check
- Git whitespace check

## Test Results

- Focused backend suite: `45 passed`
- New Phase 9 tests: `9 Python + 17 JavaScript = 26`
- Dashboard suite: `35 passed`, including all existing Phase 5 tests
- Dashboard lint: passed
- Dashboard production build: passed
- Local Python regression excluding only the ignored developer `.env` audit: `403 passed, 1 skipped, 1 deselected`
- Final clean-worktree full Python suite: `404 passed, 1 skipped`

## Blockers

Browser WebSocket clients cannot attach an `Authorization` header, while the existing authenticated WebSocket endpoint accepts only that header through `require_identity`. Default `LEVI_AUTH_ENABLED=false` operation is fully wired. Auth-enabled browser streaming requires a separately approved cookie or WebSocket subprotocol authentication design. The page now detects this runtime mode before connecting and displays a specific explanation; it does not hang, show a generic error, or weaken authentication by putting bearer tokens in URLs.

The local checkout also contains an ignored `.env`, which Phase 7’s strict release audit correctly flags. Final full-suite verification is run from a clean detached worktree rather than deleting the user’s environment file or weakening the audit.

## Assumptions

- A deterministic VOLT diagnostic may be represented as neutral informational output without becoming a directional vote.
- Evidence is the only permitted source for option inputs.
- The existing browser-auth transport limitation is preferable to an insecure query-token workaround.

## Scope Exclusions Confirmed

- No TypeScript toolchain
- No event persistence or replay
- No new LLM providers
- No dashboard API route changes
- No authentication-service changes
- No live execution or broker changes
- No merge or push
- No further phase started

## Git Diff Summary

The final diff is limited to VOLT/event-field backend corrections, supplied agent-activity components, the single adapter, live activity-page wiring, the dashboard-served mascot, focused tests, and this report.

## Recommended Next Action

Review the final WebSocket payload and designed `/agent-activity` page. Separately scope authenticated browser WebSocket transport before enabling this page in an authenticated public deployment.
