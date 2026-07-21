"""Build user-scoped dashboard responses from existing in-process state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from levi.evidence.registry import EvidenceRegistry
from levi.profiles.models import UserTradingProfile


def _iso(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else value


class DashboardService:
    """Project existing state into stable, JSON-safe dashboard contracts."""

    def __init__(self, *, shared: dict[str, Any], registry: EvidenceRegistry) -> None:
        self.shared = shared
        self.registry = registry

    def summary(self, profile: UserTradingProfile) -> dict[str, Any]:
        positions = [
            position for position in self.shared.get("positions", [])
            if position.get("user_id") == profile.user_id
        ]
        realized = sum(float(item.get("realized_pnl", 0) or 0) for item in positions)
        unrealized = sum(float(item.get("unrealized_pnl", 0) or 0) for item in positions)
        return {
            "user_id": profile.user_id,
            "display_name": profile.display_name,
            "account_value": profile.account_value,
            "buying_power": profile.buying_power,
            "daily_pnl": realized + unrealized,
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
            "open_positions": len(positions),
            "execution_mode": profile.execution_mode.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def positions(self, user_id: str) -> dict[str, Any]:
        positions = [
            dict(item) for item in self.shared.get("positions", [])
            if item.get("user_id") == user_id
        ]
        return {"user_id": user_id, "positions": positions, "count": len(positions)}

    def trades(self, user_id: str) -> dict[str, Any]:
        trades = [
            dict(item) for item in self.shared.get("trades", [])
            if item.get("user_id") == user_id
        ]
        return {"user_id": user_id, "trades": trades, "count": len(trades)}

    def evidence(self, user_id: str) -> dict[str, Any]:
        records = sorted(
            self.registry.by_user(user_id), key=lambda item: item.uploaded_at, reverse=True
        )
        return {
            "user_id": user_id,
            "evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "evidence_type": item.evidence_type.value,
                    "source_name": item.source_name,
                    "filename": item.filename,
                    "uploaded_at": _iso(item.uploaded_at),
                    "captured_at": _iso(item.captured_at),
                    "ticker_symbols": item.ticker_symbols,
                    "timeframe": item.timeframe,
                    "confidence": item.confidence,
                    "warnings": item.warnings,
                }
                for item in records
            ],
            "count": len(records),
        }

    def decisions(self, user_id: str) -> dict[str, Any]:
        decisions = [
            dict(item) for item in self.shared.get("decisions", [])
            if item.get("user_id") == user_id
        ]
        votes = [str(item.get("verdict", item.get("decision", "pending"))).lower() for item in decisions]
        approved = len(votes) >= 3 and all(vote in {"approve", "approved", "yes"} for vote in votes[:3])
        return {
            "user_id": user_id,
            "decisions": decisions,
            "consensus": {
                "decision": "approved" if approved else "not_approved",
                "approved": approved,
                "votes_required": 3,
                "votes_received": len(votes),
            },
            "required_votes": 3,
        }

    def setup(self, profile: UserTradingProfile) -> dict[str, Any]:
        evidence_count = len(self.registry.by_user(profile.user_id))
        steps = [
            {"id": "profile", "label": "Trading profile", "complete": True},
            {
                "id": "broker",
                "label": "Paper broker",
                "complete": bool(profile.broker_names),
            },
            {
                "id": "evidence",
                "label": "Evidence source",
                "complete": evidence_count > 0 or bool(profile.data_sources),
            },
        ]
        return {
            "user_id": profile.user_id,
            "steps": steps,
            "complete": all(step["complete"] for step in steps),
            "paper_trading": profile.execution_mode.value == "paper_trading",
        }

    def alerts(self, user_id: str) -> dict[str, Any]:
        alerts = [
            dict(item) for item in self.shared.get("alerts", [])
            if item.get("user_id") == user_id
        ]
        return {"user_id": user_id, "alerts": alerts, "count": len(alerts)}
