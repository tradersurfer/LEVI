"""Authentication orchestration independent of HTTP framework."""

from .base import AuthProvider
from .errors import TokenRevokedError
from .models import AuthIdentity, AuthSession, OAuthProvider
from .sessions import SessionRevocationStore


class AuthService:
    def __init__(self, adapter: AuthProvider, revocations: SessionRevocationStore | None = None):
        self.adapter = adapter
        self.revocations = revocations or SessionRevocationStore()

    def signup(self, email: str, password: str) -> AuthSession:
        return self.adapter.signup(email=email, password=password)

    def login(self, email: str, password: str) -> AuthSession:
        return self.adapter.login(email=email, password=password)

    def oauth_url(self, provider: OAuthProvider, redirect_to: str | None = None) -> str:
        return self.adapter.oauth_url(provider=provider, redirect_to=redirect_to)

    def identity(self, token: str) -> AuthIdentity:
        if self.revocations.is_revoked(token):
            raise TokenRevokedError("access token has been revoked")
        return self.adapter.verify_token(token)

    def logout(self, token: str) -> None:
        self.adapter.revoke_session(token)
        self.revocations.revoke(token)

    def refresh_session(self, refresh_token: str) -> AuthSession:
        return self.adapter.refresh_session(refresh_token)

    def exchange_code(self, code: str, redirect_to: str | None = None) -> AuthSession:
        return self.adapter.exchange_code(code, redirect_to)
