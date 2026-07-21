# LEVI Phase 2A — Evidence Ingestion Implementation Report

## Summary

Implemented the minimum shippable evidence-ingestion pipeline on top of the canonical Phase 1 `EvidenceRecord`, `EvidenceRegistry`, workspace, `WhatYouNeed`, and FastAPI architecture. Approved image, CSV, Excel, and PDF uploads are validated, deterministically parsed, encrypted at rest by default, registered with user ownership, and returned as structured evidence usable by the existing pre-analysis gate.

## Starting Commit

- Latest approved main: `90408d4` — merge of Phase 1, Step 1.
- Verified Phase 1 implementation commit `165b0cb` is an ancestor of the starting main.
- Existing baseline: 31 tests passing.

## Branch and Commit

- Branch: `phase-2a-evidence-ingestion`
- Commit message: `feat: ship Phase 2A evidence ingestion`
- Final local SHA: repository `HEAD` after this report is committed; the exact SHA is included in the completion output.
- Push status: not pushed, per instruction.

## Files Created

- `levi/evidence/parsers/__init__.py`
- `levi/evidence/parsers/base.py`
- `levi/evidence/parsers/screenshot_parser.py`
- `levi/evidence/parsers/chart_parser.py`
- `levi/evidence/parsers/csv_parser.py`
- `levi/evidence/parsers/excel_parser.py`
- `levi/evidence/parsers/pdf_parser.py`
- `levi/evidence/storage/__init__.py`
- `levi/evidence/storage/base.py`
- `levi/evidence/storage/filesystem_storage.py`
- `levi/evidence/ingestion/__init__.py`
- `levi/evidence/ingestion/uploader.py`
- `tests/evidence_helpers.py`
- `tests/test_screenshot_parser.py`
- `tests/test_chart_parser.py`
- `tests/test_csv_parser.py`
- `tests/test_excel_parser.py`
- `tests/test_pdf_parser.py`
- `tests/test_evidence_storage.py`
- `tests/test_evidence_uploader.py`
- `docs/PHASE_2A_EVIDENCE_INGESTION.md`
- `PHASE_2A_IMPLEMENTATION_REPORT.md`

## Files Modified

- `.env.example`
- `requirements.txt`
- `levi/evidence/models.py`
- `levi/evidence/__init__.py`
- `levi/contracts/what_you_need.py`
- `bot/status_api.py`

No trading loop, deterministic risk, specialist-agent, model-routing, broker, execution, or dashboard source file was changed.

## Dependencies Added or Changed

- `cryptography` (resolved locally as 49.0.0): AES-256-GCM authenticated encryption.
- `Pillow` (12.3.0): safe image validation, dimensions, format, and mode metadata.
- `openpyxl` (3.1.5): `.xlsx` reading without formula evaluation or external-link retention.
- `xlrd` (2.0.2): legacy `.xls` reading; `.xlsm` remains unsupported.
- `pypdf` (6.14.2): bounded extraction from unencrypted text PDFs.
- `python-multipart` (0.0.32): FastAPI multipart upload handling.

No OCR, hosted vision, model, market-data, database, or storage-service dependency was added.

## Parser Coverage

- Screenshot: PNG/JPEG/WebP validation, image dimensions/basic metadata, ticker/timeframe/ISO timestamp extraction when text is supplied by the vision boundary, source/account metadata preservation, and explicit no-provider warning.
- Chart: screenshot reuse, ticker/timeframe and descriptive chart fields, allowed trend normalization, confidence warning, and removal of recommendation/entry/stop/target/probability fields.
- CSV: UTF-8/BOM, safe delimiter detection, row/column/size limits, normalized columns, preserved rows, conservative timestamps and tickers, and signature-based options-chain/portfolio/journal/statement/generic detection.
- Excel: `.xlsx` and `.xls`, multiple sheets, sheet-origin preservation, hidden/empty-sheet warnings, bounded rows/columns, signature detection, tickers/timestamps, and no formula/macro/link execution.
- PDF: bounded text extraction and page references, tickers, page count, document-type detection, image-only warnings, and safe rejection of encrypted/password-protected, oversized, excessive-page, or invalid files.

All parser output uses the shared immutable Phase 2A `ParsedEvidence` extension while `EvidenceRecord` remains canonical.

## Encryption and User Isolation

- Original bytes are encrypted with AES-256-GCM using random 96-bit nonces and user/evidence identity as authenticated associated data.
- A URL-safe base64 32-byte key is required through `LEVI_EVIDENCE_ENCRYPTION_KEY`; missing/invalid keys fail closed.
- Plaintext exists only behind explicit `LEVI_ALLOW_PLAINTEXT_EVIDENCE=true`; default is false.
- Stored filenames are generated from evidence IDs.
- SHA-256 is calculated over original plaintext and recorded.
- Traversal, Windows drive/absolute names, null bytes, symbolic-link storage escapes, source symlinks, cross-user lookup, duplicate stored IDs, and user-controlled storage names are rejected.
- Keys are never logged, returned, stored in profiles, or included in reports/exceptions.
- Registry failure rolls stored data back; storage failure prevents registration.

## API Integration

Added `POST /api/evidence/upload` to `bot/status_api.py`, the existing FastAPI application. It accepts the approved multipart fields, verifies that the Phase 1 user profile exists, bounds temporary upload size, invokes the ingestion service, deletes API-owned temporary files, and returns HTTP 201 without exposing storage paths.

Status handling implements 400 malformed input, 404 missing workspace/profile, 413 size violation, 415 unsupported media, 422 parser validation, and a safe 500 response without keys, local paths, or public stack traces.

## What You Need Integration

- Ticker-sensitive chart, options-chain, and live-feed evidence must match the requested ticker.
- Chart timeframes satisfy only the matching requirement.
- Options chains require detected `EvidenceType.OPTIONS_CHAIN`; generic screenshots cannot claim strict structured evidence through metadata.
- Evidence below the configurable 0.70 threshold is shown as low-confidence context and remains missing for strict gating.
- Live-feed current spot/timestamp evidence older than 15 minutes is stale and does not satisfy the gate.
- Portfolio exports, broker statements, trade journals, and confidently typed PDF reports retain their detected canonical evidence types.
- No market-data fetching or analysis was added.

## Tests Executed

Focused command:

```text
uv run --with-requirements requirements.txt python -m pytest tests/test_screenshot_parser.py tests/test_chart_parser.py tests/test_csv_parser.py tests/test_excel_parser.py tests/test_pdf_parser.py tests/test_evidence_storage.py tests/test_evidence_uploader.py -q
```

Full command:

```text
uv run --with-requirements requirements.txt python -m pytest tests -q
```

Additional checks:

- `python -m compileall -q levi bot`
- FastAPI/parser/storage/ingestion import smoke test
- `git diff --check`
- Source scans for hosted-model references, forbidden chart recommendation fields, key use, and public storage-path exposure
- Tracked-file and scope review

## Test Results

- 70 new meaningful test functions added.
- Focused Phase 2A result: 69 passed, 1 skipped.
- The skipped test is the Windows symbolic-link escape test when the host does not grant symlink creation; the rejection path is implemented and the test runs where supported.
- Network calls: none.
- Fixtures: synthetic images, tables, workbooks, and PDFs only.

## Full Suite Results

- 100 passed, 1 skipped.
- 3 non-failing warnings: one TestClient/httpx deprecation and two existing FastAPI startup-event deprecations.
- All 31 pre-existing tests remain passing.

## Security Checks

- AES-GCM ciphertext differs from plaintext and decrypts only for the correct user/evidence identity.
- Missing encryption key fails closed; plaintext is disabled by default.
- SHA-256 integrity metadata matches original bytes.
- Cross-user retrieval and registry matching fail safely.
- Traversal, absolute paths, dangerous extension/MIME mismatches, unsupported types, excessive rows/columns/pages/characters/sizes, invalid images/workbooks/PDFs, and password-protected PDFs fail safely.
- Upload responses omit `raw_location`, `storage_path`, keys, and stack traces.
- Formula execution, macros, external links, OCR, hosted vision, recommendations, and network access are absent.

## Blockers

None.

## Assumptions

- The Phase 1 in-process registry remains intentionally non-durable until a separately approved persistence sprint.
- A user workspace/profile is provisioned before upload; authentication and authorization remain excluded.
- The environment supplies and protects a valid 32-byte encryption key in deployed environments.
- The configured workspace is on a trusted filesystem with appropriate OS permissions and backup controls.
- A 15-minute freshness window is conservative for current spot/timestamp evidence until a later approved market-data policy exists.
- Legacy `.xls` support reads stored workbook values through `xlrd`; macros and `.xlsm` are not supported.

## Scope Exclusions Confirmed

No hosted vision integration, OCR, dashboard/UI/widget, mobile upload, Supabase, S3, database persistence, authentication, broker connection, market feed, trading recommendation, specialist-agent change, model routing, live trading, automatic execution, Phase 2B, or Phase 3 work was implemented.

## Git Diff Summary

Phase 2A creates 22 scoped parser/storage/ingestion/test/documentation files and modifies only 6 existing foundation/configuration/API files. The implementation extends the Phase 1 architecture; it does not create a competing evidence contract or parallel application.

## Recommended Next Action

Stop for review. Do not push or merge until explicitly authorized. After technical and security approval, the next action is to review the local commit and open a Phase 2A pull request; no later sprint should begin from this handoff.
