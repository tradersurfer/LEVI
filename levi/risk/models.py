from dataclasses import dataclass,field
from datetime import datetime,timezone
from levi.market_data.models import QuoteValidationResult
from levi.profiles.models import UserTradingProfile
@dataclass(frozen=True)
class TradeRiskRequest:
    profile:UserTradingProfile; dte:int; maximum_loss:float; daily_loss_pct:float; weekly_loss_pct:float
    open_positions:int; correlated_positions:int; averaging_down:bool; order_type:str; limit_price:float|None
    quote_validation:QuoteValidationResult|None; quote_age_seconds:float|None; buying_power:float
    approval_reference:str|None; minimum_dte:int=4
@dataclass(frozen=True)
class GuardianDecision:
    allowed:bool; violations:tuple[str,...]; warnings:tuple[str,...]; evaluated_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc)); rule_version:str="1.0"
