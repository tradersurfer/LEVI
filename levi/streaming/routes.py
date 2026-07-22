"""FastAPI HTTP and WebSocket routes for agent activity streaming."""

from __future__ import annotations

import os
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from levi.auth.middleware import require_identity
from levi.auth.models import AuthIdentity
from levi.profiles.models import UserTradingProfile

from .bus import EventBus
from .runner import ConcurrentAnalysisError, PipelineRunner


class AnalyzeRequest(BaseModel):
    user_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1, max_length=15, pattern=r"^[A-Za-z][A-Za-z0-9.\-]*$")


class AnalyzeResponse(BaseModel):
    request_id: str


def build_streaming_router(
    *,
    runner: PipelineRunner,
    bus: EventBus,
    profile_loader: Callable[[str], UserTradingProfile],
) -> APIRouter:
    router = APIRouter(tags=["agent-streaming"])

    def streaming_identity(request: Request, payload: AnalyzeRequest) -> AuthIdentity | None:
        if os.getenv("LEVI_AUTH_ENABLED", "false").lower() != "true":
            return None
        identity = require_identity(request)
        if identity.user_id != payload.user_id:
            raise HTTPException(status_code=403, detail="analysis user does not match authenticated user")
        return identity

    def profile_or_error(user_id: str) -> UserTradingProfile:
        try:
            return profile_loader(user_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="user profile not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/agents/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_202_ACCEPTED)
    async def analyze(payload: AnalyzeRequest, _identity=Depends(streaming_identity)):
        profile_or_error(payload.user_id)
        try:
            return AnalyzeResponse(request_id=runner.run(payload.user_id, payload.symbol))
        except ConcurrentAnalysisError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.websocket("/ws/agents")
    async def agent_stream(websocket: WebSocket, user_id: str):
        if os.getenv("LEVI_AUTH_ENABLED", "false").lower() == "true":
            identity = require_identity(websocket)  # type: ignore[arg-type]
            if identity.user_id != user_id:
                raise HTTPException(status_code=403, detail="stream user does not match authenticated user")
        profile_or_error(user_id)
        queue = bus.subscribe(user_id)
        await websocket.accept()
        try:
            while True:
                event = await queue.get()
                await websocket.send_json(event.as_payload())
        except WebSocketDisconnect:
            pass
        finally:
            bus.unsubscribe(user_id, queue)

    return router
