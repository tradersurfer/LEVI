from datetime import datetime,timezone
from levi.agents.models import AgentAnalysisRequest,AgentDecision,AgentVerdict
from levi.evidence.models import EvidenceRecord,EvidenceType
from levi.market_data.models import QuoteValidationResult
from levi.profiles.models import UserTradingProfile
from levi.risk.models import GuardianDecision,TradeRiskRequest
def evidence(kind=EvidenceType.CHART,user="u1",eid="e1",**kw): return EvidenceRecord(evidence_id=eid,user_id=user,evidence_type=kind,source_name=kw.pop("source_name","test"),**kw)
def request(evidence_items=(),user="u1",symbol="SPY"):
 p=UserTradingProfile(user_id=user,display_name="User",account_value=10000,buying_power=5000)
 return AgentAnalysisRequest(user,symbol,p.trading_mode,p.instrument_type,tuple(evidence_items),None,{})
def agent_decision(name,verdict=AgentVerdict.BULLISH,confidence=.8,user="u1",symbol="SPY",did=None): return AgentDecision(did or name.lower(),user,symbol,name,verdict,confidence,"summary",("reason",),("e1",),(),datetime.now(timezone.utc),1,{})
def guardian(allowed=True): return GuardianDecision(allowed,() if allowed else ("blocked",),())
def risk_request(**kw):
 p=kw.pop("profile",UserTradingProfile(user_id="u1",display_name="User",account_value=10000,buying_power=5000))
 base=dict(profile=p,dte=10,maximum_loss=100,daily_loss_pct=0,weekly_loss_pct=0,open_positions=0,correlated_positions=0,averaging_down=False,order_type="limit",limit_price=1,quote_validation=QuoteValidationResult(True,[],[]),quote_age_seconds=1,buying_power=5000,approval_reference="approval")
 return TradeRiskRequest(**(base|kw))
