from unittest.mock import Mock, patch

from agents.atlas import Atlas


def _mock_response(content):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": content}}]}
    return response


def test_atlas_output_shape_with_mocked_grok(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    grok = _mock_response(
        '{"macro_regime":"RISK_ON","catalysts_ahead":["FOMC minutes"],'
        '"sector_bias":"BULLISH","trade_bias":"GO","confidence":0.74}'
    )

    with patch("agents.atlas.requests.post", return_value=grok):
        output = Atlas().analyze("NVDA")

    assert set(output.keys()) == {
        "macro_regime",
        "catalysts_ahead",
        "sector_bias",
        "trade_bias",
        "confidence",
        "timestamp",
    }
    assert output["macro_regime"] == "RISK_ON"
    assert output["sector_bias"] == "BULLISH"
    assert output["trade_bias"] == "GO"
    assert 0.0 <= output["confidence"] <= 1.0


def test_atlas_failure_returns_safe_wait(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    output = Atlas().analyze("SPY")
    assert output["macro_regime"] == "TRANSITION"
    assert output["sector_bias"] == "NEUTRAL"
    assert output["trade_bias"] == "WAIT"
    assert output["confidence"] == 0.0
