from __future__ import annotations
from dataclasses import dataclass
from .models import AgentDecision, ConsensusDecision
@dataclass(frozen=True)
class DecisionNarrative:
    summary:str; evidence_ids:tuple[str,...]; warnings:tuple[str,...]
class ScribeAgent:
    agent_name="SCRIBE"
    def summarize(self,decisions:tuple[AgentDecision,...],consensus:ConsensusDecision)->DecisionNarrative:
        evidence=tuple(dict.fromkeys(eid for d in decisions for eid in d.evidence_ids))
        lines=[f"{d.agent_name}: {d.verdict.value} ({d.confidence:.2f}) - {d.summary}" for d in decisions]
        outcome="approved" if consensus.approved else "blocked"
        return DecisionNarrative(f"Consensus {outcome}. "+" ".join(lines),evidence,tuple(consensus.warnings))
