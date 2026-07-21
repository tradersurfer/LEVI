"""Canonical immutable contracts for LEVI specialist decisions."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4
from levi.evidence.models import EvidenceRecord
from levi.market_data.models import Quote
from levi.profiles.models import InstrumentType, TradingMode

class AgentVerdict(str, Enum):
    BULLISH="bullish"; BEARISH="bearish"; NEUTRAL="neutral"; BLOCK="block"; INSUFFICIENT_EVIDENCE="insufficient_evidence"

@dataclass(frozen=True)
class AgentAnalysisRequest:
    user_id: str; symbol: str; trading_mode: TradingMode; instrument_type: InstrumentType
    evidence: tuple[EvidenceRecord, ...]; quote: Quote|None; portfolio_context: Mapping[str, Any]
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    def __post_init__(self):
        if not self.user_id.strip() or not self.symbol.strip(): raise ValueError("user_id and symbol are required")
        if any(e.user_id != self.user_id for e in self.evidence): raise ValueError("evidence must belong to requesting user")
        object.__setattr__(self,"symbol",self.symbol.upper())
        object.__setattr__(self,"portfolio_context",MappingProxyType(dict(self.portfolio_context)))

@dataclass(frozen=True)
class AgentDecision:
    decision_id: str; user_id: str; symbol: str; agent_name: str; verdict: AgentVerdict
    confidence: float; summary: str; reasoning: tuple[str,...]; evidence_ids: tuple[str,...]
    warnings: tuple[str,...]; created_at: datetime; processing_time_ms: int
    metadata: Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not all((self.decision_id,self.user_id,self.symbol,self.agent_name)): raise ValueError("decision identity fields are required")
        if not 0<=self.confidence<=1: raise ValueError("confidence must be between 0 and 1")
        if self.processing_time_ms<0: raise ValueError("processing_time_ms cannot be negative")
        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))

@dataclass(frozen=True)
class ConsensusDecision:
    consensus_id: str; user_id: str; symbol: str; approved: bool; verdict: AgentVerdict
    scout_decision_id: str; atlas_decision_id: str; lens_decision_id: str
    guardian_blocked: bool; guardian_reasons: tuple[str,...]; confidence: float
    created_at: datetime; warnings: tuple[str,...]=()
    def __post_init__(self):
        if not 0<=self.confidence<=1: raise ValueError("confidence must be between 0 and 1")

def decision(agent:str, request:AgentAnalysisRequest, verdict:AgentVerdict, confidence:float, summary:str, *, reasoning=(), evidence_ids=(), warnings=(), processing_time_ms=0, metadata=None):
    return AgentDecision(str(uuid4()),request.user_id,request.symbol,agent,verdict,confidence,summary,tuple(reasoning),tuple(evidence_ids),tuple(warnings),datetime.now(timezone.utc),processing_time_ms,metadata or {})
