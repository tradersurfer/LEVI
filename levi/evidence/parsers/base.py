"""Shared parser contracts and conservative extraction helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from levi.evidence.models import EvidenceType


class ParserValidationError(ValueError):
    """The supplied file cannot be safely parsed under the configured limits."""


@dataclass(frozen=True)
class ParsedEvidence:
    evidence_type: EvidenceType
    parser_name: str
    parser_version: str
    extracted_text: str | None
    ticker_symbols: tuple[str, ...]
    timeframe: str | None
    captured_at: datetime | None
    confidence: float
    warnings: tuple[str, ...]
    structured_data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


class EvidenceParser(Protocol):
    def supports(
        self, *, filename: str, mime_type: str,
        evidence_type: EvidenceType | None = None,
    ) -> bool:
        ...

    def parse(
        self, *, file_path: Path, user_id: str, source_name: str,
    ) -> ParsedEvidence:
        ...


_TICKER_RE = re.compile(r"(?<![A-Z0-9])\$?([A-Z]{1,5})(?![A-Z0-9])")
_TICKER_STOPWORDS = {
    "A", "AM", "AN", "AND", "ASK", "AT", "AVG", "BUY", "CSV", "DATE", "ETF",
    "FROM", "HIGH", "ID", "IN", "LAST", "LOW", "MARKET", "NO", "OF", "ON",
    "OPEN", "PDF", "PRICE", "QTY", "SELL", "THE", "TIME", "TO", "USD", "VALUE",
}


def extract_tickers(text: str) -> tuple[str, ...]:
    return tuple(sorted({
        match.group(1) for match in _TICKER_RE.finditer(text or "")
        if match.group(1) not in _TICKER_STOPWORDS
    }))


def detect_timeframe(text: str) -> str | None:
    match = re.search(
        r"(?i)(?<!\w)(1|2|3|5|10|15|30|45)\s*(m|min|minute)s?(?!\w)", text or ""
    )
    if match:
        return f"{match.group(1)}m"
    match = re.search(r"(?i)(?<!\w)(1|2|3|4|6|8|12)\s*(h|hr|hour)s?(?!\w)", text or "")
    if match:
        return f"{match.group(1)}h"
    if re.search(r"(?i)(?<!\w)(1\s*d|daily|day)(?!\w)", text or ""):
        return "1d"
    if re.search(r"(?i)(?<!\w)(1\s*w|weekly|week)(?!\w)", text or ""):
        return "1w"
    return None
