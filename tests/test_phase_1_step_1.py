"""Focused tests for the Phase 1, Step 1 foundation."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from levi.contracts.what_you_need import build_what_you_need
from levi.evidence.models import EvidenceRecord, EvidenceType
from levi.evidence.registry import EvidenceRegistry
from levi.modes.router import resolve_mode_policy
from levi.profiles.models import ExecutionMode, InstrumentType, TradingMode, UserTradingProfile
from levi.workspace.initializer import initialize_user_workspace, load_user_profile


def profile(**overrides) -> UserTradingProfile:
    values = {
        "user_id": "user-1",
        "display_name": "Test User",
        "trading_mode": TradingMode.DAY_TRADING,
        "instrument_type": InstrumentType.OPTIONS,
        "execution_mode": ExecutionMode.PAPER_TRADING,
        "account_value": 10_000,
        "buying_power": 5_000,
    }
    values.update(overrides)
    return UserTradingProfile(**values)


def evidence(evidence_id: str, evidence_type: EvidenceType, **overrides) -> EvidenceRecord:
    values = {
        "evidence_id": evidence_id,
        "user_id": "user-1",
        "evidence_type": evidence_type,
        "source_name": "test fixture",
        "ticker_symbols": ["SPY"],
    }
    values.update(overrides)
    return EvidenceRecord(**values)


def test_valid_day_trading_options_profile():
    result = profile()
    assert result.instrument_type is InstrumentType.OPTIONS
    assert result.execution_mode is ExecutionMode.PAPER_TRADING


def test_valid_swing_trading_options_profile():
    result = profile(trading_mode=TradingMode.SWING_TRADING)
    assert result.trading_mode is TradingMode.SWING_TRADING


def test_valid_investing_stock_profile():
    result = profile(
        trading_mode=TradingMode.INVESTING_HOLDING,
        instrument_type=InstrumentType.STOCKS,
    )
    assert result.instrument_type is InstrumentType.STOCKS


def test_invalid_investing_options_profile():
    with pytest.raises(ValidationError, match="does not support options"):
        profile(trading_mode=TradingMode.INVESTING_HOLDING)


def test_workspace_creation(tmp_path):
    expected = profile()
    user_dir = initialize_user_workspace(expected, tmp_path)
    assert {path.name for path in user_dir.iterdir()} == {
        "MEMORY.md", "MOOD.md", "BEHAVIOR.md", "PROFILE.json", "evidence"
    }
    assert load_user_profile("user-1", tmp_path) == expected


def test_workspace_user_isolation(tmp_path):
    first = initialize_user_workspace(profile(), tmp_path)
    second = initialize_user_workspace(
        profile(user_id="user-2", display_name="Second User"), tmp_path
    )
    assert first != second
    assert load_user_profile("user-1", tmp_path).display_name == "Test User"
    assert load_user_profile("user-2", tmp_path).display_name == "Second User"


def test_mode_routing():
    day = resolve_mode_policy(profile())
    swing = resolve_mode_policy(profile(trading_mode=TradingMode.SWING_TRADING))
    investing = resolve_mode_policy(profile(
        trading_mode=TradingMode.INVESTING_HOLDING,
        instrument_type=InstrumentType.STOCKS,
    ))
    assert day.required_timeframes == ["5m", "15m"]
    assert "options chain" in day.required_evidence
    assert swing.required_timeframes == ["4h", "1d"]
    assert investing.allowed_instruments == [InstrumentType.STOCKS]


def test_evidence_registration_and_queries():
    registry = EvidenceRegistry()
    record = registry.register(evidence(
        "chart-1", EvidenceType.CHART, timeframe="5m", warnings=["stale"]
    ))
    assert registry.get("chart-1", "user-1") == record
    assert registry.by_user("user-1") == [record]
    assert registry.by_ticker("user-1", "spy") == [record]
    assert registry.by_type("user-1", EvidenceType.CHART) == [record]
    assert registry.recent("user-1", timedelta(hours=1)) == [record]
    assert registry.list_warnings("user-1") == ["stale"]


def test_evidence_user_isolation():
    registry = EvidenceRegistry()
    registry.register(evidence("private-1", EvidenceType.TEXT_NOTE))
    with pytest.raises(PermissionError, match="another user"):
        registry.get("private-1", "user-2")
    with pytest.raises(PermissionError, match="another user"):
        registry.register(evidence(
            "private-1", EvidenceType.TEXT_NOTE, user_id="user-2"
        ))
    assert registry.by_user("user-2") == []


def test_what_you_need_with_missing_evidence():
    result = build_what_you_need(profile(), EvidenceRegistry(), "trade_analysis", "SPY")
    assert result.can_proceed is False
    assert "current spot" in result.missing_items
    assert "account value" in result.already_available
    assert not set(result.optional_items).intersection(result.missing_items)


def test_what_you_need_with_complete_required_evidence():
    registry = EvidenceRegistry()
    for record in [
        evidence("feed", EvidenceType.LIVE_FEED, captured_at=datetime.now(timezone.utc)),
        evidence("chart-5", EvidenceType.CHART, timeframe="5m"),
        evidence("chart-15", EvidenceType.CHART, timeframe="15m"),
        evidence("chain", EvidenceType.OPTIONS_CHAIN),
    ]:
        registry.register(record)
    result = build_what_you_need(profile(), registry, "trade_analysis", "SPY")
    assert result.can_proceed is True
    assert result.missing_items == []
    assert set(result.required_items).issubset(result.already_available)
