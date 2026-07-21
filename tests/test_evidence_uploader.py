from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bot.status_api import app
from levi.contracts.what_you_need import build_what_you_need
from levi.evidence.ingestion.uploader import (
    EvidenceIngestionService, EvidenceUploadRequest, UnsupportedEvidenceError, UploadSizeError,
)
from levi.evidence.models import EvidenceType
from levi.evidence.parsers import ChartParser, CsvEvidenceParser, ScreenshotParser
from levi.evidence.parsers.screenshot_parser import VisionExtraction
from levi.evidence.registry import EvidenceRegistry
from levi.evidence.storage.filesystem_storage import EncryptedFilesystemStorage
from levi.profiles.models import ExecutionMode, InstrumentType, TradingMode, UserTradingProfile
from levi.workspace.initializer import initialize_user_workspace
from tests.evidence_helpers import encryption_key, make_image


def _storage(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_EVIDENCE_ENCRYPTION_KEY", encryption_key())
    monkeypatch.setenv("LEVI_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    return EncryptedFilesystemStorage()


def _csv(tmp_path, name="chain.csv"):
    path = tmp_path / name
    path.write_text("symbol,expiration,strike,bid,ask\nSPY,2026-08-21,600,1,1.1\n", encoding="utf-8")
    return path


def _request(path, **overrides):
    values = dict(
        user_id="u1", source_name="Upload", original_filename=path.name,
        mime_type="text/csv", temporary_file_path=path,
    )
    values.update(overrides)
    return EvidenceUploadRequest(**values)


def test_parser_selected_by_mime_and_extension(tmp_path, monkeypatch):
    service = EvidenceIngestionService(
        registry=EvidenceRegistry(), storage=_storage(tmp_path, monkeypatch),
        parsers=[ScreenshotParser(), CsvEvidenceParser()],
    )
    result = service.ingest(_request(_csv(tmp_path)))
    assert result.parsed_evidence.parser_name == "csv_parser"


def test_registry_receives_parsed_record(tmp_path, monkeypatch):
    registry = EvidenceRegistry()
    service = EvidenceIngestionService(
        registry=registry, storage=_storage(tmp_path, monkeypatch), parsers=[CsvEvidenceParser()]
    )
    result = service.ingest(_request(_csv(tmp_path)))
    assert registry.get(result.evidence_record.evidence_id, "u1") == result.evidence_record
    assert result.evidence_record.evidence_type is EvidenceType.OPTIONS_CHAIN


def test_storage_failure_prevents_registration(tmp_path):
    class FailingStorage:
        def store(self, **kwargs):
            raise RuntimeError("storage failed")
    registry = EvidenceRegistry()
    service = EvidenceIngestionService(registry=registry, storage=FailingStorage(), parsers=[CsvEvidenceParser()])
    with pytest.raises(RuntimeError, match="storage failed"):
        service.ingest(_request(_csv(tmp_path)))
    assert registry.by_user("u1") == []


def test_registry_failure_rolls_back_storage(tmp_path, monkeypatch):
    class FailingRegistry(EvidenceRegistry):
        def register(self, evidence):
            raise RuntimeError("registry failed")
    storage = _storage(tmp_path, monkeypatch)
    service = EvidenceIngestionService(registry=FailingRegistry(), storage=storage, parsers=[CsvEvidenceParser()])
    with pytest.raises(RuntimeError, match="registry failed"):
        service.ingest(_request(_csv(tmp_path)))
    evidence_dir = tmp_path / "workspace" / "users" / "u1" / "evidence"
    assert list(evidence_dir.iterdir()) == []


def test_unsupported_file_returns_error(tmp_path, monkeypatch):
    path = tmp_path / "malware.exe"
    path.write_bytes(b"MZ")
    service = EvidenceIngestionService(
        registry=EvidenceRegistry(), storage=_storage(tmp_path, monkeypatch), parsers=[CsvEvidenceParser()]
    )
    with pytest.raises(UnsupportedEvidenceError):
        service.ingest(_request(path, mime_type="application/octet-stream"))


def test_file_size_violation_returns_error(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_MAX_CSV_SIZE_MB", "0")
    service = EvidenceIngestionService(
        registry=EvidenceRegistry(), storage=_storage(tmp_path, monkeypatch), parsers=[CsvEvidenceParser()]
    )
    with pytest.raises(UploadSizeError):
        service.ingest(_request(_csv(tmp_path)))


def test_upload_endpoint_returns_201(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    monkeypatch.setenv("LEVI_EVIDENCE_ENCRYPTION_KEY", encryption_key())
    profile = UserTradingProfile(user_id="api-user", display_name="API User")
    initialize_user_workspace(profile)
    image = make_image(tmp_path / "screen.png")
    with image.open("rb") as handle:
        response = TestClient(app).post("/api/evidence/upload", data={
            "user_id": "api-user", "source_name": "Manual Upload",
            "declared_evidence_type": "screenshot",
        }, files={"file": ("screen.png", handle, "image/png")})
    assert response.status_code == 201, response.text
    assert response.json()["stored"] is True
    assert response.json()["encrypted"] is True


def test_upload_response_does_not_expose_storage_path(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    monkeypatch.setenv("LEVI_EVIDENCE_ENCRYPTION_KEY", encryption_key())
    initialize_user_workspace(UserTradingProfile(user_id="safe-user", display_name="Safe"))
    image = make_image(tmp_path / "screen.png")
    with image.open("rb") as handle:
        response = TestClient(app).post("/api/evidence/upload", data={
            "user_id": "safe-user", "source_name": "Upload",
        }, files={"file": ("screen.png", handle, "image/png")})
    assert response.status_code == 201
    payload = response.json()
    assert "storage_path" not in payload
    assert "raw_location" not in payload


class ChartVision:
    def extract(self, image_path):
        return VisionExtraction(
            extracted_text="SPY 5m", confidence=0.95,
            structured_data={"ticker_symbols": ["SPY"], "timeframe": "5m", "trend": "unknown"},
        )


def _day_profile(user_id="u1"):
    return UserTradingProfile(
        user_id=user_id, display_name="User", trading_mode=TradingMode.DAY_TRADING,
        instrument_type=InstrumentType.OPTIONS, execution_mode=ExecutionMode.PAPER_TRADING,
        account_value=10000, buying_power=5000,
    )


def test_what_you_need_recognizes_uploaded_chart(tmp_path, monkeypatch):
    registry = EvidenceRegistry()
    service = EvidenceIngestionService(
        registry=registry, storage=_storage(tmp_path, monkeypatch),
        parsers=[ChartParser(ChartVision())],
    )
    image = make_image(tmp_path / "chart.png")
    service.ingest(EvidenceUploadRequest(
        user_id="u1", source_name="TradingView", original_filename="chart.png",
        mime_type="image/png", temporary_file_path=image,
        declared_evidence_type=EvidenceType.CHART,
    ))
    result = build_what_you_need(_day_profile(), registry, "trade_analysis", "SPY")
    assert "5-minute chart" not in result.missing_items


def test_what_you_need_recognizes_uploaded_options_chain(tmp_path, monkeypatch):
    registry = EvidenceRegistry()
    service = EvidenceIngestionService(
        registry=registry, storage=_storage(tmp_path, monkeypatch), parsers=[CsvEvidenceParser()]
    )
    service.ingest(_request(_csv(tmp_path)))
    result = build_what_you_need(_day_profile(), registry, "trade_analysis", "SPY")
    assert "options chain" not in result.missing_items


def test_evidence_remains_isolated_by_user(tmp_path, monkeypatch):
    registry = EvidenceRegistry()
    service = EvidenceIngestionService(
        registry=registry, storage=_storage(tmp_path, monkeypatch), parsers=[CsvEvidenceParser()]
    )
    service.ingest(_request(_csv(tmp_path)))
    other = build_what_you_need(_day_profile("u2"), registry, "trade_analysis", "SPY")
    assert "options chain" in other.missing_items


def test_upload_endpoint_returns_404_for_missing_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    image = make_image(tmp_path / "screen.png")
    with image.open("rb") as handle:
        response = TestClient(app).post("/api/evidence/upload", data={
            "user_id": "missing", "source_name": "Upload",
        }, files={"file": ("screen.png", handle, "image/png")})
    assert response.status_code == 404


def test_extension_mime_mismatch_rejected(tmp_path, monkeypatch):
    service = EvidenceIngestionService(
        registry=EvidenceRegistry(), storage=_storage(tmp_path, monkeypatch), parsers=[CsvEvidenceParser()]
    )
    with pytest.raises(UnsupportedEvidenceError, match="do not match"):
        service.ingest(_request(_csv(tmp_path), mime_type="image/png"))
