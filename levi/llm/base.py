from typing import Protocol
from .models import LLMRequest, LLMResponse
class LLMAdapter(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...
