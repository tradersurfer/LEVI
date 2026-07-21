"""
status_api.py — FastAPI status server for JECI Trading Suite dashboard
Bot loop runs as a background thread when RUN_BOT=true.
"""

from __future__ import annotations
import os, threading, logging, tempfile
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from levi.contracts.what_you_need import build_what_you_need
from levi.evidence.registry import EvidenceRegistry
from levi.workspace.initializer import load_user_profile
from levi.auth.api import router as auth_router
from levi.auth.service import AuthService
from levi.auth.supabase import SupabaseAuthAdapter
from levi.deployment.environment import validate_environment
from levi.dashboard import DashboardService, build_dashboard_router

log = logging.getLogger("JECI.api")

app = FastAPI(title="LEVI API", version="0.1.0-alpha")
_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "LEVI_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)

# Phase 6 is opt-in so existing deployments and paper/alert behavior are unchanged.
if os.getenv("LEVI_AUTH_ENABLED", "false").lower() == "true":
    app.state.auth_service = AuthService(SupabaseAuthAdapter())

# shared state written by the bot, read by the API
_shared: dict = {
    "report": None, "signals": {}, "trades": [], "blocklist": [],
    "positions": [], "decisions": [], "alerts": [],
}
evidence_registry = EvidenceRegistry()


def _dashboard() -> DashboardService:
    return DashboardService(shared=_shared, registry=evidence_registry)


app.include_router(build_dashboard_router(
    service_factory=_dashboard,
    profile_loader=load_user_profile,
))


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
    return {
        "status": "healthy",
        "version": app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    validation = validate_environment()
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "errors": list(validation.errors)},
        )
    return {
        "status": "ready",
        "version": app.version,
        "warnings": list(validation.warnings),
    }


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


def _ingestion_service():
    from levi.evidence.ingestion.uploader import EvidenceIngestionService
    from levi.evidence.parsers import (
        ChartParser, CsvEvidenceParser, ExcelEvidenceParser,
        PdfEvidenceParser, ScreenshotParser,
    )
    from levi.evidence.storage import EncryptedFilesystemStorage

    return EvidenceIngestionService(
        registry=evidence_registry,
        storage=EncryptedFilesystemStorage(),
        parsers=[
            ChartParser(), ScreenshotParser(), CsvEvidenceParser(),
            ExcelEvidenceParser(), PdfEvidenceParser(),
        ],
    )


@app.post("/api/evidence/upload", status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    user_id: str = Form(...),
    source_name: str = Form(...),
    file: UploadFile = File(...),
    declared_evidence_type: str | None = Form(None),
    captured_at: str | None = Form(None),
):
    from levi.evidence.models import EvidenceType
    from levi.evidence.ingestion.uploader import (
        EvidenceUploadRequest, UnsupportedEvidenceError,
        UploadSizeError, UploadValidationError,
    )
    from levi.evidence.parsers import ParserValidationError
    from levi.evidence.storage import StorageConfigurationError

    try:
        load_user_profile(user_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="user workspace/profile not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        declared = EvidenceType(declared_evidence_type) if declared_evidence_type else None
        captured = datetime.fromisoformat(captured_at.replace("Z", "+00:00")) if captured_at else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid evidence type or captured_at") from exc

    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary:
            temporary_path = Path(temporary.name)
            total = 0
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > 25 * 1024 * 1024:
                    raise UploadSizeError("upload exceeds the maximum accepted size")
                temporary.write(chunk)
        result = _ingestion_service().ingest(EvidenceUploadRequest(
            user_id=user_id,
            source_name=source_name,
            original_filename=filename,
            mime_type=file.content_type or "application/octet-stream",
            temporary_file_path=temporary_path,
            declared_evidence_type=declared,
            captured_at=captured,
        ))
    except UploadSizeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except UnsupportedEvidenceError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ParserValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except StorageConfigurationError as exc:
        log.error("Evidence storage is not safely configured")
        raise HTTPException(status_code=500, detail="evidence storage is not safely configured") from exc
    except HTTPException:
        raise
    except Exception as exc:
        log.error("Evidence ingestion failed safely (%s)", type(exc).__name__)
        raise HTTPException(status_code=500, detail="evidence ingestion failed safely") from exc
    finally:
        await file.close()
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

    record = result.evidence_record
    return {
        "evidence_id": record.evidence_id,
        "user_id": record.user_id,
        "evidence_type": record.evidence_type.value,
        "source_name": record.source_name,
        "filename": record.filename,
        "ticker_symbols": record.ticker_symbols,
        "timeframe": record.timeframe,
        "confidence": record.confidence,
        "warnings": record.warnings,
        "stored": True,
        "encrypted": result.stored_file.encrypted,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot.status_api:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
