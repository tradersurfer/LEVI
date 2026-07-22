from datetime import datetime

import pytest

from levi.agents.models import AgentVerdict
from levi.streaming.events import AgentProgressEvent, AgentStatus


def event(**changes):
    values = dict(
        event_id="e1", request_id="r1", user_id="u1", symbol="spy",
        agent_name="scout", status=AgentStatus.RUNNING,
    )
    values.update(changes)
    return AgentProgressEvent(**values)


def test_event_normalizes_symbol_and_agent_name():
    value = event()
    assert value.symbol == "SPY" and value.agent_name == "SCOUT"


def test_event_reuses_canonical_agent_verdict():
    assert event(verdict=AgentVerdict.BULLISH).verdict is AgentVerdict.BULLISH


def test_event_normalizes_wire_enum_values():
    value = event(status="complete", verdict="bullish")
    assert value.status is AgentStatus.COMPLETE and value.verdict is AgentVerdict.BULLISH


def test_event_rejects_unknown_agent():
    with pytest.raises(ValueError, match="unsupported"):
        event(agent_name="OTHER")


def test_event_rejects_invalid_confidence():
    with pytest.raises(ValueError, match="confidence"):
        event(confidence=1.01)


def test_event_rejects_negative_sequence():
    with pytest.raises(ValueError, match="sequence"):
        event(sequence=-1)


def test_event_timestamp_is_timezone_aware():
    assert event().created_at.tzinfo is not None


def test_event_payload_is_json_safe():
    payload = event(verdict=AgentVerdict.BEARISH, confidence=0.75).as_payload()
    assert payload["verdict"] == "bearish" and isinstance(payload["created_at"], str)


def test_event_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        event(created_at=datetime(2026, 1, 1))
