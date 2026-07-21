from dataclasses import dataclass
from typing import Any, Mapping
@dataclass(frozen=True)
class LLMRequest:
    model: str; system_prompt: str; payload: Mapping[str,Any]
@dataclass(frozen=True)
class LLMResponse:
    content: Mapping[str,Any]; model: str; processing_time_ms: int=0
