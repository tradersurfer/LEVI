"""Bounded Excel workbook parsing without formula or macro execution."""

from __future__ import annotations

import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl
import xlrd

from levi.evidence.models import EvidenceType
from levi.evidence.parsers.base import ParsedEvidence, ParserValidationError
from levi.evidence.parsers.csv_parser import (
    detect_tabular_schema, normalize_column, schema_evidence_type,
)


EXCEL_MIMES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",
}


def _cell_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class ExcelEvidenceParser:
    parser_name = "excel_parser"
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
            Path(filename).suffix.lower() in {".xlsx", ".xls"}
            and mime_type.lower() in EXCEL_MIMES
            and evidence_type in {
                None, EvidenceType.EXCEL, EvidenceType.TABLE, EvidenceType.OPTIONS_CHAIN,
                EvidenceType.PORTFOLIO_EXPORT, EvidenceType.TRADE_JOURNAL,
                EvidenceType.BROKER_STATEMENT,
            }
        )

    def parse(self, *, file_path: Path, user_id: str, source_name: str) -> ParsedEvidence:
        if file_path.stat().st_size > self.max_size:
            raise ParserValidationError("workbook exceeds the configured size limit")
        suffix = file_path.suffix.lower()
        if suffix == ".xlsx":
            sheets = self._read_xlsx(file_path)
        elif suffix == ".xls":
            sheets = self._read_xls(file_path)
        else:
            raise ParserValidationError("unsupported workbook extension")
        return self._build_result(sheets, source_name)

    def _read_xlsx(self, file_path: Path) -> list[dict[str, Any]]:
        try:
            workbook = openpyxl.load_workbook(
                file_path, read_only=False, data_only=False, keep_links=False
            )
        except Exception as exc:
            raise ParserValidationError("invalid or unsupported XLSX workbook") from exc
        sheets: list[dict[str, Any]] = []
        for sheet in workbook.worksheets:
            rows = [[_cell_value(cell.value) for cell in row] for row in sheet.iter_rows()]
            sheets.append({"name": sheet.title, "hidden": sheet.sheet_state != "visible", "rows": rows})
        workbook.close()
        return sheets

    def _read_xls(self, file_path: Path) -> list[dict[str, Any]]:
        try:
            workbook = xlrd.open_workbook(file_path, on_demand=True)
        except Exception as exc:
            raise ParserValidationError("invalid or unsupported XLS workbook") from exc
        sheets = []
        for index in range(workbook.nsheets):
            sheet = workbook.sheet_by_index(index)
            rows = [[_cell_value(sheet.cell_value(r, c)) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
            visibility = getattr(workbook, "sheet_visibility", [0] * workbook.nsheets)[index]
            sheets.append({"name": sheet.name, "hidden": visibility != 0, "rows": rows})
        workbook.release_resources()
        return sheets

    def _build_result(self, raw_sheets: list[dict[str, Any]], source_name: str) -> ParsedEvidence:
        warnings: list[str] = []
        parsed_sheets: list[dict[str, Any]] = []
        all_tickers: set[str] = set()
        parsed_timestamps: list[str] = []
        total_rows = 0
        evidence_types: list[EvidenceType] = []
        for raw_sheet in raw_sheets:
            name = raw_sheet["name"]
            if raw_sheet["hidden"]:
                warnings.append(f"Hidden sheet '{name}' was skipped.")
                continue
            nonempty = [row for row in raw_sheet["rows"] if any(value not in (None, "") for value in row)]
            if not nonempty:
                warnings.append(f"Empty sheet '{name}' was skipped.")
                continue
            if len(nonempty[0]) > self.max_columns:
                raise ParserValidationError("workbook exceeds the configured column limit")
            columns = [normalize_column(str(value or "")) for value in nonempty[0]]
            sheet_rows: list[dict[str, Any]] = []
            for values in nonempty[1:]:
                if total_rows >= self.max_rows:
                    warnings.append(f"Workbook was truncated at the configured {self.max_rows} row limit.")
                    break
                if len(values) > self.max_columns:
                    raise ParserValidationError("workbook row exceeds the configured column limit")
                values += [None] * (len(columns) - len(values))
                row = dict(zip(columns, values[:len(columns)]))
                sheet_rows.append(row)
                total_rows += 1
            schema, schema_warnings = detect_tabular_schema(columns)
            warnings.extend(f"Sheet '{name}': {warning}" for warning in schema_warnings)
            evidence_type = schema_evidence_type(schema)
            evidence_types.append(evidence_type)
            for row in sheet_rows:
                for column in ("symbol", "ticker", "underlying"):
                    value = str(row.get(column, "")).strip().upper().lstrip("$")
                    if re.fullmatch(r"[A-Z]{1,5}", value):
                        all_tickers.add(value)
                for column, value in row.items():
                    if (column.endswith("_time") or column.endswith("_date") or column in {"date", "timestamp"}) and value:
                        try:
                            parsed_timestamps.append(datetime.fromisoformat(str(value).replace("Z", "+00:00")).isoformat())
                        except ValueError:
                            pass
            parsed_sheets.append({
                "sheet_name": name, "schema": schema.value, "columns": columns,
                "rows": sheet_rows, "row_count": len(sheet_rows),
            })
        if not parsed_sheets:
            raise ParserValidationError("workbook contains no visible, non-empty sheets")
        specific = [kind for kind in evidence_types if kind is not EvidenceType.TABLE]
        result_type = specific[0] if specific and len(set(specific)) == 1 else EvidenceType.TABLE
        if len(set(specific)) > 1:
            warnings.append("Workbook contains multiple detected schemas; evidence type is generic table.")
        return ParsedEvidence(
            evidence_type=result_type,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            extracted_text=None,
            ticker_symbols=tuple(sorted(all_tickers)),
            timeframe=None,
            captured_at=None,
            confidence=0.9 if specific else 0.65,
            warnings=tuple(dict.fromkeys(warnings)),
            structured_data={
                "sheets": parsed_sheets, "sheet_names": [s["name"] for s in raw_sheets],
                "parsed_timestamps": parsed_timestamps,
            },
            metadata={"source_name": source_name, "sheet_count": len(raw_sheets)},
        )
