"""Validated, user-specific trading profile."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class TradingMode(str, Enum):
    DAY_TRADING = "day_trading"
    SWING_TRADING = "swing_trading"
    INVESTING_HOLDING = "investing_holding"


class InstrumentType(str, Enum):
    OPTIONS = "options"
    STOCKS = "stocks"
    POLYMARKET = "polymarket"


class ExecutionMode(str, Enum):
    ANALYSIS_ONLY = "analysis_only"
    ALERTS = "alerts"
    PAPER_TRADING = "paper_trading"
    HUMAN_APPROVED = "human_approved"


def _default_trading_mode() -> TradingMode:
    return TradingMode(os.getenv("LEVI_DEFAULT_TRADING_MODE", TradingMode.SWING_TRADING.value))


def _default_execution_mode() -> ExecutionMode:
    return ExecutionMode(
        os.getenv("LEVI_DEFAULT_EXECUTION_MODE", ExecutionMode.PAPER_TRADING.value)
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UserTradingProfile(BaseModel):
    user_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    trading_mode: TradingMode = Field(default_factory=_default_trading_mode)
    instrument_type: InstrumentType = InstrumentType.OPTIONS
    execution_mode: ExecutionMode = Field(default_factory=_default_execution_mode)
    experience_level: str = "beginner"
    account_value: float = Field(default=0.0, ge=0)
    buying_power: float = Field(default=0.0, ge=0)
    risk_per_trade_pct: float = Field(default=1.0, gt=0, le=100)
    daily_loss_limit_pct: float = Field(default=3.0, gt=0, le=100)
    weekly_loss_limit_pct: float = Field(default=6.0, gt=0, le=100)
    max_open_positions: int = Field(default=3, ge=1)
    max_correlated_positions: int = Field(default=1, ge=1)
    overnight_holding_allowed: bool = True
    preferred_tickers: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    broker_names: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    schema_version: str = "1.0"

    @model_validator(mode="after")
    def validate_mode_and_instrument(self) -> "UserTradingProfile":
        allowed = {
            TradingMode.DAY_TRADING: {InstrumentType.OPTIONS, InstrumentType.POLYMARKET},
            TradingMode.SWING_TRADING: {InstrumentType.OPTIONS, InstrumentType.POLYMARKET},
            TradingMode.INVESTING_HOLDING: {InstrumentType.STOCKS},
        }
        if self.instrument_type not in allowed[self.trading_mode]:
            choices = ", ".join(sorted(item.value for item in allowed[self.trading_mode]))
            raise ValueError(
                f"{self.trading_mode.value} does not support {self.instrument_type.value}; "
                f"allowed instruments: {choices}"
            )
        if self.max_correlated_positions > self.max_open_positions:
            raise ValueError("max_correlated_positions cannot exceed max_open_positions")
        if self.weekly_loss_limit_pct < self.daily_loss_limit_pct:
            raise ValueError("weekly_loss_limit_pct cannot be below daily_loss_limit_pct")
        return self
