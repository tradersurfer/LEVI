from __future__ import annotations

from levi.agents.models import AgentVerdict
from levi.evidence.models import EvidenceRecord, EvidenceType
from levi.evidence.registry import EvidenceRegistry
from levi.streaming import AgentProgressEvent, AgentStatus, EventBus, PipelineRunner
from tests.streaming_helpers import FixedAgent, allowed_risk, collect_run, profile_loader, run


def phase9_runner(registry=None, risk_factory=allowed_risk):
    bus = EventBus()
    value = PipelineRunner(
        registry=registry or EvidenceRegistry(), profile_loader=profile_loader, bus=bus,
        agents=tuple(FixedAgent(name) for name in ("SCOUT", "ATLAS", "LENS")),
        risk_request_factory=risk_factory,
    )
    return value, bus


def test_event_contract_accepts_volt():
    event = AgentProgressEvent(
        event_id="e", request_id="r", user_id="u1", symbol="SPY",
        agent_name="VOLT", status=AgentStatus.QUEUED,
    )
    assert event.agent_name == "VOLT"


def test_volt_is_sequenced_after_lens_before_guardian():
    value, bus = phase9_runner()
    _, _, events = run(collect_run(value, bus))
    markers = [(event.agent_name, event.status) for event in events]
    assert markers.index(("LENS", AgentStatus.COMPLETE)) < markers.index(("VOLT", AgentStatus.QUEUED))
    assert markers.index(("VOLT", AgentStatus.COMPLETE)) < markers.index(("GUARDIAN", AgentStatus.QUEUED))


def test_volt_neutral_decision_does_not_change_vote_outcome():
    value, bus = phase9_runner()
    _, consensus, events = run(collect_run(value, bus))
    volt = next(event for event in events if event.agent_name == "VOLT" and event.status is AgentStatus.COMPLETE)
    assert volt.verdict is AgentVerdict.INSUFFICIENT_EVIDENCE
    assert consensus.approved is True and consensus.verdict is AgentVerdict.BULLISH


def test_volt_uses_real_deterministic_inputs_from_evidence():
    registry = EvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="option-inputs", user_id="u1", evidence_type=EvidenceType.TABLE,
        source_name="fixture", parsed_payload={
            "spot": 100, "strike": 100, "dte": 30, "risk_free_rate": 0.05,
            "volatility": 0.2, "option_type": "call", "bid": 2, "ask": 2.05,
        },
    ))
    value, bus = phase9_runner(registry)
    _, _, events = run(collect_run(value, bus))
    volt = next(event for event in events if event.agent_name == "VOLT" and event.status is AgentStatus.COMPLETE)
    assert volt.verdict is AgentVerdict.NEUTRAL and "delta" in volt.summary


def test_volt_does_not_invent_missing_inputs():
    value, bus = phase9_runner()
    _, _, events = run(collect_run(value, bus))
    volt = next(event for event in events if event.agent_name == "VOLT" and event.status is AgentStatus.COMPLETE)
    assert volt.confidence == 0 and volt.verdict is AgentVerdict.INSUFFICIENT_EVIDENCE


def test_final_consensus_event_keeps_approval_and_guardian_fields_separate():
    value, bus = phase9_runner()
    _, consensus, events = run(collect_run(value, bus))
    final = events[-1]
    assert final.agent_name == "CONSENSUS"
    assert final.approved is consensus.approved is True
    assert final.guardian_blocked is consensus.guardian_blocked is False


def test_blocked_consensus_payload_preserves_both_false_and_true():
    value, bus = phase9_runner(risk_factory=PipelineRunner._safe_risk_request)
    _, consensus, events = run(collect_run(value, bus))
    payload = events[-1].as_payload()
    assert consensus.approved is False
    assert payload["approved"] is False and payload["guardian_blocked"] is True


def test_consensus_fields_reject_non_boolean_values():
    try:
        AgentProgressEvent(
            event_id="e", request_id="r", user_id="u1", symbol="SPY",
            agent_name="CONSENSUS", status=AgentStatus.COMPLETE, approved="yes",
        )
    except ValueError as exc:
        assert "approved" in str(exc)
    else:
        raise AssertionError("non-boolean approved value was accepted")


def test_public_config_exposes_auth_capability_without_secrets(monkeypatch):
    from fastapi.testclient import TestClient
    from bot.status_api import app

    monkeypatch.setenv("LEVI_AUTH_ENABLED", "true")
    assert TestClient(app).get("/api/config").json() == {"auth_enabled": True}
    monkeypatch.setenv("LEVI_AUTH_ENABLED", "false")
    assert TestClient(app).get("/api/config").json() == {"auth_enabled": False}
