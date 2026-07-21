"""Bounded CSV parsing and column-signature schema detection."""

from __future__ import annotations

import csv
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from levi.evidence.models import EvidenceType
from levi.evidence.parsers.base import ParsedEvidence, ParserValidationError


class TabularSchema(str, Enum):
    OPTIONS_CHAIN = "options_chain"
    PORTFOLIO_EXPORT = "portfolio_export"
    TRADE_JOURNAL = "trade_journal"
    BROKER_STATEMENT = "broker_statement"
    GENERIC_TABLE = "generic_table"


SCHEMA_SIGNATURES = {
    TabularSchema.OPTIONS_CHAIN: {
        "symbol", "expiration", "strike", "option_type", "bid", "ask", "last",
        "volume", "open_interest", "implied_volatility", "delta", "gamma", "theta", "vega",
    },
    TabularSchema.PORTFOLIO_EXPORT: {
        "symbol", "quantity", "shares", "market_value", "cost_basis", "average_price",
        "unrealized_gain",
    },
    TabularSchema.TRADE_JOURNAL: {
        "entry_time", "exit_time", "entry_price", "exit_price", "side", "strategy", "pnl", "notes",
    },
    TabularSchema.BROKER_STATEMENT: {
        "account", "account_number", "statement_date", "symbol", "quantity", "market_value",
        "cash_balance", "net_liquidation",
    },
}

CSV_MIMES = {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"}


def normalize_column(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower()).strip("_")
    aliases = {
        "ticker": "symbol", "underlying_symbol": "symbol", "qty": "quantity",
        "avg_price": "average_price", "open_interest_": "open_interest",
        "iv": "implied_volatility", "profit_loss": "pnl", "p_l": "pnl",
        "call_put": "option_type", "type": "option_type",
    }
    return aliases.get(value, value or "unnamed_column")


def detect_tabular_schema(columns: Iterable[str]) -> tuple[TabularSchema, tuple[str, ...]]:
    names = set(columns)
    scores = {schema: len(names & signature) for schema, signature in SCHEMA_SIGNATURES.items()}
    best_score = max(scores.values(), default=0)
    winners = [schema for schema, score in scores.items() if score == best_score and score >= 2]
    warnings: list[str] = []
    if not winners:
        return TabularSchema.GENERIC_TABLE, ("No known tabular schema matched the column signature.",)
    if len(winners) > 1:
        warnings.append("Column signature is ambiguous; the most specific matching schema was selected.")
    priority = [
        TabularSchema.OPTIONS_CHAIN, TabularSchema.TRADE_JOURNAL,
        TabularSchema.BROKER_STATEMENT, TabularSchema.PORTFOLIO_EXPORT,
    ]
    selected = next(schema for schema in priority if schema in winners)
    return selected, tuple(warnings)


def schema_evidence_type(schema: TabularSchema) -> EvidenceType:
    return {
        TabularSchema.OPTIONS_CHAIN: EvidenceType.OPTIONS_CHAIN,
        TabularSchema.PORTFOLIO_EXPORT: EvidenceType.PORTFOLIO_EXPORT,
        TabularSchema.TRADE_JOURNAL: EvidenceType.TRADE_JOURNAL,
        TabularSchema.BROKER_STATEMENT: EvidenceType.BROKER_STATEMENT,
        TabularSchema.GENERIC_TABLE: EvidenceType.TABLE,
    }[schema]


def _parse_timestamp(value: str) -> str | None:
    candidate = (value or "").strip().replace("Z", "+00:00")
    if not candidate:
        return None
    try:
        return datetime.fromisoformat(candidate).isoformat()
    except ValueError:
        return None


class CsvEvidenceParser:
    parser_name = "csv_parser"
    parser_version = "1.0"

    def __init__(self) -> None:
        self.max_size = int(os.getenv("LEVI_MAX_CSV_SIZE_MB", "20")) * 1024 * 1024
        self.max_rows = int(os.getenv("LEVI_MAX_CSV_ROWS", "100000"))
        self.max_columns = int(os.getenv("LEVI_MAX_CSV_COLUMNS", "250"))

    def supports(
        self, *, filename: str, mime_type: str,
        evidence_type: EvidenceType | None = None,
    ) -> bool:
        return (
            Path(filename).suffix.lower() == ".csv"
            and mime_type.lower() in CSV_MIMES
            and evidence_type in {
                None, EvidenceType.CSV, EvidenceType.TABLE, EvidenceType.OPTIONS_CHAIN,
                EvidenceType.PORTFOLIO_EXPORT, EvidenceType.TRADE_JOURNAL,
                EvidenceType.BROKER_STATEMENT,
            }
        )

    def parse(self, *, file_path: Path, user_id: str, source_name: str) -> ParsedEvidence:
        if file_path.stat().st_size > self.max_size:
            raise ParserValidationError("CSV exceeds the configured size limit")
        raw = file_path.read_bytes()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ParserValidationError("CSV must use UTF-8 or UTF-8 with BOM") from exc
        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(text.splitlines(), dialect)
        try:
            original_columns = next(reader)
        except StopIteration as exc:
            raise ParserValidationError("CSV is empty") from exc
        if len(original_columns) > self.max_columns:
            raise ParserValidationError("CSV exceeds the configured column limit")
        columns = [normalize_column(column) for column in original_columns]
        warnings: list[str] = []
        if len(set(columns)) != len(columns):
            warnings.append("Duplicate normalized column names were preserved with numeric suffixes.")
            seen: dict[str, int] = {}
            unique: list[str] = []
            for column in columns:
                seen[column] = seen.get(column, 0) + 1
                unique.append(column if seen[column] == 1 else f"{column}_{seen[column]}")
            columns = unique

        rows: list[dict[str, str]] = []
        truncated = False
        for index, values in enumerate(reader):
            if index >= self.max_rows:
                truncated = True
                break
            if len(values) > self.max_columns:
                raise ParserValidationError("CSV row exceeds the configured column limit")
            values += [""] * (len(columns) - len(values))
            rows.append(dict(zip(columns, values[:len(columns)])))
        if truncated:
            warnings.append(f"CSV was truncated at the configured {self.max_rows} row limit.")

        schema, schema_warnings = detect_tabular_schema(columns)
        warnings.extend(schema_warnings)
        symbol_columns = [column for column in columns if column in {"symbol", "underlying", "ticker"}]
        tickers = sorted({
            row[column].strip().upper().lstrip("$")
            for row in rows for column in symbol_columns
            if re.fullmatch(r"\$?[A-Za-z]{1,5}", row.get(column, "").strip())
        })
        timestamp_columns = [
            column for column in columns
            if column.endswith("_time") or column.endswith("_date") or column in {"date", "timestamp"}
        ]
        parsed_timestamps = [
            parsed for row in rows for column in timestamp_columns
            if (parsed := _parse_timestamp(row.get(column, ""))) is not None
        ]
        return ParsedEvidence(
            evidence_type=schema_evidence_type(schema),
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            extracted_text=None,
            ticker_symbols=tuple(tickers),
            timeframe=None,
            captured_at=None,
            confidence=0.9 if schema is not TabularSchema.GENERIC_TABLE else 0.65,
            warnings=tuple(warnings),
            structured_data={
                "schema": schema.value, "columns": columns, "rows": rows,
                "row_count": len(rows), "parsed_timestamps": parsed_timestamps,
            },
            metadata={"delimiter": dialect.delimiter, "encoding": "utf-8-sig", "source_name": source_name},
        )
