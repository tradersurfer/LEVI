"""Bounded text extraction for unencrypted, text-based PDFs."""

from __future__ import annotations

import os
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from levi.evidence.models import EvidenceType
from levi.evidence.parsers.base import ParsedEvidence, ParserValidationError, extract_tickers


PDF_MIMES = {"application/pdf", "application/x-pdf"}


def _document_type(text: str) -> tuple[str, EvidenceType]:
    lower = text.lower()
    if any(term in lower for term in ("brokerage statement", "account statement", "net liquidation")):
        return "broker_statement", EvidenceType.BROKER_STATEMENT
    if any(term in lower for term in ("portfolio report", "portfolio summary", "asset allocation")):
        return "portfolio_report", EvidenceType.PORTFOLIO_EXPORT
    if any(term in lower for term in ("research report", "investment research", "analyst report")):
        return "research_report", EvidenceType.PDF
    return "generic_pdf", EvidenceType.PDF


class PdfEvidenceParser:
    parser_name = "pdf_parser"
    parser_version = "1.0"

    def __init__(self) -> None:
        self.max_size = int(os.getenv("LEVI_MAX_PDF_SIZE_MB", "25")) * 1024 * 1024
        self.max_pages = int(os.getenv("LEVI_MAX_PDF_PAGES", "300"))
        self.max_characters = int(os.getenv("LEVI_MAX_EXTRACTED_CHARACTERS", "2000000"))

    def supports(
        self, *, filename: str, mime_type: str,
        evidence_type: EvidenceType | None = None,
    ) -> bool:
        return (
            Path(filename).suffix.lower() == ".pdf"
            and mime_type.lower() in PDF_MIMES
            and evidence_type in {
                None, EvidenceType.PDF, EvidenceType.BROKER_STATEMENT,
                EvidenceType.PORTFOLIO_EXPORT,
            }
        )

    def parse(self, *, file_path: Path, user_id: str, source_name: str) -> ParsedEvidence:
        if file_path.stat().st_size > self.max_size:
            raise ParserValidationError("PDF exceeds the configured size limit")
        try:
            reader = PdfReader(str(file_path), strict=True)
        except (PdfReadError, OSError, ValueError) as exc:
            raise ParserValidationError("invalid or unreadable PDF") from exc
        if reader.is_encrypted:
            raise ParserValidationError("encrypted or password-protected PDFs are not supported")
        page_count = len(reader.pages)
        if page_count > self.max_pages:
            raise ParserValidationError("PDF exceeds the configured page limit")
        warnings: list[str] = []
        pages: list[dict[str, object]] = []
        pieces: list[str] = []
        remaining = self.max_characters
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                text = ""
                warnings.append(f"Page {index} text extraction failed safely.")
            if len(text) > remaining:
                text = text[:remaining]
                warnings.append(f"Extracted text was truncated at {self.max_characters} characters.")
            pages.append({"page": index, "text": text})
            pieces.append(text)
            remaining -= len(text)
            if remaining <= 0:
                break
        extracted = "\n".join(piece for piece in pieces if piece).strip()
        if not extracted:
            warnings.append("PDF contains no extractable text and may be image-only; OCR was not attempted.")
        document_type, evidence_type = _document_type(extracted)
        return ParsedEvidence(
            evidence_type=evidence_type,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            extracted_text=extracted or None,
            ticker_symbols=extract_tickers(extracted),
            timeframe=None,
            captured_at=None,
            confidence=0.85 if extracted else 0.1,
            warnings=tuple(dict.fromkeys(warnings)),
            structured_data={"document_type": document_type, "pages": pages, "page_count": page_count},
            metadata={"source_name": source_name, "page_count": page_count},
        )
