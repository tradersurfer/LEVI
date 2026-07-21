"""Pre-analysis evidence gate."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

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


STRICT_STRUCTURED_ITEMS = {"options chain", "current spot", "timestamp"}


def _items_from_evidence(
    evidence: EvidenceRecord, *, now: datetime | None = None,
) -> set[str]:
    items = {
        str(item) for item in evidence.metadata.get("evidence_items", [])
        if str(item) not in STRICT_STRUCTURED_ITEMS
    }
    if evidence.evidence_type is EvidenceType.LIVE_FEED:
        observed_at = evidence.captured_at or evidence.uploaded_at
        current_time = now or datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        if current_time - observed_at <= timedelta(minutes=15):
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
    confidence_threshold = float(os.getenv("LEVI_EVIDENCE_CONFIDENCE_THRESHOLD", "0.70"))
    available = {"trading mode", "risk profile"}
    if profile.account_value >= 0:
        available.add("account value")
    if profile.buying_power >= 0:
        available.add("buying power")
    if ticker:
        available.add("ticker")

    user_records = registry.by_user(profile.user_id)
    low_confidence: list[str] = []
    for evidence in user_records:
        ticker_sensitive = evidence.evidence_type in {
            EvidenceType.CHART, EvidenceType.GRAPH, EvidenceType.OPTIONS_CHAIN,
            EvidenceType.LIVE_FEED,
        }
        if ticker and ticker_sensitive and ticker.upper() not in {
            symbol.upper() for symbol in evidence.ticker_symbols
        }:
            continue
        matched_items = _items_from_evidence(evidence)
        if evidence.confidence < confidence_threshold:
            low_confidence.extend(
                f"{item} (low confidence: {evidence.confidence:.2f})"
                for item in sorted(matched_items)
            )
            continue
        available.update(matched_items)

    required = list(policy.required_evidence)
    optional = list(policy.preferred_evidence)
    already = [item for item in required + optional if item in available] + low_confidence
    missing = [item for item in required if item not in available]
    return WhatYouNeed(
        request_type=request_type,
        required_items=required,
        optional_items=optional,
        already_available=already,
        missing_items=missing,
        can_proceed=not missing,
    )
