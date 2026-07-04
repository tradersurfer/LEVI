"""
tests/test_risk_moat.py — Master Risk Moat unit tests (must all pass before commit)
"""

import pytest
from bot.consensus_engine import RiskMoat, TradeProposal

# ── base clean proposal (should pass moat) ───────────────────────────────────
BASE = dict(
    account_tier="CORE",
    symbol="NVDA",
    direction="CALL",
    option_symbol="NVDA 240119C00500000",
    strike=500.0,
    dte=21,
    premium=1.20,       # $120 total (1 contract)
    quantity=1,
    net_liq=100_000.0,
    rsi15=50.0,
    market_state="NORMAL",
    state_locks={},
)


def p(**kwargs):
    return TradeProposal(**{**BASE, **kwargs})


# 1. 1-DTE → REJECTED (4DTE minimum)
def test_1dte_rejected():
    ok, fails = RiskMoat.validate(p(dte=1))
    assert not ok
    assert any("4DTE" in f or "DTE" in f for f in fails)


# 2a. Sandbox $151 total premium → REJECTED
def test_sandbox_over_cap_rejected():
    # premium=1.51, qty=1 → total_cost = $151.00
    ok, fails = RiskMoat.validate(p(account_tier="SANDBOX", premium=1.51, quantity=1))
    assert not ok
    assert any("SANDBOX CAP" in f or "150" in f for f in fails)


# 2b. Sandbox $149 → passes that check
def test_sandbox_under_cap_passes():
    ok, fails = RiskMoat.validate(p(account_tier="SANDBOX", premium=1.49, quantity=1))
    # should pass the sandbox cap rule (may still pass overall)
    cap_fails = [f for f in fails if "SANDBOX CAP" in f or "150" in f]
    assert len(cap_fails) == 0


# 3. Core position > 3.29% net liq → REJECTED
def test_position_over_pct_rejected():
    # net_liq=100_000, max=3.29% → $3,290; set premium=33.0, qty=1 → $3,300
    ok, fails = RiskMoat.validate(p(premium=33.0, quantity=1, net_liq=100_000.0))
    assert not ok
    assert any("POSITION RATIO" in f or "3.29" in f for f in fails)


# 4. CALL with rsi15=72 → REJECTED (RSI long lockout)
def test_call_rsi_overbought_rejected():
    ok, fails = RiskMoat.validate(p(direction="CALL", rsi15=72.0))
    assert not ok
    assert any("RSI LOCKOUT" in f for f in fails)


# 5. PUT with rsi15=15 → REJECTED (RSI short lockout)
def test_put_rsi_oversold_rejected():
    ok, fails = RiskMoat.validate(p(direction="PUT", rsi15=15.0))
    assert not ok
    assert any("RSI LOCKOUT" in f for f in fails)


# 6. PUT during WATERFALL locks → REJECTED
def test_put_waterfall_blocked():
    ok, fails = RiskMoat.validate(p(
        direction="PUT",
        market_state="WATERFALL",
        state_locks={"block_puts": True, "min_dte_override": 60},
        dte=90,   # pass DTE override, only test the puts block
    ))
    assert not ok
    assert any("short execution LOCKED" in f or "block_puts" in f or "LOCKED" in f for f in fails)


# 7a. DTE=30 during WATERFALL min_dte_override=60 → REJECTED
def test_dte30_waterfall_min60_rejected():
    ok, fails = RiskMoat.validate(p(
        direction="CALL",
        dte=30,
        market_state="WATERFALL",
        state_locks={"min_dte_override": 60},
    ))
    assert not ok
    assert any("DTE >= 60" in f or "min_dte_override" in f or "60" in f for f in fails)


# 7b. DTE=90 during WATERFALL min_dte_override=60 → passes that check
def test_dte90_waterfall_min60_passes():
    ok, fails = RiskMoat.validate(p(
        direction="CALL",
        dte=90,
        market_state="WATERFALL",
        state_locks={"min_dte_override": 60},
    ))
    dte_fails = [f for f in fails if "min_dte_override" in f or "DTE >= 60" in f]
    assert len(dte_fails) == 0


# 8. Clean proposal (DTE=21, $120, rsi15=50, NORMAL) → moat passes
def test_clean_proposal_passes():
    ok, fails = RiskMoat.validate(p())
    assert ok, f"Expected moat to pass but got: {fails}"
