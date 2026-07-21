from unittest.mock import Mock
import pytest,requests
from levi.llm import LLMAdapterError,LLMRequest,OpenRouterAdapter
def req(): return LLMRequest("configured/model","system",{"evidence_ids":["e1"]})
def response(content):
 r=Mock(); r.raise_for_status.return_value=None; r.json.return_value={"choices":[{"message":{"content":content}}]}; return r
def test_missing_key_fails_closed():
 with pytest.raises(LLMAdapterError): OpenRouterAdapter(api_key="").complete(req())
def test_structured_json_parsed():
 s=Mock(); s.post.return_value=response('{"verdict":"bullish"}'); assert OpenRouterAdapter(api_key="secret",session=s).complete(req()).content["verdict"]=="bullish"
def test_malformed_json_fails_safely():
 s=Mock(); s.post.return_value=response("not json")
 with pytest.raises(LLMAdapterError): OpenRouterAdapter(api_key="secret",session=s,max_retries=0).complete(req())
def test_timeout_is_bounded():
 s=Mock(); s.post.side_effect=requests.Timeout()
 with pytest.raises(LLMAdapterError): OpenRouterAdapter(api_key="secret",session=s,max_retries=1).complete(req())
 assert s.post.call_count==2
def test_secret_absent_from_exception():
 s=Mock(); s.post.side_effect=requests.Timeout()
 with pytest.raises(LLMAdapterError) as exc: OpenRouterAdapter(api_key="super-secret",session=s,max_retries=0).complete(req())
 assert "super-secret" not in str(exc.value)
def test_missing_model_fails_closed():
 with pytest.raises(LLMAdapterError): OpenRouterAdapter(api_key="secret").complete(LLMRequest("","system",{}))
