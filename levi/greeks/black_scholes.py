"""Deterministic Black-Scholes diagnostics (365-day annualization)."""
from __future__ import annotations
import math
from dataclasses import dataclass
from enum import Enum
class OptionType(str,Enum): CALL="call"; PUT="put"
@dataclass(frozen=True)
class BlackScholesInputs:
    spot:float; strike:float; time_to_expiration_years:float; risk_free_rate:float; volatility:float; option_type:OptionType
    market_price:float|None=None; bid:float|None=None; ask:float|None=None
    def __post_init__(self):
        if self.spot<=0 or self.strike<=0: raise ValueError("spot and strike must be positive")
        if self.time_to_expiration_years<=0: raise ValueError("option must have positive time to expiration")
        if self.volatility<=0: raise ValueError("volatility must be positive")
        if self.bid is not None and self.bid<0: raise ValueError("bid cannot be negative")
        if self.ask is not None and self.bid is not None and self.ask<self.bid: raise ValueError("ask cannot be below bid")
@dataclass(frozen=True)
class BlackScholesResult:
    calculated_value:float; delta:float; gamma:float; theta_per_day:float; vega_per_vol_point:float; rho_per_rate_point:float
    intrinsic_value:float; extrinsic_value:float; moneyness:str; break_even:float; spread_pct:float|None; liquid:bool|None; source:str="calculated_black_scholes"
def _cdf(x): return .5*(1+math.erf(x/math.sqrt(2)))
def _pdf(x): return math.exp(-x*x/2)/math.sqrt(2*math.pi)
def calculate(i:BlackScholesInputs)->BlackScholesResult:
    t=i.time_to_expiration_years; root=math.sqrt(t); d1=(math.log(i.spot/i.strike)+(i.risk_free_rate+i.volatility*i.volatility/2)*t)/(i.volatility*root); d2=d1-i.volatility*root; disc=math.exp(-i.risk_free_rate*t); pdf=_pdf(d1)
    if i.option_type is OptionType.CALL:
        value=i.spot*_cdf(d1)-i.strike*disc*_cdf(d2); delta=_cdf(d1); theta=(-(i.spot*pdf*i.volatility)/(2*root)-i.risk_free_rate*i.strike*disc*_cdf(d2))/365; rho=i.strike*t*disc*_cdf(d2)/100; intrinsic=max(0,i.spot-i.strike); breakeven=i.strike+(i.market_price if i.market_price is not None else value)
    else:
        value=i.strike*disc*_cdf(-d2)-i.spot*_cdf(-d1); delta=_cdf(d1)-1; theta=(-(i.spot*pdf*i.volatility)/(2*root)+i.risk_free_rate*i.strike*disc*_cdf(-d2))/365; rho=-i.strike*t*disc*_cdf(-d2)/100; intrinsic=max(0,i.strike-i.spot); breakeven=i.strike-(i.market_price if i.market_price is not None else value)
    gamma=pdf/(i.spot*i.volatility*root); vega=i.spot*pdf*root/100; extrinsic=max(0,(i.market_price if i.market_price is not None else value)-intrinsic)
    if abs(i.spot-i.strike)<1e-9: money="at_the_money"
    elif (i.option_type is OptionType.CALL and i.spot>i.strike) or (i.option_type is OptionType.PUT and i.spot<i.strike): money="in_the_money"
    else: money="out_of_the_money"
    spread=None; liquid=None
    if i.bid is not None and i.ask is not None:
        mid=(i.bid+i.ask)/2; spread=((i.ask-i.bid)/mid*100) if mid else float("inf"); liquid=i.bid>0 and spread<=5
    return BlackScholesResult(
        calculated_value=round(value,8), delta=round(delta,8), gamma=round(gamma,8),
        theta_per_day=round(theta,8), vega_per_vol_point=round(vega,8),
        rho_per_rate_point=round(rho,8), intrinsic_value=round(intrinsic,8),
        extrinsic_value=round(extrinsic,8), moneyness=money,
        break_even=round(breakeven,8),
        spread_pct=None if spread is None else round(spread,8), liquid=liquid,
    )
