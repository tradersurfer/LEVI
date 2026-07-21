from typing import Protocol
from .models import AgentAnalysisRequest, AgentDecision
class SpecialistAgent(Protocol):
    agent_name: str
    def analyze(self, request: AgentAnalysisRequest) -> AgentDecision: ...
