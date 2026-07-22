import os

import pytest

from levi.agents.models import AgentVerdict
from levi.evidence.registry import EvidenceRegistry
from levi.llm import MockLLMAdapter
from levi.streaming import AgentStatus, ConcurrentAnalysisError, EventBus, PipelineRunner
from tests.streaming_helpers import FixedAgent, SlowAgent, allowed_risk, collect_run, profile_loader, run


def runner(*, agents=None, risk_factory=allowed_risk):
    bus = EventBus()
    value = PipelineRunner(
        registry=EvidenceRegistry(), profile_loader=profile_loader, bus=bus,
        agents=agents or tuple(FixedAgent(name) for name in ("SCOUT", "ATLAS", "LENS")),
        risk_request_factory=risk_factory,
    )
    return value, bus


def test_runner_emits_monotonic_sequence_and_final_consensus():
    value, bus = runner()
    _, _, events = run(collect_run(value, bus))
    assert [item.sequence for item in events] == list(range(1, len(events) + 1))
    assert events[-1].agent_name == "CONSENSUS"


def test_runner_emits_queued_running_complete_for_specialists():
    value, bus = runner()
    _, _, events = run(collect_run(value, bus))
    for name in ("SCOUT", "ATLAS", "LENS"):
        assert [item.status for item in events if item.agent_name == name] == [
            AgentStatus.QUEUED, AgentStatus.RUNNING, AgentStatus.COMPLETE,
        ]


def test_runner_final_event_matches_real_consensus_object():
    value, bus = runner()
    request_id, consensus, events = run(collect_run(value, bus))
    final = events[-1]
    assert value.result(request_id) is consensus
    assert final.verdict is consensus.verdict
    assert final.confidence == consensus.confidence
    assert (final.status is AgentStatus.COMPLETE) is consensus.approved


def test_guardian_block_is_reflected_in_stream():
    value, bus = runner(risk_factory=PipelineRunner._safe_risk_request)
    _, consensus, events = run(collect_run(value, bus))
    guardian = next(item for item in events if item.agent_name == "GUARDIAN" and item.status is AgentStatus.BLOCKED)
    assert guardian.verdict is AgentVerdict.BLOCK and consensus.guardian_blocked


def test_runner_rejects_concurrent_user_run():
    async def scenario():
        value, _ = runner(agents=(SlowAgent("SCOUT"), FixedAgent("ATLAS"), FixedAgent("LENS")))
        request_id = value.run("u1", "SPY")
        with pytest.raises(ConcurrentAnalysisError):
            value.run("u1", "AAPL")
        await value.wait(request_id)
    run(scenario())


def test_runner_allows_different_users_concurrently():
    async def scenario():
        value, _ = runner(agents=(SlowAgent("SCOUT"), FixedAgent("ATLAS"), FixedAgent("LENS")))
        first = value.run("u1", "SPY"); second = value.run("u2", "AAPL")
        assert first != second
        await value.wait(first); await value.wait(second)
    run(scenario())


def test_runner_uses_existing_mock_adapter_when_unconfigured(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    value = PipelineRunner(registry=EvidenceRegistry(), profile_loader=profile_loader, bus=EventBus())
    assert all(isinstance(agent.llm, MockLLMAdapter) for agent in value.agents)


def test_runner_loads_only_requesting_users_evidence():
    value, bus = runner()
    _, _, events = run(collect_run(value, bus, user_id="u1"))
    assert all(item.user_id == "u1" for item in events)


def test_runner_invalid_symbol_rejected_before_start():
    value, _ = runner()
    with pytest.raises(ValueError, match="symbol"):
        value.run("u1", "../SPY")


def test_runner_failure_emits_safe_error_without_exception_text():
    class BrokenAgent(FixedAgent):
        def analyze(self, request):
            raise RuntimeError("private details")
    value, bus = runner(agents=(BrokenAgent("SCOUT"), FixedAgent("ATLAS"), FixedAgent("LENS")))
    _, result, events = run(collect_run(value, bus))
    assert result is None and events[-1].status is AgentStatus.ERROR
    assert "private details" not in events[-1].summary
