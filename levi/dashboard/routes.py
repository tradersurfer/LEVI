"""FastAPI router for read-only dashboard projections."""

from __future__ import annotations

from collections.abc import Callable
import os

from fastapi import APIRouter, Depends, HTTPException, Request

from levi.auth.middleware import require_identity
from levi.auth.models import AuthIdentity
from levi.dashboard.models import (
    AlertListResponse, DashboardSummary, DecisionListResponse, EvidenceListResponse,
    PositionListResponse, SetupStatusResponse, TradeListResponse,
)
from levi.dashboard.service import DashboardService
from levi.profiles.models import UserTradingProfile


def build_dashboard_router(
    *,
    service_factory: Callable[[], DashboardService],
    profile_loader: Callable[[str], UserTradingProfile],
) -> APIRouter:
    router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

    def dashboard_identity(request: Request, user_id: str) -> AuthIdentity | None:
        """Enforce tenant identity when authentication is enabled on the app."""
        if os.getenv("LEVI_AUTH_ENABLED", "false").lower() != "true":
            return None
        identity = require_identity(request)
        if identity.user_id != user_id:
            raise HTTPException(status_code=403, detail="dashboard user does not match authenticated user")
        return identity

    def profile_or_error(user_id: str) -> UserTradingProfile:
        try:
            return profile_loader(user_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="user profile not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/summary", response_model=DashboardSummary)
    def summary(user_id: str, _identity=Depends(dashboard_identity)):
        return service_factory().summary(profile_or_error(user_id))

    @router.get("/positions", response_model=PositionListResponse)
    def positions(user_id: str, _identity=Depends(dashboard_identity)):
        profile_or_error(user_id)
        return service_factory().positions(user_id)

    @router.get("/trades", response_model=TradeListResponse)
    def trades(user_id: str, _identity=Depends(dashboard_identity)):
        profile_or_error(user_id)
        return service_factory().trades(user_id)

    @router.get("/evidence", response_model=EvidenceListResponse)
    def evidence(user_id: str, _identity=Depends(dashboard_identity)):
        profile_or_error(user_id)
        return service_factory().evidence(user_id)

    @router.get("/decisions", response_model=DecisionListResponse)
    def decisions(user_id: str, _identity=Depends(dashboard_identity)):
        profile_or_error(user_id)
        return service_factory().decisions(user_id)

    @router.get("/alerts", response_model=AlertListResponse)
    def alerts(user_id: str, _identity=Depends(dashboard_identity)):
        profile_or_error(user_id)
        return service_factory().alerts(user_id)

    @router.get("/setup-status", response_model=SetupStatusResponse)
    def setup_status(user_id: str, _identity=Depends(dashboard_identity)):
        return service_factory().setup(profile_or_error(user_id))

    return router
