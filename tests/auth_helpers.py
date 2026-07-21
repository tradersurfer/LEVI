from datetime import datetime, timedelta, timezone

from levi.auth.models import AuthIdentity, AuthSession


class FakeAuthProvider:
    def __init__(self):
        self.revoked = []
        self.verified = []
        self.fail = False

    def session(self, email="user@example.com"):
        return AuthSession("access", "refresh", datetime.now(timezone.utc) + timedelta(hours=1),
                           AuthIdentity("user-1", email, "email"))

    def signup(self, *, email, password): return self.session(email)
    def login(self, *, email, password): return self.session(email)
    def oauth_url(self, *, provider, redirect_to=None): return f"https://auth.test/{provider.value}?redirect={redirect_to or ''}"
    def refresh_session(self, refresh_token): return self.session()
    def verify_token(self, access_token):
        from levi.auth.errors import AuthenticationError
        if self.fail: raise AuthenticationError("invalid token")
        self.verified.append(access_token)
        return self.session().identity
    def revoke_session(self, access_token): self.revoked.append(access_token)
    def exchange_code(self, code, redirect_to=None): return self.session()
