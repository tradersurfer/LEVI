"""Small Supabase GoTrue adapter; network behavior is injectable for tests."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import requests

from .errors import AuthenticationConfigurationError, AuthenticationError
from .models import AuthenticatedUser, AuthSession, OAuthProvider


class SupabaseAuthAdapter:
    def __init__(self, *, url: str | None = None, anon_key: str | None = None,
                 session: requests.Session | None = None, timeout: float = 8.0):
        self.url = (url or os.getenv("SUPABASE_URL", "")).rstrip("/")
        self.anon_key = anon_key or os.getenv("SUPABASE_ANON_KEY", "")
        self.session = session or requests.Session()
        self.timeout = timeout

    def _configured(self) -> None:
        if not self.url or not self.anon_key:
            raise AuthenticationConfigurationError("Supabase authentication is not configured")

    def _request(self, method: str, path: str, *, token: str | None = None,
                 payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._configured()
        headers = {"apikey": self.anon_key, "Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = self.session.request(method, f"{self.url}/auth/v1/{path}",
                                            headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            raise AuthenticationError("authentication provider unavailable") from exc
        if response.status_code >= 400:
            raise AuthenticationError("authentication request rejected")
        try:
            return response.json()
        except ValueError as exc:
            raise AuthenticationError("authentication provider returned invalid data") from exc

    @staticmethod
    def _identity(user: dict[str, Any]) -> AuthenticatedUser:
        user_id = str(user.get("id") or "")
        if not user_id:
            raise AuthenticationError("authentication response missing user identity")
        metadata = user.get("app_metadata") or {}
        return AuthenticatedUser(user_id=user_id, email=user.get("email"),
                            provider=str(metadata.get("provider") or "email"), claims=dict(user))

    def _session(self, data: dict[str, Any]) -> AuthSession:
        token = str(data.get("access_token") or "")
        if not token:
            raise AuthenticationError("authentication response missing access token")
        return AuthSession(access_token=token, refresh_token=data.get("refresh_token"),
                           expires_at=datetime.now(timezone.utc) + timedelta(seconds=int(data.get("expires_in", 3600))),
                           identity=self._identity(data.get("user") or {}))

    def signup(self, *, email: str, password: str) -> AuthSession:
        return self._session(self._request("POST", "signup", payload={"email": email, "password": password}))

    def login(self, *, email: str, password: str) -> AuthSession:
        return self._session(self._request("POST", "token?grant_type=password", payload={"email": email, "password": password}))

    def oauth_url(self, *, provider: OAuthProvider, redirect_to: str | None = None) -> str:
        self._configured()
        query = {"provider": provider.value}
        if redirect_to:
            query["redirect_to"] = redirect_to
        return f"{self.url}/auth/v1/authorize?{urlencode(query)}"

    def refresh_session(self, refresh_token: str) -> AuthSession:
        return self._session(self._request("POST", "token?grant_type=refresh_token", payload={"refresh_token": refresh_token}))

    def verify_token(self, access_token: str) -> AuthIdentity:
        return self._identity(self._request("GET", "user", token=access_token))

    def revoke_session(self, access_token: str) -> None:
        self._request("POST", "logout", token=access_token)

    def exchange_code(self, code: str, redirect_to: str | None = None) -> AuthSession:
        payload = {"auth_code": code}
        if redirect_to:
            payload["redirect_to"] = redirect_to
        return self._session(self._request("POST", "token?grant_type=pkce", payload=payload))
