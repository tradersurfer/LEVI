"""Image metadata parser with an explicit, offline vision boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
from typing import Any, Protocol

from PIL import Image, UnidentifiedImageError

from levi.evidence.models import EvidenceType
from levi.evidence.parsers.base import ParsedEvidence, ParserValidationError, detect_timeframe, extract_tickers


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_IMAGE_MIMES = {"image/png", "image/jpeg", "image/webp"}


def _visible_timestamp(text: str) -> datetime | None:
    match = re.search(
        r"\b(\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?)?)\b",
        text or "",
    )
    if not match:
        return None
    try:
        return datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(frozen=True)
class VisionExtraction:
    extracted_text: str | None = None
    confidence: float = 0.0
    warnings: tuple[str, ...] = ()
    structured_data: dict[str, Any] = field(default_factory=dict)
    captured_at: datetime | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("vision confidence must be between 0.0 and 1.0")


class VisionExtractor(Protocol):
    def extract(self, image_path: Path) -> VisionExtraction:
        ...


class NoOpVisionExtractor:
    def extract(self, image_path: Path) -> VisionExtraction:
        return VisionExtraction(
            confidence=0.1,
            warnings=("No vision provider is configured; only image metadata was extracted.",),
        )


class ScreenshotParser:
    parser_name = "screenshot_parser"
    parser_version = "1.0"

    def __init__(self, vision_extractor: VisionExtractor | None = None) -> None:
        self.vision_extractor = vision_extractor or NoOpVisionExtractor()

    def supports(
        self, *, filename: str, mime_type: str,
        evidence_type: EvidenceType | None = None,
    ) -> bool:
        extension_ok = Path(filename).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        type_ok = evidence_type in {None, EvidenceType.SCREENSHOT}
        return extension_ok and mime_type.lower() in SUPPORTED_IMAGE_MIMES and type_ok

    def parse(self, *, file_path: Path, user_id: str, source_name: str) -> ParsedEvidence:
        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ParserValidationError("unsupported screenshot extension")
        try:
            with Image.open(file_path) as image:
                image.verify()
            with Image.open(file_path) as image:
                width, height = image.size
                image_format = image.format
                image_mode = image.mode
        except (UnidentifiedImageError, OSError) as exc:
            raise ParserValidationError("invalid or unreadable image") from exc

        vision = self.vision_extractor.extract(file_path)
        text = vision.extracted_text
        structured = dict(vision.structured_data)
        tickers = structured.get("ticker_symbols") or extract_tickers(text or "")
        timeframe = structured.get("timeframe") or detect_timeframe(text or "")
        metadata = {
            "width": width, "height": height, "format": image_format,
            "mode": image_mode, "source_name": source_name,
        }
        for key in ("broker", "source_platform", "account_label", "portfolio_label"):
            if structured.get(key) is not None:
                metadata[key] = structured[key]
        return ParsedEvidence(
            evidence_type=EvidenceType.SCREENSHOT,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            extracted_text=text,
            ticker_symbols=tuple(sorted(set(tickers))),
            timeframe=timeframe,
            captured_at=vision.captured_at or _visible_timestamp(text or ""),
            confidence=vision.confidence,
            warnings=vision.warnings,
            structured_data=structured,
            metadata=metadata,
        )
