from collections import deque
from .models import LLMRequest, LLMResponse
class MockLLMAdapter:
    def __init__(self,responses=()): self.responses=deque(responses); self.requests=[]
    def complete(self,request:LLMRequest)->LLMResponse:
        self.requests.append(request)
        if not self.responses: raise RuntimeError("no mock response configured")
        value=self.responses.popleft()
        if isinstance(value,Exception): raise value
        return value if isinstance(value,LLMResponse) else LLMResponse(value,request.model)
