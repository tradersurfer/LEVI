"""Bounded OpenRouter JSON adapter; never logs prompts or secrets."""
import json, os, re, time
import requests
from .models import LLMRequest, LLMResponse
class LLMAdapterError(RuntimeError): pass
class OpenRouterAdapter:
    endpoint="https://openrouter.ai/api/v1/chat/completions"
    def __init__(self,api_key=None,timeout=None,max_retries=None,session=None):
        self._api_key=api_key if api_key is not None else os.getenv("OPENROUTER_API_KEY","")
        self.timeout=timeout or int(os.getenv("LEVI_LLM_TIMEOUT_SECONDS","30")); self.max_retries=max_retries if max_retries is not None else int(os.getenv("LEVI_LLM_MAX_RETRIES","1")); self.session=session or requests.Session()
    def complete(self,request:LLMRequest)->LLMResponse:
        if not self._api_key: raise LLMAdapterError("OpenRouter is not configured")
        if not request.model.strip(): raise LLMAdapterError("specialist model is not configured")
        started=time.perf_counter(); last=None
        for _ in range(self.max_retries+1):
            try:
                r=self.session.post(self.endpoint,headers={"Authorization":f"Bearer {self._api_key}","Content-Type":"application/json"},json={"model":request.model,"messages":[{"role":"system","content":request.system_prompt},{"role":"user","content":json.dumps(request.payload,default=str)}],"temperature":0,"response_format":{"type":"json_object"}},timeout=self.timeout)
                r.raise_for_status(); text=r.json()["choices"][0]["message"]["content"]; match=re.search(r"\{.*\}",text,re.S)
                if not match: raise LLMAdapterError("model returned malformed JSON")
                data=json.loads(match.group(0))
                if not isinstance(data,dict): raise LLMAdapterError("model returned invalid object")
                return LLMResponse(data,request.model,int((time.perf_counter()-started)*1000))
            except (requests.RequestException,KeyError,TypeError,json.JSONDecodeError,LLMAdapterError) as exc: last=exc
        raise LLMAdapterError(f"OpenRouter request failed safely: {type(last).__name__}")
