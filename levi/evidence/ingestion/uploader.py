"""Validate, parse, securely store, and register uploaded evidence."""

from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PureWindowsPath
from typing import Any, Sequence
from uuid import uuid4

from levi.evidence.models import EvidenceRecord, EvidenceType
from levi.evidence.parsers.base import EvidenceParser, ParsedEvidence, ParserValidationError
from levi.evidence.registry import EvidenceRegistry
from levi.evidence.storage.base import StorageAdapter, StoredEvidenceFile


class UploadValidationError(ValueError):
    pass


class UnsupportedEvidenceError(UploadValidationError):
    pass


class UploadSizeError(UploadValidationError):
    pass


EXTENSION_MIMES = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".webp": {"image/webp"},
    ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/octet-stream"},
    ".xls": {"application/vnd.ms-excel", "application/octet-stream"},
    ".pdf": {"application/pdf", "application/x-pdf"},
}


@dataclass(frozen=True)
class EvidenceUploadRequest:
    user_id: str
    source_name: str
    original_filename: str
    mime_type: str
    temporary_file_path: Path
    declared_evidence_type: EvidenceType | None = None
    captured_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceIngestionResult:
    evidence_record: EvidenceRecord
    parsed_evidence: ParsedEvidence
    stored_file: StoredEvidenceFile


def _validate_user_id(user_id: str) -> None:
    if (
        not user_id or user_id in {".", ".."} or "\x00" in user_id
        or "/" in user_id or "\\" in user_id or Path(user_id).is_absolute()
        or PureWindowsPath(user_id).is_absolute()
    ):
        raise UploadValidationError("invalid user_id")


def _validate_filename(filename: str) -> str:
    if (
        not filename or "\x00" in filename or Path(filename).name != filename
        or Path(filename).is_absolute() or PureWindowsPath(filename).is_absolute()
        or "/" in filename or "\\" in filename
    ):
        raise UploadValidationError("invalid original filename")
    extension = Path(filename).suffix.lower()
    if extension not in EXTENSION_MIMES:
        raise UnsupportedEvidenceError("unsupported file extension")
    return extension


class EvidenceIngestionService:
    def __init__(
        self, *, registry: EvidenceRegistry, storage: StorageAdapter,
        parsers: Sequence[EvidenceParser],
    ) -> None:
        self.registry = registry
        self.storage = storage
        self.parsers = tuple(parsers)

    def ingest(self, request: EvidenceUploadRequest) -> EvidenceIngestionResult:
        _validate_user_id(request.user_id)
        if not request.source_name.strip():
            raise UploadValidationError("source_name is required")
        extension = _validate_filename(request.original_filename)
        path = Path(request.temporary_file_path)
        if not path.is_file() or path.is_symlink():
            raise UploadValidationError("temporary upload file does not exist")
        size_limit_mb = int(os.getenv(
            "LEVI_MAX_PDF_SIZE_MB" if extension == ".pdf" else "LEVI_MAX_CSV_SIZE_MB",
            "25" if extension == ".pdf" else "20",
        ))
        if path.stat().st_size > size_limit_mb * 1024 * 1024:
            raise UploadSizeError("upload exceeds the configured size limit")

        mime_type = request.mime_type.lower().split(";", 1)[0].strip()
        if mime_type not in EXTENSION_MIMES[extension]:
            raise UnsupportedEvidenceError("file extension and MIME type do not match")
        guessed, _ = mimetypes.guess_type(request.original_filename)
        if guessed and guessed not in EXTENSION_MIMES[extension] and mime_type != "application/octet-stream":
            raise UnsupportedEvidenceError("dangerous extension and MIME mismatch")

        parser = next((
            candidate for candidate in self.parsers
            if candidate.supports(
                filename=request.original_filename, mime_type=mime_type,
                evidence_type=request.declared_evidence_type,
            )
        ), None)
        if parser is None:
            raise UnsupportedEvidenceError("no parser supports this upload")
        try:
            parsed = parser.parse(
                file_path=path, user_id=request.user_id, source_name=request.source_name
            )
        except ParserValidationError:
            raise
        except Exception as exc:
            raise ParserValidationError("parser could not safely process the upload") from exc

        evidence_id = f"ev_{uuid4().hex}"
        stored = self.storage.store(
            user_id=request.user_id,
            evidence_id=evidence_id,
            source_path=path,
            original_filename=request.original_filename,
        )
        metadata = {
            **request.metadata,
            **parsed.metadata,
            "parser_name": parsed.parser_name,
            "parser_version": parsed.parser_version,
            "sha256": stored.sha256,
            "encrypted": stored.encrypted,
        }
        record = EvidenceRecord(
            evidence_id=evidence_id,
            user_id=request.user_id,
            evidence_type=parsed.evidence_type,
            source_name=request.source_name,
            filename=request.original_filename,
            mime_type=mime_type,
            captured_at=request.captured_at or parsed.captured_at,
            ticker_symbols=list(parsed.ticker_symbols),
            timeframe=parsed.timeframe,
            raw_location=stored.storage_path,
            parsed_payload={
                "structured_data": parsed.structured_data,
                "extracted_text": parsed.extracted_text,
            },
            confidence=parsed.confidence,
            warnings=list(parsed.warnings),
            metadata=metadata,
        )
        try:
            self.registry.register(record)
        except Exception:
            self.storage.delete(user_id=request.user_id, evidence_id=evidence_id)
            raise
        return EvidenceIngestionResult(record, parsed, stored)
