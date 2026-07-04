"""LENS — technical analysis and options-chain agent for LEVI."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import requests

from agents.trace import Trace

log = logging.getLogger("LEVI.LENS")

SETUP_QUALITIES = {"A", "B", "C", "SKIP"}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _clamp_confidence(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _entry_zone(value: Any) -> tuple[float, float]:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return (_float(value[0]), _float(value[1]))
    return (0.0, 0.0)


def _safe_skip() -> dict[str, Any]:
    return {
        "setup_quality": "SKIP",
        "entry_zone": (0.0, 0.0),
        "target": 0.0,
        "stop": 0.0,
        "iv_rank": 0.0,
        "unusual_activity": False,
        "confidence": 0.0,
        "trace_triggered": False,
        "timestamp": _utc_timestamp(),
    }


class Lens:
    """Technical setup + live options-chain analyzer."""

    def __init__(self) -> None:
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY", "")
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
        self.perplexity_model = os.getenv(
            "PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online"
        )
        self.timeout = int(os.getenv("AGENT_TIMEOUT_SEC", "25"))

    def analyze(self, symbol: str, chart_metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return standardized technical analysis output for a symbol."""
        try:
            if not self.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY missing")
            if not self.perplexity_api_key:
                raise RuntimeError("PERPLEXITY_API_KEY missing")

            chart_metrics = chart_metrics or {}
            technical = self._analyze_chart(symbol, chart_metrics)
            options = self._query_options_chain(symbol)

            setup_quality = str(technical.get("setup_quality", "SKIP")).upper()
            if setup_quality not in SETUP_QUALITIES:
                setup_quality = "SKIP"

            output = {
                "setup_quality": setup_quality,
                "entry_zone": _entry_zone(technical.get("entry_zone")),
                "target": _float(technical.get("target")),
                "stop": _float(technical.get("stop")),
                "iv_rank": _float(options.get("iv_rank")),
                "unusual_activity": bool(options.get("unusual_activity", False)),
                "confidence": _clamp_confidence(technical.get("confidence")),
                "trace_triggered": False,
                "timestamp": _utc_timestamp(),
            }

            if output["confidence"] < 0.7:
                traced = Trace().clarify({"symbol": symbol, **output, "chart_metrics": chart_metrics})
                output["trace_triggered"] = True
                output["confidence"] = _clamp_confidence(traced.get("confidence", output["confidence"]))
                if traced.get("trace_recommendation") in {"AVOID", "SKIP"}:
                    output["setup_quality"] = "SKIP"

            return output
        except Exception as exc:
            log.warning("LENS failed: %s", exc)
            return _safe_skip()

    def _analyze_chart(self, symbol: str, chart_metrics: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "You are LENS, LEVI's technical analysis agent. Analyze this chart setup "
            f"for {symbol}. Return ONLY JSON with keys: setup_quality (A|B|C|SKIP), "
            "entry_zone ([low, high]), target (number), stop (number), confidence "
            "(0.0-1.0). Metrics:\n"
            f"{json.dumps(chart_metrics, indent=2)}"
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
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        raw = response.json()["content"][0]["text"]
        return _extract_json(raw) or {}

    def _query_options_chain(self, symbol: str) -> dict[str, Any]:
        prompt = (
            "Query current live options-chain context for "
            f"{symbol}: IV rank, put/call ratio, max pain, and unusual options "
            "activity. Return ONLY JSON with keys: iv_rank (number 0-100), "
            "unusual_activity (boolean)."
        )
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.perplexity_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        return _extract_json(raw) or {}


def analyze(symbol: str, chart_metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    return Lens().analyze(symbol, chart_metrics=chart_metrics)
