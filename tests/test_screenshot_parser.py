from dataclasses import dataclass

import pytest

from levi.evidence.models import EvidenceType
from levi.evidence.parsers.base import ParsedEvidence, ParserValidationError
from levi.evidence.parsers.screenshot_parser import (
    NoOpVisionExtractor, ScreenshotParser, VisionExtraction,
)
from tests.evidence_helpers import make_image


def test_supported_screenshot_extension_accepted():
    parser = ScreenshotParser()
    assert parser.supports(filename="screen.png", mime_type="image/png")


def test_unsupported_image_extension_rejected():
    parser = ScreenshotParser()
    assert not parser.supports(filename="screen.gif", mime_type="image/gif")


def test_image_dimensions_extracted(tmp_path):
    path = make_image(tmp_path / "screen.png", (321, 123))
    result = ScreenshotParser().parse(file_path=path, user_id="u1", source_name="Upload")
    assert result.metadata["width"] == 321
    assert result.metadata["height"] == 123
    assert result.evidence_type is EvidenceType.SCREENSHOT


def test_noop_vision_returns_warning(tmp_path):
    path = make_image(tmp_path / "screen.png")
    extraction = NoOpVisionExtractor().extract(path)
    assert extraction.extracted_text is None
    assert extraction.confidence < 0.70
    assert "No vision provider" in extraction.warnings[0]


def test_invalid_image_rejected(tmp_path):
    path = tmp_path / "bad.png"
    path.write_bytes(b"not an image")
    with pytest.raises(ParserValidationError, match="invalid or unreadable image"):
        ScreenshotParser().parse(file_path=path, user_id="u1", source_name="Upload")


def test_parsed_evidence_rejects_invalid_confidence():
    with pytest.raises(ValueError, match="confidence"):
        ParsedEvidence(
            evidence_type=EvidenceType.SCREENSHOT, parser_name="test", parser_version="1",
            extracted_text=None, ticker_symbols=(), timeframe=None, captured_at=None,
            confidence=1.1, warnings=(), structured_data={}, metadata={},
        )


def test_visible_iso_timestamp_detected(tmp_path):
    class TimestampVision:
        def extract(self, image_path):
            return VisionExtraction(extracted_text="SPY 5m 2026-07-21T10:30:00Z", confidence=0.9)
    parsed = ScreenshotParser(TimestampVision()).parse(
        file_path=make_image(tmp_path / "screen.png"), user_id="u1", source_name="Upload"
    )
    assert parsed.captured_at.isoformat() == "2026-07-21T10:30:00+00:00"
