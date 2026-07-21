"""Pre-analysis evidence gate."""

from __future__ import annotations

from dataclasses import dataclass

from levi.evidence.models import EvidenceRecord, EvidenceType
from levi.evidence.registry import EvidenceRegistry
from levi.modes.router import resolve_mode_policy
from levi.profiles.models import UserTradingProfile


@dataclass
class WhatYouNeed:
    request_type: str
    required_items: list[str]
    optional_items: list[str]
    already_available: list[str]
    missing_items: list[str]
    can_proceed: bool


def _items_from_evidence(evidence: EvidenceRecord) -> set[str]:
    items = {str(item) for item in evidence.metadata.get("evidence_items", [])}
    if evidence.evidence_type is EvidenceType.LIVE_FEED:
        items.update({"current spot", "timestamp", "volume"})
    elif evidence.evidence_type is EvidenceType.OPTIONS_CHAIN:
        items.update({"options chain", "expiration"})
    elif evidence.evidence_type is EvidenceType.PORTFOLIO_EXPORT:
        items.update({"open positions", "current position or desired position"})
    elif evidence.evidence_type is EvidenceType.BROKER_STATEMENT:
        items.update({"open positions", "current position or desired position"})
    if evidence.evidence_type in {EvidenceType.CHART, EvidenceType.GRAPH}:
        timeframe = (evidence.timeframe or "").lower()
        chart_names = {
            "5m": "5-minute chart", "5-minute": "5-minute chart",
            "15m": "15-minute chart", "15-minute": "15-minute chart",
            "4h": "4-hour chart", "4-hour": "4-hour chart",
            "1d": "daily chart", "daily": "daily chart",
        }
        if timeframe in chart_names:
            items.add(chart_names[timeframe])
    return items


def build_what_you_need(
    profile: UserTradingProfile,
    registry: EvidenceRegistry,
    request_type: str,
    ticker: str | None = None,
) -> WhatYouNeed:
    policy = resolve_mode_policy(profile)
    available = {"trading mode", "risk profile"}
    if profile.account_value >= 0:
        available.add("account value")
    if profile.buying_power >= 0:
        available.add("buying power")
    if ticker:
        available.add("ticker")

    user_records = registry.by_user(profile.user_id)
    records = [
        evidence for evidence in user_records
        if not ticker
        or not evidence.ticker_symbols
        or ticker.upper() in {symbol.upper() for symbol in evidence.ticker_symbols}
    ]
    for evidence in records:
        available.update(_items_from_evidence(evidence))

    required = list(policy.required_evidence)
    optional = list(policy.preferred_evidence)
    already = [item for item in required + optional if item in available]
    missing = [item for item in required if item not in available]
    return WhatYouNeed(
        request_type=request_type,
        required_items=required,
        optional_items=optional,
        already_available=already,
        missing_items=missing,
        can_proceed=not missing,
    )
