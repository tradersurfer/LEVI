# LEVI Phase 5 — Trading Dashboard

Phase 5 extends the existing Vite/React dashboard and FastAPI application with a minimum shippable, read-only trading workspace. It does not add authentication, persistence, agent execution, credential storage, or trading behavior.

## Architecture

The existing `dashboard/` Vite application contains six focused views: `StatePanel`, `TradeJournal`, `SpecialistPanel`, `EvidenceViewer`, `SetupWizard`, and `Alerts`. Reusable `PositionTable`, `ConsensusCard`, `LoadingState`, `EmptyState`, and `ErrorState` components make positions and user-facing states explicit. `dashboard/src/api/client.js` requests seven user-scoped projections from the existing FastAPI app. If the local API is unavailable, the UI displays clearly labeled fixture data rather than inventing live state.

Typed response contracts, projections, and routes live in `levi/dashboard/models.py`, `levi/dashboard/service.py`, and `levi/dashboard/routes.py`. They read existing profile, evidence-registry, and in-process bot state. They do not query a database or mutate broker, risk, agent, or execution state.

## API

All routes require a `user_id` query parameter and return 404 when its workspace profile is absent:

- `GET /api/dashboard/summary`
- `GET /api/dashboard/positions`
- `GET /api/dashboard/trades`
- `GET /api/dashboard/evidence`
- `GET /api/dashboard/decisions`
- `GET /api/dashboard/alerts`
- `GET /api/dashboard/setup-status`

Evidence responses deliberately omit encrypted storage locations. Cross-user records are filtered. Setup status reports only whether profile, paper-broker name, and evidence source are configured; it never accepts or returns broker credentials.

## Decision compatibility

Decision fixtures use the fields `agent_name`, `verdict`, `confidence`, and `rationale`. Consensus uses `decision`, `approved`, `votes_required`, and `votes_received`. These shapes are compatible integration seams for Phase 4 contracts, but Phase 5 does not import Phase 4 or implement specialist logic.

## Development

```bash
uvicorn bot.status_api:app --reload
cd dashboard
npm run dev
```

Set `VITE_API_URL` to override `http://localhost:8000` and `VITE_LEVI_USER_ID` to select an installed local user. Run frontend verification with `npm test`, `npm run lint`, and `npm run build`. Run backend tests with `pytest tests/test_dashboard_api.py -q` and the complete suite with `pytest tests -q`.

## Responsive behavior and accessibility

The desktop layout uses a twelve-column grid, collapses panels below 900px, and uses single-column metrics below 600px. Panels use labelled headings and native sections, lists, buttons, and status text. Color is supported by textual state labels.

## Known exclusions

No authentication, database, WebSocket, dashboard-side uploads, broker credential persistence, agent logic, market-data fetch, order submission, automatic execution, or live trading was added. Real-time streaming and durable journal storage require separately approved work.
