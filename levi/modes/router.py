"""Select mode policy without performing trading analysis."""

from dataclasses import dataclass

from levi.profiles.models import InstrumentType, TradingMode, UserTradingProfile


@dataclass(frozen=True)
class ModePolicy:
    mode: TradingMode
    allowed_instruments: list[InstrumentType]
    required_evidence: list[str]
    preferred_evidence: list[str]
    risk_policy_name: str
    permitted_holding_period: str
    required_timeframes: list[str]
    output_contract: str


def resolve_mode_policy(profile: UserTradingProfile) -> ModePolicy:
    """Return the deterministic policy for a validated profile."""
    if profile.trading_mode is TradingMode.DAY_TRADING:
        required = [
            "current spot", "timestamp", "5-minute chart", "15-minute chart",
            "volume", "account value", "buying power",
        ]
        preferred = ["VWAP", "RSI", "MACD", "flow data", "market context", "SPY or QQQ context"]
        policy = ModePolicy(
            mode=profile.trading_mode,
            allowed_instruments=[InstrumentType.OPTIONS, InstrumentType.POLYMARKET],
            required_evidence=required,
            preferred_evidence=preferred,
            risk_policy_name="day_trading_risk",
            permitted_holding_period="intraday",
            required_timeframes=["5m", "15m"],
            output_contract="trade_analysis",
        )
    elif profile.trading_mode is TradingMode.SWING_TRADING:
        required = [
            "current spot", "daily chart", "4-hour chart", "expiration",
            "account value", "open positions",
        ]
        preferred = ["IV", "expected move", "earnings date", "macro calendar", "sector context"]
        policy = ModePolicy(
            mode=profile.trading_mode,
            allowed_instruments=[InstrumentType.OPTIONS, InstrumentType.POLYMARKET],
            required_evidence=required,
            preferred_evidence=preferred,
            risk_policy_name="swing_trading_risk",
            permitted_holding_period="multi-day to multi-week",
            required_timeframes=["4h", "1d"],
            output_contract="trade_analysis",
        )
    else:
        policy = ModePolicy(
            mode=profile.trading_mode,
            allowed_instruments=[InstrumentType.STOCKS],
            required_evidence=["ticker", "current position or desired position", "account value", "time horizon"],
            preferred_evidence=[
                "financial statements", "valuation data", "earnings history",
                "sector exposure", "portfolio concentration",
            ],
            risk_policy_name="investing_holding_risk",
            permitted_holding_period="long term",
            required_timeframes=[],
            output_contract="investment_analysis",
        )

    if profile.instrument_type is InstrumentType.OPTIONS:
        required_with_chain = list(policy.required_evidence)
        insert_at = required_with_chain.index("account value")
        required_with_chain.insert(insert_at, "options chain")
        policy = ModePolicy(**{**policy.__dict__, "required_evidence": required_with_chain})
    return policy
