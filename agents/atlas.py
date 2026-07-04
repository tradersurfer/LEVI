"""ATLAS — macro and fundamental context agent for LEVI."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import requests

log = logging.getLogger("LEVI.ATLAS")

MACRO_REGIMES = {"RISK_ON", "RISK_OFF", "TRANSITION"}
SECTOR_BIASES = {"BULLISH", "BEARISH", "NEUTRAL"}
TRADE_BIASES = {"GO", "WAIT", "AVOID"}


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


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _fallback() -> dict[str, Any]:
    return {
        "macro_regime": "TRANSITION",
        "catalysts_ahead": [],
        "sector_bias": "NEUTRAL",
        "trade_bias": "WAIT",
        "confidence": 0.0,
        "timestamp": _utc_timestamp(),
    }


class Atlas:
    """Macro/fundamental agent: Fed, earnings, regime, 48-hour catalysts."""

    def __init__(self) -> None:
        self.xai_api_key = os.getenv("XAI_API_KEY", "")
        self.grok_model = os.getenv("GROK_MODEL", "grok-4")
        self.timeout = int(os.getenv("AGENT_TIMEOUT_SEC", "25"))

    def analyze(self, symbol: str) -> dict[str, Any]:
        try:
            if not self.xai_api_key:
                raise RuntimeError("XAI_API_KEY missing")

            prompt = (
                "You are ATLAS, LEVI's macro and fundamental agent. For ticker "
                f"{symbol}, evaluate current macro regime, Fed calendar, earnings "
                "calendar, sector context, and catalysts in the next 48 hours. "
                "Return ONLY JSON with keys: macro_regime (RISK_ON|RISK_OFF|TRANSITION), "
                "catalysts_ahead (array), sector_bias (BULLISH|BEARISH|NEUTRAL), "
                "trade_bias (GO|WAIT|AVOID), confidence (0.0-1.0)."
            )
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.xai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.grok_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"]
            data = _extract_json(raw) or {}

            output = _fallback()
            macro_regime = str(data.get("macro_regime", "TRANSITION")).upper()
            sector_bias = str(data.get("sector_bias", "NEUTRAL")).upper()
            trade_bias = str(data.get("trade_bias", "WAIT")).upper()
            output.update(
                {
                    "macro_regime": macro_regime if macro_regime in MACRO_REGIMES else "TRANSITION",
                    "catalysts_ahead": _as_list(data.get("catalysts_ahead")),
                    "sector_bias": sector_bias if sector_bias in SECTOR_BIASES else "NEUTRAL",
                    "trade_bias": trade_bias if trade_bias in TRADE_BIASES else "WAIT",
                    "confidence": _clamp_confidence(data.get("confidence")),
                    "timestamp": _utc_timestamp(),
                }
            )
            return output
        except Exception as exc:
            log.warning("ATLAS failed: %s", exc)
            return _fallback()


def analyze(symbol: str) -> dict[str, Any]:
    return Atlas().analyze(symbol)
