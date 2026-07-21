"""Local JWT signature and claim validation used by request middleware."""

from __future__ import annotations

import os
from typing import Any

import jwt

from .errors import AuthenticationConfigurationError, AuthenticationError
from .models import AuthenticatedUser


class JwtValidator:
    def __init__(self, *, secret: str | None = None, audience: str | None = None,
                 issuer: str | None = None):
        self.secret = secret or os.getenv("SUPABASE_JWT_SECRET", "")
        self.audience = audience or os.getenv("LEVI_AUTH_AUDIENCE", "authenticated")
        self.issuer = issuer if issuer is not None else os.getenv("LEVI_AUTH_ISSUER") or None

    def validate(self, token: str) -> AuthenticatedUser:
        if not self.secret:
            raise AuthenticationConfigurationError("JWT validation is not configured")
        options: dict[str, Any] = {"require": ["sub", "exp"]}
        try:
            claims = jwt.decode(token, self.secret, algorithms=["HS256"], audience=self.audience,
                                issuer=self.issuer, options=options)
        except jwt.PyJWTError as exc:
            raise AuthenticationError("invalid or expired access token") from exc
        from datetime import datetime, timezone
        return AuthenticatedUser(user_id=str(claims["sub"]), email=claims.get("email"),
            provider=str(claims.get("app_metadata", {}).get("provider", "email")),
            issued_at=datetime.fromtimestamp(claims["iat"], timezone.utc) if claims.get("iat") else None,
            expires_at=datetime.fromtimestamp(claims["exp"], timezone.utc), claims=claims)
