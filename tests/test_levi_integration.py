"""
tests/test_levi_integration.py

Integration test: verify SCOUT, ATLAS, and LENS are called inside _attempt_entry
before the consensus vote, their outputs reach the metrics dict, and no
Tastytrade API calls are made during the scan.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest


# ── shared mock outputs ──────────────────────────────────────────────────────

SCOUT_OUT = {
    "sentiment": "BULLISH",
    "trending_tickers": ["NVDA"],
    "key_signals": ["Fed hold confirmed"],
    "confidence": 0.82,
    "source_count": 4,
    "perplexity_verified": True,
    "raw_grok_response": "mocked",
    "timestamp": "2026-07-04T10:00:00+00:00",
}

ATLAS_OUT = {
    "macro_regime": "RISK_ON",
    "catalysts_ahead": ["CPI tomorrow"],
    "sector_bias": "BULLISH",
    "trade_bias": "GO",
    "confidence": 0.78,
    "timestamp": "2026-07-04T10:00:00+00:00",
}

LENS_OUT = {
    "setup_quality": "A",
    "entry_zone": (500.0, 505.0),
    "target": 520.0,
    "stop": 492.0,
    "iv_rank": 38.0,
    "unusual_activity": True,
    "confidence": 0.84,
    "trace_triggered": False,
    "timestamp": "2026-07-04T10:00:00+00:00",
}


# ── minimal Signal stub (avoids importing Yahoo/fetch deps at import time) ───

@dataclass
class _Signal:
    symbol: str = "NVDA"
    tier: str = "CORE"
    direction: str = "CALL"
    price: float = 135.0
    ema20: float = 133.0
    sma50: float = 130.0
    rsi14: float = 58.0
    bb_upper: float = 138.0
    bb_lower: float = 128.0
    pct5d: float = 1.8
    reasons: list = None
    confidence: str = "HIGH"

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = ["EMA20 > SMA50"]


# ── helper to build minimal fake chain so find_option succeeds ───────────────

def _fake_chain():
    expiration = (date.today() + timedelta(days=21)).isoformat()
    return [
        {
            "expiration-date": expiration,
            "strikes": [
                {
                    "strike-price": "135",
                    "call": {
                        "symbol": "NVDA 260719C00135000",
                        "bid": "4.80",
                        "ask": "5.00",
                        "delta": "0.36",
                    },
                }
            ],
        }
    ]


# ── test ─────────────────────────────────────────────────────────────────────

def test_sub_agents_called_and_metrics_populated_no_tt_calls(monkeypatch):
    """
    SCOUT, ATLAS, and LENS are called exactly once inside _attempt_entry.
    Their outputs are forwarded into the metrics dict passed to ConsensusEngine.
    No Tastytrade place_order call is made.
    """
    # Patch sub-agent singletons on the module before import
    with (
        patch("agents.scout.Scout.scan", return_value=SCOUT_OUT) as mock_scout,
        patch("agents.atlas.Atlas.analyze", return_value=ATLAS_OUT) as mock_atlas,
        patch("agents.lens.Lens.analyze", return_value=LENS_OUT) as mock_lens,
    ):
        # Import bot after patches are in place so singletons pick up mocks
        import bot.levi_bot as lb  # noqa: PLC0415

        # Stub out network helpers that would hit Yahoo / Tastytrade
        monkeypatch.setattr(lb, "fetch_rsi15", lambda _: 52.0)

        # Build bot instance with a mocked TT session
        bot = lb.JECIOptionsBot.__new__(lb.JECIOptionsBot)
        bot.trades = {}
        bot.stopped_out_today = set()
        bot._blocklist_day = date.today()
        bot.state_eng = MagicMock()

        tt = MagicMock()
        tt.accounts = {"CORE": "ACCT-001"}
        tt.get_balance.return_value = 100_000.0
        tt.get_option_chain.return_value = _fake_chain()
        bot.tt = tt

        # Capture metrics dict passed to consensus
        captured_metrics: dict = {}

        def fake_consensus_evaluate(proposal, metrics):
            captured_metrics.update(metrics)
            result = MagicMock()
            result.approved = False          # don't proceed to execute
            result.votes = "MOAT-PASS/CONSENSUS-SKIP"
            result.notes = []
            return result

        consensus = MagicMock()
        consensus.evaluate.side_effect = fake_consensus_evaluate
        consensus.agents_online.return_value = {
            "grok": True, "claude": True, "deepseek": True
        }
        bot.consensus = consensus

        # Build minimal market-state report
        report = MagicMock()
        report.state.value = "NORMAL"
        report.locks = {}

        sig = _Signal()

        # Call _attempt_entry directly
        lb.CONSENSUS_REQUIRED = True
        bot._attempt_entry("CORE", sig, report)

        # ── assertions ────────────────────────────────────────────────────────

        # Sub-agents called exactly once each
        mock_scout.assert_called_once_with("NVDA")
        mock_atlas.assert_called_once_with("NVDA")
        mock_lens.assert_called_once_with("NVDA", "CALL")

        # Consensus was called (moat passed → consensus reached)
        consensus.evaluate.assert_called_once()

        # All 9 new keys present in metrics
        new_keys = [
            "x_sentiment", "x_confidence", "x_signals",
            "macro_regime", "macro_bias", "catalysts",
            "setup_quality", "lens_confidence", "trace_triggered",
        ]
        missing = [k for k in new_keys if k not in captured_metrics]
        assert not missing, f"Missing metrics keys: {missing}"

        # Values match mock outputs
        assert captured_metrics["x_sentiment"]    == SCOUT_OUT["sentiment"]
        assert captured_metrics["x_confidence"]   == SCOUT_OUT["confidence"]
        assert captured_metrics["x_signals"]      == SCOUT_OUT["key_signals"]
        assert captured_metrics["macro_regime"]   == ATLAS_OUT["macro_regime"]
        assert captured_metrics["macro_bias"]     == ATLAS_OUT["trade_bias"]
        assert captured_metrics["catalysts"]      == ATLAS_OUT["catalysts_ahead"]
        assert captured_metrics["setup_quality"]  == LENS_OUT["setup_quality"]
        assert captured_metrics["lens_confidence"]== LENS_OUT["confidence"]
        assert captured_metrics["trace_triggered"]== LENS_OUT["trace_triggered"]

        # No Tastytrade order placed
        tt.place_order.assert_not_called()
