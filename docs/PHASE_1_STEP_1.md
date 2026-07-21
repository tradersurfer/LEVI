# LEVI Phase 1, Step 1 — Foundation

This step adds the minimum user-specific foundation without changing LEVI's existing paper-trading, alert-mode, risk-moat, consensus, model-routing, or dashboard behavior.

## What was added

- A validated user trading profile in `levi/profiles/models.py`.
- Deterministic mode policies in `levi/modes/router.py`.
- Configurable, isolated user workspaces in `levi/workspace/initializer.py`.
- Vendor-neutral evidence models and an in-process registry in `levi/evidence/`.
- The pre-analysis `WhatYouNeed` gate in `levi/contracts/what_you_need.py`.
- `POST /api/what-you-need` in the existing FastAPI application at `bot/status_api.py`.

## Supported modes

| Mode | Instruments | Holding policy |
| --- | --- | --- |
| Day trading | Options, Polymarket | Intraday |
| Swing trading | Options, Polymarket | Multi-day to multi-week |
| Investing / holding | Stocks | Long term |

Paper trading is the default execution mode. Automatic live execution is not part of this contract.

## Profile validation

Every profile requires a user ID, display name, trading mode, instrument type, execution mode, and deterministic risk fields. Investing/holding accepts stocks only; options and Polymarket are rejected. Day and swing modes accept options or Polymarket. Loss and position limits are validated, and the public risk-per-trade default is 1%.

## User workspace

`LEVI_WORKSPACE_ROOT` controls the storage root and defaults to `./workspace` for development. Each user receives:

```text
users/{user_id}/
├── MEMORY.md
├── MOOD.md
├── BEHAVIOR.md
├── PROFILE.json
└── evidence/
```

The repository ignores the development workspace. Production deployments should set `LEVI_WORKSPACE_ROOT` to durable storage outside the application checkout. `PROFILE.json` contains only validated profile fields and no credential fields.

## Evidence contract

`EvidenceRecord` supports screenshots, CSV, Excel, PDF, tables, charts, graphs, broker statements, portfolio exports, options chains, trade journals, text notes, and live feeds. The registry supports registration, user/ticker/type/recent queries, warning listing, and ownership checks. `EvidenceParser` is the extension interface; parsing is intentionally not implemented in this step.

## API endpoint

`POST /api/what-you-need`

```json
{
  "user_id": "string",
  "request_type": "trade_analysis",
  "ticker": "SPY"
}
```

The endpoint loads the user's validated workspace profile, resolves the mode policy, inspects registered evidence, and reports required, optional, available, and missing inputs. Missing required inputs set `can_proceed` to `false`; optional inputs never block progress. This endpoint does not launch analysis or specialist agents.

## Known exclusions

Authentication, Supabase, broker integrations or changes, live feeds, OCR and file parsing, mobile/PWA packaging, dashboard redesign, model or routing changes, fine-tuning, new strategies, and automated or Polymarket execution are excluded.

## Next step

After approval of this foundation, Phase 1, Step 2 should connect the evidence ingestion lifecycle to durable storage and parser implementations while preserving the contracts introduced here.
