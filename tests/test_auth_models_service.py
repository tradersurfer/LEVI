from dataclasses import FrozenInstanceError

import pytest

from levi.auth.errors import TokenRevokedError
from levi.auth.models import OAuthProvider
from levi.auth.service import AuthService
from levi.auth.sessions import SessionRevocationStore
from tests.auth_helpers import FakeAuthProvider


def test_signup_delegates(): assert AuthService(FakeAuthProvider()).signup("a@b.com", "password").identity.email == "a@b.com"
def test_login_delegates(): assert AuthService(FakeAuthProvider()).login("a@b.com", "password").access_token == "access"
def test_google_oauth_url(): assert "google" in AuthService(FakeAuthProvider()).oauth_url(OAuthProvider.GOOGLE)
def test_github_oauth_url(): assert "github" in AuthService(FakeAuthProvider()).oauth_url(OAuthProvider.GITHUB)
def test_identity_delegates(): assert AuthService(FakeAuthProvider()).identity("token").user_id == "user-1"
def test_logout_revokes_provider_and_local():
    provider = FakeAuthProvider(); service = AuthService(provider); service.logout("token")
    assert provider.revoked == ["token"]
    with pytest.raises(TokenRevokedError): service.identity("token")
def test_token_fingerprint_not_plaintext(): assert SessionRevocationStore.fingerprint("secret") != "secret"
def test_identity_is_immutable():
    identity = FakeAuthProvider().session().identity
    with pytest.raises(FrozenInstanceError): identity.user_id = "other"
