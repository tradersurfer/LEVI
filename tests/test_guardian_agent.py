from levi.agents import GuardianAgent
from levi.profiles.models import ExecutionMode
from tests.phase4_helpers import risk_request
def assess(**kw): return GuardianAgent().analyze(risk_request(**kw))
def test_guardian_allows_valid_paper_request(): assert assess().allowed
def test_guardian_enforces_paper_mode():
 p=risk_request().profile.model_copy(update={"execution_mode":ExecutionMode.HUMAN_APPROVED}); assert not assess(profile=p).allowed
def test_guardian_enforces_dte(): assert "minimum DTE not met" in assess(dte=1).violations
def test_guardian_enforces_risk_budget(): assert not assess(maximum_loss=500).allowed
def test_guardian_enforces_loss_limit(): assert not assess(daily_loss_pct=3).allowed
def test_guardian_enforces_buying_power(): assert not assess(maximum_loss=6000).allowed
def test_guardian_blocks_market_order(): assert "market orders are prohibited" in assess(order_type="market").violations
def test_guardian_blocks_stale_quote(): assert "fresh quote required" in assess(quote_age_seconds=30).violations
def test_guardian_uses_three_second_options_freshness(): assert "fresh quote required" in assess(quote_age_seconds=4).violations
def test_guardian_blocks_averaging_down(): assert not assess(averaging_down=True).allowed
def test_guardian_requires_approval(): assert not assess(approval_reference=None).allowed
