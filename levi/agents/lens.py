from levi.evidence.models import EvidenceType
from levi.profiles.models import TradingMode
from ._hosted import HostedEvidenceAgent
from .models import AgentVerdict,decision
class LensAgent(HostedEvidenceAgent):
    agent_name="LENS"; model_env="LEVI_LENS_MODEL"; prompt="Analyze only supplied chart structure and validated quote. Never invent levels or treat a daily chart as intraday confirmation. Return JSON verdict, confidence, summary, reasoning, warnings."
    def select_evidence(self,request):
        return [e for e in request.evidence if e.evidence_type in {EvidenceType.CHART,EvidenceType.GRAPH} and (not e.ticker_symbols or request.symbol in {t.upper() for t in e.ticker_symbols})]
    def analyze(self,request):
        relevant=self.select_evidence(request)
        if request.trading_mode is TradingMode.DAY_TRADING and relevant and not any((e.timeframe or "").lower() in {"5m","5-minute","15m","15-minute"} for e in relevant):
            return decision(self.agent_name,request,AgentVerdict.INSUFFICIENT_EVIDENCE,0,"Intraday chart evidence is missing",evidence_ids=tuple(e.evidence_id for e in relevant),warnings=("Daily or higher timeframe does not confirm an intraday setup",))
        return super().analyze(request)
