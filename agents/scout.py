"""SCOUT — X sentiment scanner for LEVI.

SCOUT uses Grok/xAI for X-native sentiment discovery and Perplexity for
live-source verification. API failures never bubble into the trading loop; the
safe fallback is neutral sentiment with zero confidence.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import requests

log = logging.getLogger("LEVI.SCOUT")

SENTIMENTS = {"BULLISH", "BEARISH", "NEUTRAL", "MIXED"}


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


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _neutral(raw: str = "") -> dict[str, Any]:
    return {
        "sentiment": "NEUTRAL",
        "trending_tickers": [],
        "key_signals": [],
        "confidence": 0.0,
        "source_count": 0,
        "perplexity_verified": False,
        "raw_grok_response": raw,
        "timestamp": _utc_timestamp(),
    }


class Scout:
    """X scanner: traders, analysts, trending tickers, verified with Perplexity."""

    def __init__(self) -> None:
        self.xai_api_key = os.getenv("XAI_API_KEY", "")
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY", "")
        self.grok_model = os.getenv("GROK_MODEL", "grok-4")
        self.perplexity_model = os.getenv(
            "PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online"
        )
        self.timeout = int(os.getenv("AGENT_TIMEOUT_SEC", "25"))

    def scan(self, watchlist: list[str] | None = None) -> dict[str, Any]:
        """Return standardized sentiment output for the LEVI scan loop."""
        try:
            if not self.xai_api_key:
                raise RuntimeError("XAI_API_KEY missing")

            tickers = ", ".join(watchlist or ["SPY", "QQQ", "NVDA", "TSLA"])
            prompt = (
                "You are SCOUT, LEVI's X sentiment scanner. Scan current X posts "
                "from traders, analysts, and market accounts for trending tickers, "
                "sentiment velocity, and near-term catalysts. Focus on actionable "
                f"signals for: {tickers}. Return ONLY JSON with keys: "
                "sentiment (BULLISH|BEARISH|NEUTRAL|MIXED), trending_tickers "
                "(array), key_signals (array), confidence (0.0-1.0)."
            )
            grok_response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.xai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.grok_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    # xAI supports live search parameters on search-enabled models;
                    # harmless in tests and ignored by mocks.
                    "search_parameters": {"mode": "auto", "sources": [{"type": "x"}]},
                },
                timeout=self.timeout,
            )
            grok_response.raise_for_status()
            raw = grok_response.json()["choices"][0]["message"]["content"]
            data = _extract_json(raw) or {}

            sentiment = str(data.get("sentiment", "NEUTRAL")).upper()
            if sentiment not in SENTIMENTS:
                sentiment = "NEUTRAL"

            output = _neutral(raw=raw)
            output.update(
                {
                    "sentiment": sentiment,
                    "trending_tickers": _as_string_list(data.get("trending_tickers")),
                    "key_signals": _as_string_list(data.get("key_signals")),
                    "confidence": _clamp_confidence(data.get("confidence")),
                }
            )

            signal_found = (
                output["sentiment"] != "NEUTRAL"
                or bool(output["trending_tickers"])
                or bool(output["key_signals"])
            )
            if signal_found:
                verified, source_count = self._verify_with_perplexity(output)
                output["perplexity_verified"] = verified
                output["source_count"] = source_count

            return output
        except Exception as exc:  # safe fallback; never raise into trading loop
            log.warning("SCOUT failed: %s", exc)
            return _neutral()

    def _verify_with_perplexity(self, signal: dict[str, Any]) -> tuple[bool, int]:
        if not self.perplexity_api_key:
            return False, 0

        prompt = (
            "Verify this market sentiment signal against current live web/news "
            "sources. Return ONLY JSON: {\"verified\": true|false, "
            "\"source_count\": <integer>}. Signal:\n"
            f"{json.dumps(signal, indent=2)}"
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
        data = _extract_json(raw) or {}
        try:
            source_count = max(0, int(data.get("source_count", 0)))
        except (TypeError, ValueError):
            source_count = 0
        return bool(data.get("verified")) and source_count > 0, source_count


def scan(watchlist: list[str] | None = None) -> dict[str, Any]:
    return Scout().scan(watchlist=watchlist)
