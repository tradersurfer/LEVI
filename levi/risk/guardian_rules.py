from levi.profiles.models import ExecutionMode,InstrumentType,TradingMode
from .models import GuardianDecision,TradeRiskRequest
class GuardianRules:
    def evaluate(self,r:TradeRiskRequest)->GuardianDecision:
        v=[]; p=r.profile
        if p.execution_mode is not ExecutionMode.PAPER_TRADING: v.append("execution mode must be paper_trading")
        if r.dte<r.minimum_dte: v.append("minimum DTE not met")
        if r.maximum_loss>float(p.account_value)*float(p.risk_per_trade_pct)/100: v.append("maximum risk per trade exceeded")
        if r.daily_loss_pct>=p.daily_loss_limit_pct: v.append("daily loss limit reached")
        if r.weekly_loss_pct>=p.weekly_loss_limit_pct: v.append("weekly loss limit reached")
        if r.open_positions>=p.max_open_positions: v.append("maximum open positions reached")
        if r.correlated_positions>=p.max_correlated_positions: v.append("maximum correlated positions reached")
        if r.averaging_down: v.append("averaging down is prohibited")
        if r.order_type.lower()!="limit": v.append("market orders are prohibited")
        if r.limit_price is None or r.limit_price<=0: v.append("valid limit price required")
        if r.quote_validation is None or not r.quote_validation.is_valid: v.append("valid quote required")
        maximum_quote_age = 3 if p.instrument_type is InstrumentType.OPTIONS else 15
        if r.quote_age_seconds is None or r.quote_age_seconds>maximum_quote_age: v.append("fresh quote required")
        valid_combo=(p.trading_mode in {TradingMode.DAY_TRADING,TradingMode.SWING_TRADING} and p.instrument_type in {InstrumentType.OPTIONS,InstrumentType.POLYMARKET}) or (p.trading_mode is TradingMode.INVESTING_HOLDING and p.instrument_type is InstrumentType.STOCKS)
        if not valid_combo: v.append("unsupported trading mode and instrument combination")
        if r.maximum_loss>r.buying_power: v.append("insufficient buying power")
        if not r.approval_reference: v.append("approval reference required")
        return GuardianDecision(not v,tuple(v),())
