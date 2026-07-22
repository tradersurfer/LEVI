from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from levi.auth.service import AuthService
from levi.streaming import AgentProgressEvent, AgentStatus, EventBus, build_streaming_router
from tests.auth_helpers import FakeAuthProvider
from tests.streaming_helpers import profile_loader


class PublishingRunner:
    def __init__(self, bus): self.bus = bus
    def run(self, user_id, symbol):
        request_id = str(uuid4())
        event = AgentProgressEvent(
            event_id=str(uuid4()), request_id=request_id, user_id=user_id,
            symbol=symbol, agent_name="CONSENSUS", status=AgentStatus.COMPLETE, sequence=1,
        )
        for queue in tuple(self.bus._subscribers.get(user_id, ())):
            queue.put_nowait(event)
        return request_id


def app_client():
    app = FastAPI(); bus = EventBus(); runner = PublishingRunner(bus)
    app.include_router(build_streaming_router(runner=runner, bus=bus, profile_loader=profile_loader))
    return app, TestClient(app), bus


def test_ws_stream_delivers_user_event_when_auth_disabled(monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_ENABLED", "false")
    _, client, _ = app_client()
    with client.websocket_connect("/ws/agents?user_id=u1") as websocket:
        response = client.post("/api/agents/analyze", json={"user_id": "u1", "symbol": "SPY"})
        assert websocket.receive_json()["request_id"] == response.json()["request_id"]


def test_ws_stream_isolates_another_user(monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_ENABLED", "false")
    _, client, bus = app_client()
    with client.websocket_connect("/ws/agents?user_id=u1"):
        assert bus.subscriber_count("u1") == 1 and bus.subscriber_count("u2") == 0


def test_ws_unsubscribes_on_disconnect(monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_ENABLED", "false")
    _, client, bus = app_client()
    with client.websocket_connect("/ws/agents?user_id=u1"):
        assert bus.subscriber_count("u1") == 1
    assert bus.subscriber_count("u1") == 0


def test_ws_auth_rejects_identity_mismatch(monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_ENABLED", "true")
    app, client, _ = app_client(); app.state.auth_service = AuthService(FakeAuthProvider())
    with pytest.raises(Exception) as denied:
        with client.websocket_connect(
            "/ws/agents?user_id=u2", headers={"Authorization": "Bearer token"},
        ):
            pass
    assert getattr(denied.value, "status_code", 403) == 403


def test_ws_auth_accepts_matching_identity(monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_ENABLED", "true")
    app, client, _ = app_client(); app.state.auth_service = AuthService(FakeAuthProvider())
    with client.websocket_connect(
        "/ws/agents?user_id=user-1", headers={"Authorization": "Bearer token"},
    ) as websocket:
        response = client.post(
            "/api/agents/analyze", json={"user_id": "user-1", "symbol": "SPY"},
            headers={"Authorization": "Bearer token"},
        )
        assert websocket.receive_json()["request_id"] == response.json()["request_id"]
