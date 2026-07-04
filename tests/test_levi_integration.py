# LEVI Integration Test

from unittest.mock import Mock, patch
from datetime import datetime, timezone

from agents.scout import Scout
from agents.atlas import Atlas
from agents.lens import Lens
from bot.consensus_engine import _extract_json # Helper for mock responses

# Constants
SYMBOLS = ["SPY", "NVDA"]
SCOUT_OUT = {
    "sentiment": "BULLISH", "trending_tickers": ["AAPL"], "key_signals": ["Fed speaker"],
    "confidence": 0.8, "source_count": 1, "perplexity_verified": True,
    "raw_grok_response": "Mock response", "timestamp": datetime.now(timezone.utc).isoformat()
}
ATLAS_OUT = {
    "macro_regime": "RISK_ON", "catalysts_ahead": ["Earnings report"],
    "sector_bias": "BULLISH", "trade_bias": "GO", "confidence": 0.85,
    "timestamp": datetime.now(timezone.utc).isoformat()
}
LENS_OUT = {
    "setup_quality": "A", "entry_zone": [100.0, 101.0], "target": 105.0,
    "stop": 98.0, "iv_rank": 60.0, "unusual_activity": True,
    "confidence": 0.81, "trace_triggered": False, "timestamp": datetime.now(timezone.utc).isoformat()
}

# Mock agent methods to return fixed values
def mock_scout_scan(watchlist=None):
    return SCOUT_OUT

def mock_atlas_analyze(symbol):
    return ATLAS_OUT

def mock_lens_analyze(symbol, chart_metrics=None):
    return LENS_OUT

def test_levi_scan_loop_integration(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "test-xai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity")
    monkeypatch.setenv("LEVI_CONFIG_PATH", "./levi_config.json")
    # Mocking out the actual bot run to test the scan loop logic in isolation
    # We'll verify the metrics dict construction and that no actual API calls are made

    # Patch agent methods to return predefined values
    with patch("agents.scout.Scout.scan", side_effect=mock_scout_scan), \
         patch("agents.atlas.Atlas.analyze", side_effect=mock_atlas_analyze), \
         patch("agents.lens.Lens.analyze", side_effect=mock_lens_analyze), \
         patch("bot.jeci_options_bot.TastytradeSession.place_order") as mock_place_order: # Ensure no TT calls

        # Need to load Levi config and initialize bot to access _handle method context
        from bot.jeci_options_bot import JECIOptionsBot, LEVI_CONFIG
        from bot.consensus_engine import ConsensusEngine # Needed for mocking

        # Simulate loading levi_config.json
        monkeypatch.setattr(__import__('bot.jeci_options_bot'), 'LEVI_CONFIG', {
            "agent_name": "LEVI", "operator": "JECI Group", "tiers": [
                {"id": "sandbox", "name": "Sandbox", "account_env": "ACCT_SANDBOX", "max_premium_per_trade": 150.00, "max_position_pct": 2.0, "zero_dte_enabled": False, "alerts_only": False, "swing_enabled": True, "long_hold_alerts": False},
                {"id": "core", "name": "Core", "account_env": "ACCT_CORE", "max_premium_per_trade": 500.00, "max_position_pct": 3.29, "zero_dte_enabled": True, "alerts_only": False, "swing_enabled": True, "long_hold_alerts": True},
                {"id": "hodl", "name": "HODL", "account_env": "ACCT_HODL", "max_premium_per_trade": 0, "max_position_pct": 0, "zero_dte_enabled": False, "alerts_only": True, "swing_enabled": False, "long_hold_alerts": True}
            ],
            "consensus": {"required": True, "timeout_sec": 25,
                          "agents": {"grok": {"model": "grok-4"}, "claude": {"model": "claude-sonnet-4-5"}, "deepseek": {"model": "deepseek/deepseek-r1"}}},
            "market_hours_only": True, "scan_interval_sec": 300
        })

        # Mocking necessary parts of the bot to isolate scan loop logic
        bot = JECIOptionsBot()
        bot.tt.accounts = {"CORE": "12345", "SANDBOX": "98765"} # Mock accounts
        bot.consensus = Mock(spec=ConsensusEngine) # Mock the consensus engine
        # Mock bot.consensus.evaluate to return a successful consensus result
        bot.consensus.evaluate.return_value.approved = True
        bot.consensus.evaluate.return_value.votes = "3/3" # Simulate successful vote
        bot.consensus.agents_online.return_value = {"grok": True, "claude": True, "deepseek": True}

        # Monkeypatch the _handle method to capture the metrics dict
        captured_metrics = {}
        original_handle = bot._handle
        def mock_handle(tier, sym, report):
            nonlocal captured_metrics
            if tier == "CORE" and sym == "SPY": # Targeting a specific call
                # Call original _handle to get the metrics dict built
                original_handle(tier, sym, report)
                # Access the metrics from bot._attempt_entry internal state (this is tricky to mock)
                # A simpler approach: re-construct what would have been passed if mock_attempt_entry was used
                # For now, we'll assert later that the expected keys *would* have been in metrics
                pass # Metrics will be checked indirectly via consensus evaluate args
            else:
                original_handle(tier, sym, report)

        monkeypatch.setattr(bot, '_handle', mock_handle)

        # Mocking the market state and signal generation to pass through the loop
        mock_report = Mock()
        mock_report.state.value = "NORMAL"
        mock_report.gap_pct = 0.1
        mock_report.rsi15 = 55.0
        mock_report.vwap = 400.0
        mock_report.last = 405.0
        mock_report.drop_from_hod_pct = -1.0
        mock_report.above_vwap = True
        mock_report.details = "Clear uptrend"
        mock_report.locks = {}

        mock_signal = Mock()
        mock_signal.symbol = "SPY"
        mock_signal.tier = "CORE"
        mock_signal.direction = "CALL"
        mock_signal.price = 405.0
        mock_signal.ema20 = 402.0
        mock_signal.sma50 = 398.0
        mock_signal.rsi14 = 67.2
        mock_signal.bb_upper = 408.0
        mock_signal.bb_lower = 398.0
        mock_signal.pct5d = 1.5
        mock_signal.reasons = ["Bullish EMA cross"]
        mock_signal.confidence = "HIGH"

        # Mock fetch_rsi15 as it's called within _handle indirectly
        monkeypatch.setattr("bot.jeci_options_bot.fetch_rsi15", lambda s: 55.0)
        # Mock generate_signal to return our mock signal for SPY/CORE
        monkeypatch.setattr("bot.jeci_options_bot.generate_signal", lambda s, t:mock_signal if s=="SPY" and t=="CORE" else None)
        # Mock TT session methods to prevent actual API calls
        bot.tt.get_balance.return_value = 100_000.0
        bot.tt.get_option_chain.return_value = [{"expiration-date": "2026-07-19", "strikes": [{"strike-price": 400.0, "call": {"symbol": "SPY 260719C00400000", "bid": "5.00", "ask": "5.10"}}]}]
        bot.tt.accounts = {"CORE": "12345"} # Ensure accounts are set


        # Execute the scan_all logic to trigger the _handle method
        bot.scan_all(mock_report) # Pass mock report to avoid market hours check

        # Verify that the consensus engine's evaluate method was called with the correct metrics
        bot.consensus.evaluate.assert_called_once()
        call_args, call_kwargs = bot.consensus.evaluate.call_args
        # The second argument to evaluate is the metrics dict
        metrics_dict = call_args[1]

        assert "x_sentiment" in metrics_dict
        assert "x_confidence" in metrics_dict
        assert "x_signals" in metrics_dict
        assert "macro_regime" in metrics_dict
        assert "macro_bias" in metrics_dict
        assert "catalysts" in metrics_dict
        assert "setup_quality" in metrics_dict
        assert "lens_confidence" in metrics_dict
        assert "trace_triggered" in metrics_dict

        assert metrics_dict["x_sentiment"] == SCOUT_OUT["sentiment"]
        assert metrics_dict["x_confidence"] == SCOUT_OUT["confidence"]
        assert metrics_dict["x_signals"] == SCOUT_OUT["key_signals"]
        assert metrics_dict["macro_regime"] == ATLAS_OUT["macro_regime"]
        assert metrics_dict["macro_bias"] == ATLAS_OUT["trade_bias"]
        assert metrics_dict["catalysts"] == ATLAS_OUT["catalysts_ahead"]
        assert metrics_dict["setup_quality"] == LENS_OUT["setup_quality"]
        assert metrics_dict["lens_confidence"] == LENS_OUT["confidence"]
        assert metrics_dict["trace_triggered"] == LENS_OUT["trace_triggered"]

        # Assert that no Tastytrade API calls were made for order placement during the scan
        mock_place_order.assert_not_called()

        # Check that the Risk Moat was at least consulted (it's called before consensus)
        from bot.consensus_engine import RiskMoat
        with patch.object(RiskMoat, 'validate') as mock_validate:
            bot._handle("CORE", "SPY", mock_report)
            mock_validate.assert_called_once()

