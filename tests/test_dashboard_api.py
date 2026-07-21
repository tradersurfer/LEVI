"""Focused Phase 5 dashboard API and projection tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from bot.status_api import _shared, app, evidence_registry
from levi.dashboard.service import DashboardService
from levi.dashboard.models import DashboardSummary, DecisionListResponse
from levi.dashboard.routes import build_dashboard_router
from levi.agents.consensus import ConsensusEngine
from levi.agents.models import AgentVerdict
from levi.evidence.models import EvidenceRecord, EvidenceType
from levi.profiles.models import UserTradingProfile
from levi.workspace.initializer import initialize_user_workspace
from tests.auth_helpers import FakeAuthProvider
from tests.phase4_helpers import agent_decision, guardian
from levi.auth.service import AuthService


@pytest.fixture
def profile(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_WORKSPACE_ROOT", str(tmp_path))
    value = UserTradingProfile(
        user_id="dash-user", display_name="Dashboard User", account_value=25_000,
        buying_power=12_000, broker_names=["paper"], data_sources=["uploads"],
    )
    initialize_user_workspace(value)
    for key in ("trades", "positions", "decisions", "alerts"):
        _shared[key] = []
    _shared.pop("consensus_decision", None)
    evidence_registry._records.clear()
    yield value
    evidence_registry._records.clear()


@pytest.fixture
def client(profile):
    return TestClient(app)


def endpoint(client, name):
    return client.get(f"/api/dashboard/{name}", params={"user_id": "dash-user"})


def test_summary_endpoint_returns_profile_state(client):
    body = endpoint(client, "summary").json()
    assert body["account_value"] == 25_000 and body["execution_mode"] == "paper_trading"


def test_summary_includes_utc_update_timestamp(client):
    assert datetime.fromisoformat(endpoint(client, "summary").json()["updated_at"]).tzinfo


def test_summary_calculates_daily_pnl(client):
    _shared["positions"] = [{"user_id": "dash-user", "realized_pnl": 4, "unrealized_pnl": 6}]
    assert endpoint(client, "summary").json()["daily_pnl"] == 10


def test_positions_endpoint_returns_positions(client):
    _shared["positions"] = [{"user_id": "dash-user", "symbol": "SPY", "quantity": 1}]
    assert endpoint(client, "positions").json()["positions"][0]["symbol"] == "SPY"


def test_positions_endpoint_filters_another_user(client):
    _shared["positions"] = [{"user_id": "other", "symbol": "SECRET"}]
    assert endpoint(client, "positions").json()["count"] == 0


def test_trades_endpoint_returns_reasoning(client):
    _shared["trades"] = [{"user_id": "dash-user", "symbol": "SPY", "reasoning": "evidence"}]
    assert endpoint(client, "trades").json()["trades"][0]["reasoning"] == "evidence"


def test_trades_endpoint_filters_another_user(client):
    _shared["trades"] = [{"user_id": "other", "symbol": "SECRET"}]
    assert endpoint(client, "trades").json()["trades"] == []


def test_evidence_endpoint_returns_safe_metadata(client):
    evidence_registry.register(EvidenceRecord(
        evidence_id="ev-1", user_id="dash-user", evidence_type=EvidenceType.CHART,
        source_name="Fixture", filename="spy.png", ticker_symbols=["SPY"], timeframe="5m",
    ))
    body = endpoint(client, "evidence").json()["evidence"][0]
    assert body["filename"] == "spy.png" and "raw_location" not in body


def test_evidence_endpoint_filters_another_user(client):
    evidence_registry.register(EvidenceRecord(
        evidence_id="ev-2", user_id="other", evidence_type=EvidenceType.PDF, source_name="Private",
    ))
    assert endpoint(client, "evidence").json()["count"] == 0


def test_evidence_is_sorted_newest_first(client):
    for index, day in enumerate((1, 2)):
        evidence_registry.register(EvidenceRecord(
            evidence_id=f"ev-{index}", user_id="dash-user", evidence_type=EvidenceType.CHART,
            source_name="Fixture", uploaded_at=datetime(2026, 1, day, tzinfo=timezone.utc),
        ))
    assert endpoint(client, "evidence").json()["evidence"][0]["evidence_id"] == "ev-1"


def test_decisions_endpoint_exposes_agent_verdict_shape(client):
    _shared["decisions"] = [{"user_id": "dash-user", "agent_name": "SCOUT", "verdict": "approve", "confidence": .8}]
    assert endpoint(client, "decisions").json()["decisions"][0]["agent_name"] == "SCOUT"


def test_three_approvals_produce_approved_consensus(client):
    decisions = tuple(agent_decision(name, user="dash-user") for name in ("SCOUT", "ATLAS", "LENS"))
    _shared["decisions"] = list(decisions)
    _shared["consensus_decision"] = ConsensusEngine().evaluate(user_id="dash-user", symbol="SPY", decisions=decisions, guardian=guardian())
    assert endpoint(client, "decisions").json()["consensus"]["approved"] is True


def test_two_approvals_do_not_produce_consensus(client):
    _shared["decisions"] = [{"user_id": "dash-user", "verdict": "approve"}] * 2
    assert endpoint(client, "decisions").json()["consensus"]["decision"] == "not_approved"


def test_rejection_does_not_produce_consensus(client):
    _shared["decisions"] = [{"user_id": "dash-user", "verdict": value} for value in ("approve", "reject", "approve")]
    assert endpoint(client, "decisions").json()["consensus"]["approved"] is False

def test_real_agent_consensus_contract_reaches_dashboard(client):
    decisions = tuple(agent_decision(name, AgentVerdict.BEARISH, user="dash-user") for name in ("SCOUT", "ATLAS", "LENS"))
    consensus = ConsensusEngine().evaluate(user_id="dash-user", symbol="SPY", decisions=decisions, guardian=guardian())
    _shared["decisions"] = list(decisions)
    _shared["consensus_decision"] = consensus
    body = endpoint(client, "decisions").json()
    assert body["consensus"]["approved"] is True
    assert body["consensus"]["decision"] == "bearish"
    assert body["decisions"][0]["decision_id"] and body["decisions"][0]["verdict"] == "bearish"

def test_dashboard_requires_matching_identity_when_auth_enabled(client, monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_ENABLED", "true")
    app.state.auth_service = AuthService(FakeAuthProvider())
    try:
        assert endpoint(client, "summary").status_code == 401
        assert client.get("/api/dashboard/summary", params={"user_id": "dash-user"}, headers={"Authorization": "Bearer token"}).status_code == 403
    finally:
        del app.state.auth_service


def test_decisions_filter_another_user(client):
    _shared["decisions"] = [{"user_id": "other", "agent_name": "SCOUT", "verdict": "approve"}]
    assert endpoint(client, "decisions").json()["decisions"] == []


def test_alerts_endpoint_returns_alerts(client):
    _shared["alerts"] = [{"user_id": "dash-user", "message": "Paper fill", "severity": "info"}]
    assert endpoint(client, "alerts").json()["alerts"][0]["message"] == "Paper fill"


def test_alerts_filter_another_user(client):
    _shared["alerts"] = [{"user_id": "other", "message": "Private"}]
    assert endpoint(client, "alerts").json()["count"] == 0


def test_setup_status_has_three_steps(client):
    assert len(endpoint(client, "setup-status").json()["steps"]) == 3


def test_setup_status_marks_profile_complete(client):
    steps = endpoint(client, "setup-status").json()["steps"]
    assert next(step for step in steps if step["id"] == "profile")["complete"] is True


def test_setup_status_does_not_expose_credentials(client):
    body = endpoint(client, "setup-status").json()
    assert "password" not in str(body).lower() and "token" not in str(body).lower()


def test_setup_status_confirms_paper_mode(client):
    assert endpoint(client, "setup-status").json()["paper_trading"] is True


@pytest.mark.parametrize("route", ["summary", "positions", "trades", "evidence", "decisions", "alerts", "setup-status"])
def test_dashboard_routes_require_existing_profile(client, route):
    response = client.get(f"/api/dashboard/{route}", params={"user_id": "missing"})
    assert response.status_code == 404


def test_service_account_count_is_user_scoped(profile):
    service = DashboardService(shared={"trades": [{"user_id": "other"}]}, registry=evidence_registry)
    assert service.summary(profile)["open_positions"] == 0


def test_summary_excludes_position_without_user_id(profile):
    service = DashboardService(
        shared={"positions": [{"symbol": "OWNERLESS", "unrealized_pnl": 999}]},
        registry=evidence_registry,
    )
    summary = service.summary(profile)
    assert summary["open_positions"] == 0
    assert summary["daily_pnl"] == 0


@pytest.mark.parametrize(
    ("method_name", "response_key"),
    [("positions", "positions"), ("trades", "trades"),
     ("decisions", "decisions"), ("alerts", "alerts")],
)
def test_service_excludes_record_without_user_id(profile, method_name, response_key):
    service = DashboardService(
        shared={response_key: [{"symbol": "OWNERLESS", "message": "private"}]},
        registry=evidence_registry,
    )
    assert getattr(service, method_name)(profile.user_id)[response_key] == []


def test_service_contracts_are_json_safe(profile):
    service = DashboardService(shared={}, registry=evidence_registry)
    assert isinstance(service.summary(profile)["updated_at"], str)


def test_summary_response_model_validates_service_output(profile):
    output = DashboardService(shared={}, registry=evidence_registry).summary(profile)
    assert DashboardSummary.model_validate(output).user_id == profile.user_id


def test_decision_response_model_validates_consensus(profile):
    output = DashboardService(shared={}, registry=evidence_registry).decisions(profile.user_id)
    assert DecisionListResponse.model_validate(output).consensus.votes_required == 3


def test_dashboard_routes_are_owned_by_dashboard_router():
    router = build_dashboard_router(
        service_factory=lambda: DashboardService(shared={}, registry=evidence_registry),
        profile_loader=lambda _: UserTradingProfile(user_id="route-user", display_name="Route User"),
    )
    assert len(router.routes) == 7 and all("dashboard" in route.tags for route in router.routes)
