from levi.agents import AgentVerdict,AtlasAgent
from levi.evidence.models import EvidenceType
from levi.llm import MockLLMAdapter
from tests.phase4_helpers import evidence,request
from datetime import datetime,timezone,timedelta
def test_atlas_missing_macro(): assert AtlasAgent(MockLLMAdapter()).analyze(request()).verdict is AgentVerdict.INSUFFICIENT_EVIDENCE
def test_atlas_macro_decision():
 d=AtlasAgent(MockLLMAdapter([{"verdict":"bearish","confidence":.75,"summary":"risk off"}])).analyze(request((evidence(EvidenceType.PDF,metadata={"topic":"macro regime"},captured_at=datetime.now(timezone.utc)),)))
 assert d.verdict is AgentVerdict.BEARISH
def test_atlas_neutral_regime():
 d=AtlasAgent(MockLLMAdapter([{"verdict":"neutral","confidence":.8,"summary":"mixed"}])).analyze(request((evidence(EvidenceType.TEXT_NOTE,metadata={"topic":"rates"},captured_at=datetime.now(timezone.utc)),)))
 assert d.verdict is AgentVerdict.NEUTRAL
def test_atlas_clamps_model_confidence():
 d=AtlasAgent(MockLLMAdapter([{"verdict":"bullish","confidence":9}])).analyze(request((evidence(EvidenceType.TEXT_NOTE,metadata={"topic":"fomc"},captured_at=datetime.now(timezone.utc)),)))
 assert d.confidence==1
def test_atlas_stale_macro_is_insufficient():
 item=evidence(EvidenceType.TEXT_NOTE,metadata={"topic":"macro"},captured_at=datetime.now(timezone.utc)-timedelta(days=2))
 assert AtlasAgent(MockLLMAdapter()).analyze(request((item,))).verdict is AgentVerdict.INSUFFICIENT_EVIDENCE
