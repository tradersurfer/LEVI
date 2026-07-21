from levi.agents import AgentVerdict,ConsensusEngine
from tests.phase4_helpers import agent_decision,guardian
def decisions(verdict=AgentVerdict.BULLISH,confidence=.8): return tuple(agent_decision(n,verdict,confidence) for n in ("SCOUT","ATLAS","LENS"))
def evaluate(items=None,g=None): return ConsensusEngine().evaluate(user_id="u1",symbol="SPY",decisions=items or decisions(),guardian=g or guardian())
def test_unanimous_bullish_approved(): assert evaluate().approved
def test_unanimous_bearish_approved(): assert evaluate(decisions(AgentVerdict.BEARISH)).approved
def test_two_to_one_rejected(): assert not evaluate(decisions()[:2]+(agent_decision("LENS",AgentVerdict.BEARISH),)).approved
def test_neutral_rejected(): assert not evaluate(decisions(AgentVerdict.NEUTRAL)).approved
def test_missing_vote_rejected(): assert not evaluate(decisions()[:2]).approved
def test_low_confidence_rejected(): assert not evaluate(decisions(confidence=.69)).approved
def test_guardian_veto(): assert evaluate(g=guardian(False)).guardian_blocked
def test_cross_user_decision_rejected(): assert not evaluate(decisions()[:2]+(agent_decision("LENS",user="u2"),)).approved
def test_deterministic_outcome():
 a=evaluate(); b=evaluate(); assert (a.approved,a.verdict,a.confidence)==(b.approved,b.verdict,b.confidence)
def test_configurable_threshold(): assert ConsensusEngine(.9).evaluate(user_id="u1",symbol="SPY",decisions=decisions(confidence=.8),guardian=guardian()).approved is False
