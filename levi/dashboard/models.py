"""Typed response contracts for the Phase 5 dashboard API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    user_id: str
    display_name: str
    account_value: float
    buying_power: float
    daily_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    open_positions: int
    execution_mode: str
    updated_at: str


class PositionListResponse(BaseModel):
    user_id: str
    positions: list[dict[str, Any]] = Field(default_factory=list)
    count: int


class TradeListResponse(BaseModel):
    user_id: str
    trades: list[dict[str, Any]] = Field(default_factory=list)
    count: int


class EvidenceListResponse(BaseModel):
    user_id: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    count: int


class ConsensusSummary(BaseModel):
    decision: str
    approved: bool
    votes_required: int
    votes_received: int


class DecisionListResponse(BaseModel):
    user_id: str
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    consensus: ConsensusSummary
    required_votes: int


class AlertListResponse(BaseModel):
    user_id: str
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    count: int


class SetupStep(BaseModel):
    id: str
    label: str
    complete: bool


class SetupStatusResponse(BaseModel):
    user_id: str
    steps: list[SetupStep]
    complete: bool
    paper_trading: bool
