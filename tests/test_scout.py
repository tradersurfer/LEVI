import os
from unittest.mock import Mock, patch

from agents.scout import Scout


def _mock_response(content):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": content}}]}
    return response


def test_scout_output_shape_with_mocked_xai_and_perplexity(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pplx-test")

    grok = _mock_response(
        '{"sentiment":"BULLISH","trending_tickers":["SPY","NVDA"],'
        '"key_signals":["Fed speaker at 2pm"],"confidence":0.82}'
    )
    perplexity = _mock_response('{"verified":true,"source_count":3}')

    with patch("agents.scout.requests.post", side_effect=[grok, perplexity]):
        output = Scout().scan(["SPY", "NVDA"])

    assert set(output.keys()) == {
        "sentiment",
        "trending_tickers",
        "key_signals",
        "confidence",
        "source_count",
        "perplexity_verified",
        "raw_grok_response",
        "timestamp",
    }
    assert output["sentiment"] == "BULLISH"
    assert output["trending_tickers"] == ["SPY", "NVDA"]
    assert output["perplexity_verified"] is True
    assert output["source_count"] == 3
    assert 0.0 <= output["confidence"] <= 1.0


def test_scout_failure_returns_neutral(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    output = Scout().scan()
    assert output["sentiment"] == "NEUTRAL"
    assert output["confidence"] == 0.0
    assert output["perplexity_verified"] is False
