"""Authentication endpoints for the existing FastAPI application."""

from __future__ import annotations

from dataclasses import asdict
import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from .errors import AuthenticationConfigurationError, AuthenticationError
from .middleware import bearer_token, require_identity
from .models import AuthIdentity, OAuthProvider


router = APIRouter(prefix="/api/auth", tags=["authentication"])


class CredentialsRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("invalid email address")
        return normalized


class OAuthRequest(BaseModel):
    provider: OAuthProvider
    redirect_to: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=4096)


def _safe_redirect(redirect_to: str | None) -> str | None:
    if redirect_to is None:
        return None
    allowed = {item.strip() for item in os.getenv("LEVI_AUTH_REDIRECT_ALLOWLIST", "").split(",") if item.strip()}
    if redirect_to not in allowed:
        raise HTTPException(status_code=400, detail="redirect URL is not allowed")
    return redirect_to


def _service(request: Request):
    service = getattr(request.app.state, "auth_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="authentication is disabled")
    return service


def _serialize(session):
    return {"access_token": session.access_token, "refresh_token": session.refresh_token,
            "expires_at": session.expires_at.isoformat(), "user": asdict(session.identity)}


def _call(action):
    try:
        return action()
    except AuthenticationConfigurationError as exc:
        raise HTTPException(status_code=503, detail="authentication is not configured") from exc
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: CredentialsRequest, request: Request):
    return _serialize(_call(lambda: _service(request).signup(str(payload.email), payload.password)))


@router.post("/login")
def login(payload: CredentialsRequest, request: Request):
    return _serialize(_call(lambda: _service(request).login(str(payload.email), payload.password)))


@router.post("/oauth")
def oauth(payload: OAuthRequest, request: Request):
    redirect = _safe_redirect(payload.redirect_to)
    return {"authorization_url": _call(lambda: _service(request).oauth_url(payload.provider, redirect))}


@router.get("/oauth/{provider}")
def oauth_provider(provider: OAuthProvider, request: Request, redirect_to: str | None = None):
    redirect = _safe_redirect(redirect_to)
    return {"authorization_url": _call(lambda: _service(request).oauth_url(provider, redirect))}


@router.get("/callback")
def oauth_callback(request: Request, code: str, redirect_to: str | None = None):
    redirect = _safe_redirect(redirect_to)
    return _serialize(_call(lambda: _service(request).exchange_code(code, redirect)))


@router.post("/refresh")
def refresh(payload: RefreshRequest, request: Request):
    return _serialize(_call(lambda: _service(request).refresh_session(payload.refresh_token)))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request):
    _call(lambda: _service(request).logout(bearer_token(request)))


@router.get("/me")
def me(identity: AuthIdentity = Depends(require_identity)):
    return asdict(identity)
