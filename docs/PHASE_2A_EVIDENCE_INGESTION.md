# LEVI Phase 2A — Evidence Ingestion

Phase 2A connects approved user uploads to the Phase 1 `EvidenceRecord`, `EvidenceRegistry`, and `WhatYouNeed` contracts. It does not add authentication, databases, market data, model routing, recommendations, or UI.

## Architecture

```text
POST /api/evidence/upload
        |
        v
EvidenceIngestionService
  1. validate ownership metadata, extension, MIME, and size
  2. select one deterministic parser
  3. parse structured metadata
  4. encrypt and store the original file
  5. create the canonical Phase 1 EvidenceRecord
  6. register it, rolling storage back if registration fails
        |
        v
WhatYouNeed confidence/ticker/timeframe gate
```

Parsers live under `levi/evidence/parsers/`, storage adapters under `levi/evidence/storage/`, and orchestration under `levi/evidence/ingestion/`.

## Supported file types

| Input | Extensions | Behavior |
| --- | --- | --- |
| Screenshot/chart image | `.png`, `.jpg`, `.jpeg`, `.webp` | Dimensions and safe metadata; vision provider boundary defaults to no-op |
| CSV/tabular data | `.csv` | UTF-8/BOM, delimiter detection, normalized columns, bounded rows/columns |
| Excel/tabular data | `.xlsx`, `.xls` | Multiple sheets; hidden/empty sheets skipped; formulas never evaluated |
| PDF | `.pdf` | Text extraction only; encrypted, oversized, or excessive-page PDFs rejected |

Archives, executables, HTML, macros, audio, video, arbitrary binaries, and `.xlsm` files are rejected.

## Parser behavior

All parsers return the shared immutable `ParsedEvidence` contract: evidence type, parser identity/version, extracted text, tickers, timeframe, captured time, confidence, warnings, structured data, and metadata. Identical inputs produce deterministic parsing results. Evidence IDs and encryption nonces are intentionally unique.

The screenshot and chart parsers expose `VisionExtractor`. `NoOpVisionExtractor` is the default and reports that no provider is configured. No hosted model or OCR dependency is connected. Chart output is descriptive only and strips entry, stop, target, probability, and recommendation fields.

CSV and Excel schema detection uses column signatures for options chains, portfolio exports, trade journals, broker statements, and generic tables. Unmapped columns and sheet origins remain in structured data.

PDF parsing uses text already embedded in a document. Image-only PDFs return a warning and low confidence; OCR is not attempted. Password protection is never bypassed.

## Confidence scoring and matching

`LEVI_EVIDENCE_CONFIDENCE_THRESHOLD` defaults to `0.70`. Evidence below the threshold is listed by `WhatYouNeed` as low-confidence context but does not satisfy a strict requirement.

Ticker-sensitive evidence must match the requested ticker. Chart evidence must match the required timeframe. An options-chain requirement requires `EvidenceType.OPTIONS_CHAIN`; a generic screenshot cannot satisfy it. Live-feed spot/timestamp evidence older than 15 minutes is considered stale. No market-data lookup occurs.

## Storage encryption and isolation

`EncryptedFilesystemStorage` uses AES-256-GCM authenticated encryption with a random nonce and user/evidence identity as associated data. `LEVI_EVIDENCE_ENCRYPTION_KEY` must be a URL-safe base64-encoded 32-byte key. The key remains outside user workspaces and is never logged or returned.

Encryption fails closed by default. Development plaintext storage is available only with `LEVI_ALLOW_PLAINTEXT_EVIDENCE=true`; its default is false. Stored names are generated from evidence IDs. Storage rejects traversal, absolute/original path names, null bytes, symbolic-link escapes, cross-user lookup, and user-selected stored filenames.

Files are stored beneath:

```text
{LEVI_WORKSPACE_ROOT}/users/{user_id}/evidence/
```

## Environment variables

```dotenv
LEVI_EVIDENCE_ENCRYPTION_KEY=
LEVI_ALLOW_PLAINTEXT_EVIDENCE=false
LEVI_EVIDENCE_CONFIDENCE_THRESHOLD=0.70
LEVI_MAX_CSV_SIZE_MB=20
LEVI_MAX_CSV_ROWS=100000
LEVI_MAX_CSV_COLUMNS=250
LEVI_MAX_PDF_SIZE_MB=25
LEVI_MAX_PDF_PAGES=300
LEVI_MAX_EXTRACTED_CHARACTERS=2000000
```

Generate and manage the encryption key outside the repository. Key rotation is not implemented in this sprint.

## Upload endpoint

`POST /api/evidence/upload` accepts multipart fields `user_id`, `source_name`, optional `declared_evidence_type`, optional ISO-8601 `captured_at`, and `file`.

Successful uploads return HTTP 201 with evidence identity, detected type/tickers/timeframe, confidence, warnings, and encryption status. The response never contains local storage paths or encryption material.

Expected failures use 400 for malformed input, 404 for a missing workspace/profile, 413 for size limits, 415 for unsupported media, 422 for parser validation, and a path/key-safe 500 response for internal configuration or ingestion failure.

## Security limitations

- The Phase 1 registry remains in-process and is not durable across process restarts.
- The filesystem adapter targets a single trusted host; operating-system permissions and backups remain deployment responsibilities.
- Authentication and authorization are explicitly outside Phase 2A, so the endpoint must not be exposed publicly without a later approved auth layer.
- Antivirus scanning, content disarm, OCR, key rotation, and hosted vision are not implemented.
- Formula text may be preserved, but formulas, links, macros, and embedded objects are never executed.

## Known exclusions

No dashboard widget, mobile upload flow, Supabase/S3 integration, database, authentication, broker connection, live feed, trading recommendation, specialist-agent change, model-routing change, live execution, Phase 2B, or Phase 3 work is included.

## Tests

Run focused Phase 2A tests:

```bash
pytest tests/test_screenshot_parser.py tests/test_chart_parser.py tests/test_csv_parser.py tests/test_excel_parser.py tests/test_pdf_parser.py tests/test_evidence_storage.py tests/test_evidence_uploader.py -q
```

Run the complete suite:

```bash
pytest tests -q
```

All fixtures are small and synthetic; no personal statements, portfolios, credentials, or screenshots are committed.

## S3-compatible migration path

The ingestion service depends only on `StorageAdapter`. A later approved sprint can implement an S3-compatible adapter with server-side or client-side authenticated encryption, tenant-scoped object keys, integrity metadata, and the same `store`, `retrieve`, `delete`, and `exists` methods. Parsers, `EvidenceRecord`, registry behavior, and the upload response do not need a competing architecture.
