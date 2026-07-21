"""Immutable authentication domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class OAuthProvider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str | None
    provider: str
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    claims: Mapping[str, Any] = field(default_factory=dict)


# Compatibility name retained for Phase 6 callers created before final review.
AuthIdentity = AuthenticatedUser


@dataclass(frozen=True)
class AuthSession:
    access_token: str
    refresh_token: str | None
    expires_at: datetime
    identity: AuthenticatedUser
