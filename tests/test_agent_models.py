import pytest
from levi.agents.models import AgentVerdict
from tests.phase4_helpers import agent_decision,evidence,request
def test_decision_accepts_bounds(): assert agent_decision("SCOUT",confidence=0).confidence==0
def test_decision_rejects_low_confidence():
 with pytest.raises(ValueError): agent_decision("SCOUT",confidence=-.1)
def test_decision_rejects_high_confidence():
 with pytest.raises(ValueError): agent_decision("SCOUT",confidence=1.1)
def test_request_normalizes_symbol(): assert request(symbol="spy").symbol=="SPY"
def test_request_rejects_cross_user_evidence():
 with pytest.raises(ValueError): request((evidence(user="other"),))
def test_verdict_contract_complete(): assert len(AgentVerdict)==5
