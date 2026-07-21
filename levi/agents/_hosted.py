from __future__ import annotations
import os, time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from levi.llm import LLMAdapter, LLMRequest
from .models import AgentAnalysisRequest, AgentDecision, AgentVerdict, decision

class HostedEvidenceAgent(ABC):
    agent_name=""; model_env=""; prompt=""
    def __init__(self,llm:LLMAdapter): self.llm=llm
    @abstractmethod
    def select_evidence(self,request:AgentAnalysisRequest): ...
    def analyze(self,request:AgentAnalysisRequest)->AgentDecision:
        started=time.perf_counter(); evidence=tuple(self.select_evidence(request))
        if not evidence: return decision(self.agent_name,request,AgentVerdict.INSUFFICIENT_EVIDENCE,0,"Required evidence is missing",warnings=("No relevant supplied evidence",))
        payload={"user_id":request.user_id,"symbol":request.symbol,"trading_mode":request.trading_mode.value,"instrument_type":request.instrument_type.value,"quote":None if request.quote is None else {"ticker":request.quote.ticker,"bid":request.quote.bid,"ask":request.quote.ask,"last":request.quote.last,"timestamp":request.quote.timestamp.isoformat()},"evidence":[{"evidence_id":e.evidence_id,"type":e.evidence_type.value,"captured_at":e.captured_at.isoformat() if e.captured_at else None,"timeframe":e.timeframe,"parsed_payload":e.parsed_payload,"metadata":e.metadata,"warnings":e.warnings} for e in evidence]}
        try: response=self.llm.complete(LLMRequest(os.getenv(self.model_env,""),self.prompt,payload))
        except Exception as exc: return decision(self.agent_name,request,AgentVerdict.INSUFFICIENT_EVIDENCE,0,"Specialist model failed safely",evidence_ids=tuple(e.evidence_id for e in evidence),warnings=(type(exc).__name__,),processing_time_ms=int((time.perf_counter()-started)*1000))
        raw=str(response.content.get("verdict","")).lower()
        try: verdict=AgentVerdict(raw)
        except ValueError: verdict=AgentVerdict.INSUFFICIENT_EVIDENCE
        try: confidence=max(0,min(1,float(response.content.get("confidence",0))))
        except (TypeError,ValueError): confidence=0
        reasoning=response.content.get("reasoning",[]); warnings=response.content.get("warnings",[])
        if not isinstance(reasoning,list): reasoning=[]
        if not isinstance(warnings,list): warnings=[]
        return decision(self.agent_name,request,verdict,confidence,str(response.content.get("summary","No summary")),reasoning=reasoning,evidence_ids=tuple(e.evidence_id for e in evidence),warnings=warnings,processing_time_ms=response.processing_time_ms)
