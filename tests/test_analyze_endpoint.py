from fastapi import FastAPI
from fastapi.testclient import TestClient

from levi.auth.service import AuthService
from levi.streaming import ConcurrentAnalysisError, EventBus, build_streaming_router
from tests.auth_helpers import FakeAuthProvider
from tests.streaming_helpers import profile_loader


class StubRunner:
    def __init__(self): self.calls = []; self.error = None
    def run(self, user_id, symbol):
        if self.error: raise self.error
        self.calls.append((user_id, symbol)); return "request-1"


def client(runner=None):
    app = FastAPI(); value = runner or StubRunner()
    app.include_router(build_streaming_router(runner=value, bus=EventBus(), profile_loader=profile_loader))
    return TestClient(app), value, app


def test_analyze_returns_request_id_immediately():
    api, value, _ = client()
    response = api.post("/api/agents/analyze", json={"user_id": "u1", "symbol": "spy"})
    assert response.status_code == 202 and response.json() == {"request_id": "request-1"}
    assert value.calls == [("u1", "spy")]


def test_analyze_requires_existing_profile():
    api, _, _ = client()
    assert api.post("/api/agents/analyze", json={"user_id": "missing", "symbol": "SPY"}).status_code == 404


def test_analyze_rejects_invalid_symbol():
    api, _, _ = client()
    assert api.post("/api/agents/analyze", json={"user_id": "u1", "symbol": "../SPY"}).status_code == 422


def test_analyze_returns_409_for_concurrent_run():
    value = StubRunner(); value.error = ConcurrentAnalysisError("analysis already running for this user")
    api, _, _ = client(value)
    assert api.post("/api/agents/analyze", json={"user_id": "u1", "symbol": "SPY"}).status_code == 409


def test_analyze_auth_rejects_different_user(monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_ENABLED", "true")
    api, _, app = client(); app.state.auth_service = AuthService(FakeAuthProvider())
    response = api.post(
        "/api/agents/analyze", json={"user_id": "u2", "symbol": "SPY"},
        headers={"Authorization": "Bearer token"},
    )
    assert response.status_code == 403


def test_analyze_is_permissive_when_auth_disabled(monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_ENABLED", "false")
    api, _, _ = client()
    assert api.post("/api/agents/analyze", json={"user_id": "u2", "symbol": "SPY"}).status_code == 202


def test_existing_fastapi_application_registers_streaming_routes():
    from bot.status_api import app
    assert str(app.url_path_for("analyze")) == "/api/agents/analyze"
    assert str(app.url_path_for("agent_stream")) == "/ws/agents"
