from levi.agents import AgentVerdict,ScoutAgent
from levi.evidence.models import EvidenceType
from levi.llm import MockLLMAdapter
from tests.phase4_helpers import evidence,request
def test_scout_missing_evidence(): assert ScoutAgent(MockLLMAdapter()).analyze(request()).verdict is AgentVerdict.INSUFFICIENT_EVIDENCE
def test_scout_uses_sentiment_evidence():
 d=ScoutAgent(MockLLMAdapter([{"verdict":"bullish","confidence":.8,"summary":"crowd positive","reasoning":[]}])).analyze(request((evidence(EvidenceType.TEXT_NOTE,metadata={"topic":"sentiment"}),)))
 assert d.verdict is AgentVerdict.BULLISH and d.evidence_ids==("e1",)
def test_scout_unknown_verdict_fails_safe():
 d=ScoutAgent(MockLLMAdapter([{"verdict":"moon","confidence":.9}])).analyze(request((evidence(EvidenceType.LIVE_FEED,metadata={"topic":"flow"}),)))
 assert d.verdict is AgentVerdict.INSUFFICIENT_EVIDENCE
def test_scout_provider_failure_abstains():
 d=ScoutAgent(MockLLMAdapter([TimeoutError()])).analyze(request((evidence(EvidenceType.TEXT_NOTE,metadata={"topic":"news"}),)))
 assert d.confidence==0
def test_scout_conflicting_sentiment_is_neutral():
 items=(evidence(EvidenceType.TEXT_NOTE,eid="bull",metadata={"topic":"sentiment","sentiment":"bullish"}),evidence(EvidenceType.TEXT_NOTE,eid="bear",metadata={"topic":"sentiment","sentiment":"bearish"}))
 assert ScoutAgent(MockLLMAdapter()).analyze(request(items)).verdict is AgentVerdict.NEUTRAL
