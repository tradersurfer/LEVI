from levi.agents import ConsensusEngine,ScribeAgent
from tests.phase4_helpers import agent_decision,guardian
def setup():
 ds=tuple(agent_decision(n) for n in ("SCOUT","ATLAS","LENS")); c=ConsensusEngine().evaluate(user_id="u1",symbol="SPY",decisions=ds,guardian=guardian()); return ds,c
def test_scribe_does_not_add_evidence():
 ds,c=setup(); assert set(ScribeAgent().summarize(ds,c).evidence_ids)=={"e1"}
def test_scribe_mentions_each_agent():
 ds,c=setup(); text=ScribeAgent().summarize(ds,c).summary; assert all(n in text for n in ("SCOUT","ATLAS","LENS"))
def test_scribe_does_not_vote(): assert not hasattr(ScribeAgent(),"evaluate")
