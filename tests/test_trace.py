from unittest.mock import Mock, patch

from agents.trace import Trace


def _mock_response(content):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"content": [{"text": content}]}
    return response


def test_trace_clarifies_setup(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test")
    setup = {"symbol": "SPY", "confidence": 0.52, "setup_quality": "C"}
    claude = _mock_response(
        '{"confidence":0.72,"recommendation":"WAIT","rationale":"VWAP reclaim needed"}'
    )

    with patch("agents.trace.requests.post", return_value=claude):
        output = Trace().clarify(setup)

    assert output["confidence"] == 0.72
    assert output["trace_recommendation"] == "WAIT"
    assert output["trace_failed"] is False
    assert "trace_rationale" in output


def test_trace_failure_returns_original_with_flag(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    setup = {"symbol": "SPY", "confidence": 0.52, "setup_quality": "C"}
    output = Trace().clarify(setup)
    assert output["symbol"] == setup["symbol"]
    assert output["confidence"] == setup["confidence"]
    assert output["trace_failed"] is True
