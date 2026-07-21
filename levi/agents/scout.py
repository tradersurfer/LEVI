from levi.evidence.models import EvidenceType
from ._hosted import HostedEvidenceAgent
from .models import AgentVerdict,decision
class ScoutAgent(HostedEvidenceAgent):
    agent_name="SCOUT"; model_env="LEVI_SCOUT_MODEL"; prompt="Analyze only supplied sentiment, flow, news, and crowd-positioning evidence. Social consensus is not price confirmation. Return JSON verdict, confidence, summary, reasoning, warnings."
    def select_evidence(self,request):
        relevant=[]
        for e in request.evidence:
            tags=" ".join((e.source_name,str(e.metadata),str(e.parsed_payload))).lower()
            if e.evidence_type in {EvidenceType.TEXT_NOTE,EvidenceType.TRADE_JOURNAL,EvidenceType.LIVE_FEED} and any(k in tags for k in ("sentiment","flow","news","crowd","social")): relevant.append(e)
        return relevant
    def analyze(self,request):
        relevant=self.select_evidence(request)
        sentiments={str((e.metadata or {}).get("sentiment","")).lower() for e in relevant}
        if "bullish" in sentiments and "bearish" in sentiments:
            return decision(self.agent_name,request,AgentVerdict.NEUTRAL,0.5,"Supplied crowd sentiment is contradictory",evidence_ids=tuple(e.evidence_id for e in relevant),warnings=("Social sentiment conflicts and is not price confirmation",))
        return super().analyze(request)
