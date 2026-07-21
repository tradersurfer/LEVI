import pytest

from levi.auth.errors import AuthenticationConfigurationError, AuthenticationError
from levi.auth.models import OAuthProvider
from levi.auth.supabase import SupabaseAuthAdapter


class Response:
    status_code = 200
    def __init__(self, data): self.data = data
    def json(self): return self.data


class Session:
    def __init__(self, response): self.response=response; self.calls=[]
    def request(self, method, url, **kwargs): self.calls.append((method,url,kwargs)); return self.response


def data(): return {"access_token":"a", "refresh_token":"r", "expires_in":60, "user":{"id":"u1","email":"u@test.com","app_metadata":{"provider":"email"}}}
def test_signup_parses_session(): assert SupabaseAuthAdapter(url="https://x",anon_key="k",session=Session(Response(data()))).signup(email="u@test.com",password="password").identity.user_id == "u1"
def test_login_uses_password_grant():
    transport=Session(Response(data())); SupabaseAuthAdapter(url="https://x",anon_key="k",session=transport).login(email="u@test.com",password="password")
    assert "grant_type=password" in transport.calls[0][1]
def test_refresh_uses_refresh_grant():
    transport=Session(Response(data())); SupabaseAuthAdapter(url="https://x",anon_key="k",session=transport).refresh_session("r")
    assert "refresh_token" in transport.calls[0][2]["json"]
def test_verify_token_uses_bearer():
    transport=Session(Response(data()["user"])); assert SupabaseAuthAdapter(url="https://x",anon_key="k",session=transport).verify_token("a").user_id == "u1"
    assert transport.calls[0][2]["headers"]["Authorization"] == "Bearer a"
def test_revoke_session_posts_logout():
    transport=Session(Response({})); SupabaseAuthAdapter(url="https://x",anon_key="k",session=transport).revoke_session("a")
    assert transport.calls[0][1].endswith("/logout")
def test_oauth_supports_google_and_redirect(): assert "provider=google" in SupabaseAuthAdapter(url="https://x",anon_key="k").oauth_url(provider=OAuthProvider.GOOGLE,redirect_to="https://app.test/cb")
def test_missing_configuration_fails_closed():
    with pytest.raises(AuthenticationConfigurationError): SupabaseAuthAdapter(url="",anon_key="").oauth_url(provider=OAuthProvider.GITHUB)
def test_provider_error_is_safe():
    response=Response({}); response.status_code=401
    with pytest.raises(AuthenticationError, match="rejected"): SupabaseAuthAdapter(url="https://x",anon_key="k",session=Session(response)).login(email="u@test.com",password="password")
def test_exchange_code_uses_pkce_grant():
    transport=Session(Response(data())); SupabaseAuthAdapter(url="https://x",anon_key="k",session=transport).exchange_code("code")
    assert "grant_type=pkce" in transport.calls[0][1]
