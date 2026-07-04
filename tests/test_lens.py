from unittest.mock import Mock, patch

from agents.lens import Lens


def _anthropic_response(content):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"content": [{"text": content}]}
    return response


def _perplexity_response(content):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": content}}]}
    return response


def test_lens_output_shape_and_trace_not_triggered(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pplx-test")
    claude = _anthropic_response(
        '{"setup_quality":"A","entry_zone":[500.0,505.0],"target":520.0,'
        '"stop":492.5,"confidence":0.81}'
    )
    perplexity = _perplexity_response('{"iv_rank":44.0,"unusual_activity":true}')

    with patch("agents.lens.requests.post", side_effect=[claude, perplexity]):
        output = Lens().analyze("NVDA", {"rsi": 52})

    assert set(output.keys()) == {
        "setup_quality",
        "entry_zone",
        "target",
        "stop",
        "iv_rank",
        "unusual_activity",
        "confidence",
        "trace_triggered",
        "timestamp",
    }
    assert output["setup_quality"] == "A"
    assert output["entry_zone"] == (500.0, 505.0)
    assert output["unusual_activity"] is True
    assert output["trace_triggered"] is False
    assert 0.0 <= output["confidence"] <= 1.0


def test_lens_calls_trace_when_confidence_low(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pplx-test")
    claude = _anthropic_response(
        '{"setup_quality":"C","entry_zone":[100.0,101.0],"target":105.0,'
        '"stop":98.0,"confidence":0.55}'
    )
    perplexity = _perplexity_response('{"iv_rank":21.0,"unusual_activity":false}')

    with patch("agents.lens.requests.post", side_effect=[claude, perplexity]), patch(
        "agents.lens.Trace"
    ) as trace_cls:
        trace_cls.return_value.clarify.return_value = {"confidence": 0.71, "trace_recommendation": "WAIT"}
        output = Lens().analyze("SPY", {"rsi": 48})

    assert output["trace_triggered"] is True
    assert output["confidence"] == 0.71
    trace_cls.return_value.clarify.assert_called_once()


def test_lens_failure_returns_skip(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    output = Lens().analyze("SPY")
    assert output["setup_quality"] == "SKIP"
    assert output["confidence"] == 0.0
    assert output["trace_triggered"] is False
