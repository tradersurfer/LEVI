"""
status_api.py — FastAPI status server for JECI Trading Suite dashboard
Bot loop runs as a background thread when RUN_BOT=true.
"""

from __future__ import annotations
import os, threading, logging
from datetime import datetime, timezone
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from levi.contracts.what_you_need import build_what_you_need
from levi.evidence.registry import EvidenceRegistry
from levi.workspace.initializer import load_user_profile

log = logging.getLogger("JECI.api")

app = FastAPI(title="JECI Status API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# shared state written by the bot, read by the API
_shared: dict = {"report": None, "signals": {}, "trades": [], "blocklist": []}
evidence_registry = EvidenceRegistry()


class WhatYouNeedRequest(BaseModel):
    user_id: str
    request_type: str
    ticker: str | None = None


@app.on_event("startup")
def _start_bot():
    if os.getenv("RUN_BOT", "false").lower() != "true":
        log.info("RUN_BOT=false — API-only mode")
        return
    from bot.levi_bot import JECIOptionsBot
    bot = JECIOptionsBot()
    bot._shared = _shared          # inject shared state reference
    threading.Thread(target=bot.start, daemon=True).start()
    log.info("Bot loop started in background thread")


@app.get("/health")
def health():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}


@app.get("/state")
def get_state():
    if _shared["report"]:
        r = _shared["report"]
        # StateReport is a dataclass; convert for JSON
        return {
            "state":   r.state.value,
            "index":   r.index,
            "gap_pct": r.gap_pct,
            "rsi15":   r.rsi15,
            "rsi15_session_low": r.rsi15_session_low,
            "vwap":    r.vwap,
            "last":    r.last,
            "drop_from_hod_pct": r.drop_from_hod_pct,
            "above_vwap": r.above_vwap,
            "details": r.details,
            "locks":   r.locks,
        }
    # on-demand if bot hasn't run yet
    try:
        from bot.market_state import MarketStateEngine
        r = MarketStateEngine("SPY").detect()
        _shared["report"] = r
        return {
            "state": r.state.value, "index": r.index, "gap_pct": r.gap_pct,
            "rsi15": r.rsi15, "rsi15_session_low": r.rsi15_session_low,
            "vwap": r.vwap, "last": r.last, "drop_from_hod_pct": r.drop_from_hod_pct,
            "above_vwap": r.above_vwap, "details": r.details, "locks": r.locks,
        }
    except Exception as e:
        return {"state": "UNKNOWN", "error": str(e)}


@app.get("/signals")
def get_signals():
    return _shared["signals"]


@app.get("/trades")
def get_trades():
    return {"open_trades": _shared["trades"], "blocklist": _shared["blocklist"]}


@app.post("/api/what-you-need")
def what_you_need(request: WhatYouNeedRequest):
    try:
        profile = load_user_profile(request.user_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="user profile not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_what_you_need(
        profile=profile,
        registry=evidence_registry,
        request_type=request.request_type,
        ticker=request.ticker,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot.status_api:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
