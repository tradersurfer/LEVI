"""In-process evidence registry with strict user isolation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from levi.evidence.models import EvidenceRecord, EvidenceType


class EvidenceRegistry:
    def __init__(self) -> None:
        self._records: dict[str, EvidenceRecord] = {}

    def register(self, evidence: EvidenceRecord) -> EvidenceRecord:
        existing = self._records.get(evidence.evidence_id)
        if existing and existing.user_id != evidence.user_id:
            raise PermissionError("evidence_id belongs to another user")
        self._records[evidence.evidence_id] = evidence
        return evidence

    def get(self, evidence_id: str, user_id: str) -> EvidenceRecord:
        evidence = self._records[evidence_id]
        self._assert_owner(evidence, user_id)
        return evidence

    def by_user(self, user_id: str) -> list[EvidenceRecord]:
        return [record for record in self._records.values() if record.user_id == user_id]

    def by_ticker(self, user_id: str, ticker: str) -> list[EvidenceRecord]:
        ticker = ticker.upper()
        return [
            record for record in self.by_user(user_id)
            if ticker in {symbol.upper() for symbol in record.ticker_symbols}
        ]

    def by_type(self, user_id: str, evidence_type: EvidenceType) -> list[EvidenceRecord]:
        return [record for record in self.by_user(user_id) if record.evidence_type is evidence_type]

    def recent(self, user_id: str, since: datetime | timedelta) -> list[EvidenceRecord]:
        cutoff = (
            datetime.now(timezone.utc) - since
            if isinstance(since, timedelta)
            else since
        )
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)
        return [
            record for record in self.by_user(user_id)
            if (record.captured_at or record.uploaded_at) >= cutoff
        ]

    def list_warnings(self, user_id: str) -> list[str]:
        return [warning for record in self.by_user(user_id) for warning in record.warnings]

    @staticmethod
    def _assert_owner(evidence: EvidenceRecord, user_id: str) -> None:
        if evidence.user_id != user_id:
            raise PermissionError("evidence belongs to another user")
