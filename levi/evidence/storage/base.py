"""Evidence storage contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class StoredEvidenceFile:
    evidence_id: str
    user_id: str
    storage_path: str
    original_filename: str
    stored_filename: str
    size_bytes: int
    sha256: str
    encrypted: bool
    encryption_version: str | None


class StorageAdapter(Protocol):
    def store(
        self, *, user_id: str, evidence_id: str, source_path: Path,
        original_filename: str,
    ) -> StoredEvidenceFile:
        ...

    def retrieve(self, *, user_id: str, evidence_id: str) -> bytes:
        ...

    def delete(self, *, user_id: str, evidence_id: str) -> None:
        ...

    def exists(self, *, user_id: str, evidence_id: str) -> bool:
        ...
