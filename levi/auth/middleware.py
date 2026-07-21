"""FastAPI authentication dependency and optional identity middleware."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException, Request, status
from fastapi.security.utils import get_authorization_scheme_param

from .errors import AuthenticationConfigurationError, AuthenticationError
from .models import AuthIdentity


def bearer_token(request: Request) -> str:
    scheme, token = get_authorization_scheme_param(request.headers.get("Authorization"))
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    return token


def require_identity(request: Request) -> AuthIdentity:
    service = getattr(request.app.state, "auth_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="authentication is disabled")
    try:
        return service.identity(bearer_token(request))
    except AuthenticationConfigurationError as exc:
        raise HTTPException(status_code=503, detail="authentication is not configured") from exc
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


class AuthenticationMiddleware:
    """Populate request.state.identity when a bearer token is present."""

    def __init__(self, app, service_getter: Callable | None = None):
        self.app = app
        self.service_getter = service_getter

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        scheme, token = get_authorization_scheme_param(request.headers.get("Authorization"))
        scope.setdefault("state", {})["identity"] = None
        service = self.service_getter(request) if self.service_getter else getattr(request.app.state, "auth_service", None)
        if service and scheme.lower() == "bearer" and token:
            try:
                scope["state"]["identity"] = service.identity(token)
            except (AuthenticationError, AuthenticationConfigurationError):
                pass
        await self.app(scope, receive, send)
