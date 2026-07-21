from levi.agents import AgentVerdict,LensAgent
from levi.evidence.models import EvidenceType
from levi.llm import MockLLMAdapter
from tests.phase4_helpers import evidence,request
from levi.agents.models import AgentAnalysisRequest
from levi.profiles.models import TradingMode
def test_lens_missing_chart(): assert LensAgent(MockLLMAdapter()).analyze(request()).verdict is AgentVerdict.INSUFFICIENT_EVIDENCE
def test_lens_chart_decision():
 d=LensAgent(MockLLMAdapter([{"verdict":"bullish","confidence":.9,"summary":"aligned"}])).analyze(request((evidence(timeframe="5m",ticker_symbols=["SPY"]),)))
 assert d.verdict is AgentVerdict.BULLISH
def test_lens_wrong_ticker_ignored(): assert LensAgent(MockLLMAdapter()).analyze(request((evidence(ticker_symbols=["AAPL"]),))).confidence==0
def test_lens_graph_supported():
 d=LensAgent(MockLLMAdapter([{"verdict":"neutral","confidence":.7}])).analyze(request((evidence(EvidenceType.GRAPH),)))
 assert d.evidence_ids==("e1",)
def test_lens_daily_chart_does_not_confirm_day_trade():
 base=request((evidence(timeframe="1d"),)); day=AgentAnalysisRequest(base.user_id,base.symbol,TradingMode.DAY_TRADING,base.instrument_type,base.evidence,None,{})
 assert LensAgent(MockLLMAdapter()).analyze(day).verdict is AgentVerdict.INSUFFICIENT_EVIDENCE
