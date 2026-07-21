"""Vendor-neutral evidence records and parser extension point."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    SCREENSHOT = "screenshot"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    TABLE = "table"
    CHART = "chart"
    GRAPH = "graph"
    BROKER_STATEMENT = "broker_statement"
    PORTFOLIO_EXPORT = "portfolio_export"
    OPTIONS_CHAIN = "options_chain"
    TRADE_JOURNAL = "trade_journal"
    TEXT_NOTE = "text_note"
    LIVE_FEED = "live_feed"


class ParsedEvidence(BaseModel):
    evidence_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class EvidenceRecord(BaseModel):
    evidence_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    evidence_type: EvidenceType
    source_name: str = Field(min_length=1)
    filename: str | None = None
    mime_type: str | None = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    captured_at: datetime | None = None
    ticker_symbols: list[str] = Field(default_factory=list)
    account_name: str | None = None
    timeframe: str | None = None
    raw_location: str | None = None
    parsed_payload: dict[str, Any] | None = None
    confidence: float = Field(default=1.0, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceParser(Protocol):
    def supports(self, evidence: EvidenceRecord) -> bool:
        ...

    def parse(self, evidence: EvidenceRecord) -> ParsedEvidence:
        ...
