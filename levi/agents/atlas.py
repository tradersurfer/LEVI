from datetime import datetime,timezone,timedelta
from levi.evidence.models import EvidenceType
from ._hosted import HostedEvidenceAgent
from .models import AgentVerdict,decision
class AtlasAgent(HostedEvidenceAgent):
    agent_name="ATLAS"; model_env="LEVI_ATLAS_MODEL"; prompt="Analyze only supplied macro, rates, volatility, regime, and catalyst evidence. Preserve uncertainty. Return JSON verdict, confidence, summary, reasoning, warnings."
    def select_evidence(self,request):
        relevant=[]
        for e in request.evidence:
            tags=" ".join((e.source_name,str(e.metadata),str(e.parsed_payload))).lower()
            if any(k in tags for k in ("macro","rates","fomc","catalyst","regime","vix","volatility")): relevant.append(e)
        return relevant
    def analyze(self,request):
        relevant=self.select_evidence(request)
        current=[e for e in relevant if e.captured_at and request.requested_at-e.captured_at.astimezone(timezone.utc)<=timedelta(hours=24)]
        if relevant and not current:
            return decision(self.agent_name,request,AgentVerdict.INSUFFICIENT_EVIDENCE,0,"Macro evidence is stale",evidence_ids=tuple(e.evidence_id for e in relevant),warnings=("Macro evidence exceeds 24-hour freshness window",))
        return super().analyze(request)
