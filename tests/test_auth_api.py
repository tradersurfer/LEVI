from fastapi.testclient import TestClient

from bot.status_api import app
from levi.auth.service import AuthService
from tests.auth_helpers import FakeAuthProvider


def client():
    app.state.auth_service = AuthService(FakeAuthProvider())
    return TestClient(app)


def test_signup_endpoint(): assert client().post("/api/auth/signup",json={"email":"U@TEST.COM","password":"password"}).status_code == 201
def test_login_endpoint(): assert client().post("/api/auth/login",json={"email":"u@test.com","password":"password"}).json()["access_token"] == "access"
def test_short_password_rejected(): assert client().post("/api/auth/login",json={"email":"u@test.com","password":"x"}).status_code == 422
def test_invalid_email_rejected(): assert client().post("/api/auth/login",json={"email":"invalid","password":"password"}).status_code == 422
def test_oauth_endpoint(): assert "github" in client().post("/api/auth/oauth",json={"provider":"github"}).json()["authorization_url"]
def test_me_requires_bearer(): assert client().get("/api/auth/me").status_code == 401
def test_me_returns_identity(): assert client().get("/api/auth/me",headers={"Authorization":"Bearer token"}).json()["user_id"] == "user-1"
def test_logout_returns_204(): assert client().post("/api/auth/logout",headers={"Authorization":"Bearer token"}).status_code == 204
def test_refresh_endpoint(): assert client().post("/api/auth/refresh",json={"refresh_token":"r"}).json()["access_token"] == "access"
def test_oauth_provider_endpoint(): assert "google" in client().get("/api/auth/oauth/google").json()["authorization_url"]
def test_callback_endpoint(): assert client().get("/api/auth/callback",params={"code":"abc"}).json()["user"]["user_id"] == "user-1"
def test_redirect_not_allowlisted_is_rejected(monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_REDIRECT_ALLOWLIST","https://safe.test/callback")
    assert client().get("/api/auth/oauth/google",params={"redirect_to":"https://evil.test"}).status_code == 400
def test_allowlisted_redirect_is_accepted(monkeypatch):
    monkeypatch.setenv("LEVI_AUTH_REDIRECT_ALLOWLIST","https://safe.test/callback")
    assert client().get("/api/auth/oauth/github",params={"redirect_to":"https://safe.test/callback"}).status_code == 200
