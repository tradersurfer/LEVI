"""TRACE — chart ambiguity assistant for LENS."""

from __future__ import annotations

import copy
import json
import logging
import os
import re
from typing import Any

import requests

log = logging.getLogger("LEVI.TRACE")

RECOMMENDATIONS = {"GO", "WAIT", "AVOID", "SKIP"}


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _clamp_confidence(value: Any, fallback: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return fallback


class Trace:
    """Clarifies low-confidence setups from LENS using Claude."""

    def __init__(self) -> None:
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
        self.timeout = int(os.getenv("AGENT_TIMEOUT_SEC", "25"))

    def clarify(self, setup: dict[str, Any]) -> dict[str, Any]:
        original = copy.deepcopy(setup)
        try:
            if not self.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY missing")

            prompt = (
                "You are TRACE, LEVI's chart ambiguity assistant. LENS produced a "
                "low-confidence setup. Ask the implicit clarifying questions, resolve "
                "ambiguity, and return ONLY JSON with keys: confidence (0.0-1.0), "
                "recommendation (GO|WAIT|AVOID|SKIP), rationale (short string). Setup:\n"
                f"{json.dumps(setup, indent=2)}"
            )
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.claude_model,
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            raw = response.json()["content"][0]["text"]
            data = _extract_json(raw) or {}

            updated = copy.deepcopy(setup)
            current_confidence = _clamp_confidence(updated.get("confidence"), 0.0)
            updated["confidence"] = _clamp_confidence(data.get("confidence"), current_confidence)
            recommendation = str(data.get("recommendation", "")).upper()
            if recommendation in RECOMMENDATIONS:
                updated["trace_recommendation"] = recommendation
            if data.get("rationale"):
                updated["trace_rationale"] = str(data["rationale"])
            updated["trace_failed"] = False
            return updated
        except Exception as exc:
            log.warning("TRACE failed: %s", exc)
            original["trace_failed"] = True
            return original


def clarify(setup: dict[str, Any]) -> dict[str, Any]:
    return Trace().clarify(setup)
