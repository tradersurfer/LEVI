from __future__ import annotations
import os
from datetime import datetime,timezone
from uuid import uuid4
from .models import AgentDecision,AgentVerdict,ConsensusDecision
class ConsensusEngine:
    required=("SCOUT","ATLAS","LENS")
    def __init__(self,min_confidence=None): self.min_confidence=float(min_confidence if min_confidence is not None else os.getenv("LEVI_CONSENSUS_MIN_CONFIDENCE","0.70"))
    def evaluate(self,*,user_id:str,symbol:str,decisions:tuple[AgentDecision,...],guardian)->ConsensusDecision:
        found={d.agent_name.upper():d for d in decisions}; warnings=[]
        missing=[name for name in self.required if name not in found]
        if missing: warnings.append("Missing required decisions: "+", ".join(missing))
        selected=[found[n] for n in self.required if n in found]
        verdicts={d.verdict for d in selected}
        ids={n:found[n].decision_id if n in found else "" for n in self.required}
        invalid=any(d.user_id!=user_id or d.symbol.upper()!=symbol.upper() for d in selected)
        if invalid: warnings.append("Decision ownership or symbol mismatch")
        low=any(d.confidence<self.min_confidence for d in selected)
        if low: warnings.append("Minimum confidence not met")
        prohibited=any(d.verdict in {AgentVerdict.NEUTRAL,AgentVerdict.BLOCK,AgentVerdict.INSUFFICIENT_EVIDENCE} for d in selected)
        unanimous=len(selected)==3 and len(verdicts)==1 and not prohibited
        blocked=not guardian.allowed
        if blocked: warnings.append("GUARDIAN veto")
        approved=unanimous and not missing and not invalid and not low and not blocked
        verdict=selected[0].verdict if approved else (AgentVerdict.BLOCK if blocked else AgentVerdict.NEUTRAL)
        confidence=min((d.confidence for d in selected),default=0) if approved else 0
        return ConsensusDecision(str(uuid4()),user_id,symbol.upper(),approved,verdict,ids["SCOUT"],ids["ATLAS"],ids["LENS"],blocked,tuple(guardian.violations),confidence,datetime.now(timezone.utc),tuple(warnings))
