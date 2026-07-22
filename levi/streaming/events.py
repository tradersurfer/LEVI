"""Wire contracts for live specialist-agent progress."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from levi.agents.models import AgentVerdict


class AgentStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    BLOCKED = "blocked"
    ERROR = "error"


_AGENT_NAMES = frozenset({"SCRIBE", "SCOUT", "ATLAS", "LENS", "GUARDIAN", "CONSENSUS"})


@dataclass(frozen=True)
class AgentProgressEvent:
    event_id: str
    request_id: str
    user_id: str
    symbol: str
    agent_name: str
    status: AgentStatus
    verdict: AgentVerdict | None = None
    confidence: float | None = None
    summary: str | None = None
    sequence: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        try:
            status = self.status if isinstance(self.status, AgentStatus) else AgentStatus(self.status)
        except ValueError as exc:
            raise ValueError(f"unsupported status: {self.status}") from exc
        try:
            verdict = (
                self.verdict
                if self.verdict is None or isinstance(self.verdict, AgentVerdict)
                else AgentVerdict(self.verdict)
            )
        except ValueError as exc:
            raise ValueError(f"unsupported verdict: {self.verdict}") from exc
        if not self.event_id.strip() or not self.request_id.strip() or not self.user_id.strip():
            raise ValueError("event_id, request_id, and user_id are required")
        symbol = self.symbol.strip().upper()
        agent_name = self.agent_name.strip().upper()
        if not symbol:
            raise ValueError("symbol is required")
        if agent_name not in _AGENT_NAMES:
            raise ValueError(f"unsupported agent_name: {agent_name}")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.sequence < 0:
            raise ValueError("sequence cannot be negative")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "agent_name", agent_name)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "verdict", verdict)

    def as_payload(self) -> dict[str, object]:
        """Return a JSON-safe representation of this immutable event."""
        return {
            "event_id": self.event_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "verdict": self.verdict.value if self.verdict else None,
            "confidence": self.confidence,
            "summary": self.summary,
            "sequence": self.sequence,
            "created_at": self.created_at.isoformat(),
        }
