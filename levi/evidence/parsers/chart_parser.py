"""Chart-image extraction without trade analysis or recommendations."""

from __future__ import annotations

import os
from pathlib import Path

from levi.evidence.models import EvidenceType
from levi.evidence.parsers.base import ParsedEvidence
from levi.evidence.parsers.screenshot_parser import (
    NoOpVisionExtractor, ScreenshotParser, SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_IMAGE_MIMES, VisionExtractor,
)


ALLOWED_TRENDS = {"uptrend", "downtrend", "sideways", "mixed", "unknown"}
FORBIDDEN_RECOMMENDATION_FIELDS = {
    "entry", "entry_price", "stop", "stop_loss", "target", "probability", "recommendation"
}


class ChartParser:
    parser_name = "chart_parser"
    parser_version = "1.0"

    def __init__(
        self, vision_extractor: VisionExtractor | None = None,
        confidence_threshold: float | None = None,
    ) -> None:
        self.vision_extractor = vision_extractor or NoOpVisionExtractor()
        self.confidence_threshold = confidence_threshold if confidence_threshold is not None else float(
            os.getenv("LEVI_EVIDENCE_CONFIDENCE_THRESHOLD", "0.70")
        )
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("evidence confidence threshold must be between 0.0 and 1.0")

    def supports(
        self, *, filename: str, mime_type: str,
        evidence_type: EvidenceType | None = None,
    ) -> bool:
        return (
            Path(filename).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            and mime_type.lower() in SUPPORTED_IMAGE_MIMES
            and evidence_type is EvidenceType.CHART
        )

    def parse(self, *, file_path: Path, user_id: str, source_name: str) -> ParsedEvidence:
        screenshot = ScreenshotParser(self.vision_extractor).parse(
            file_path=file_path, user_id=user_id, source_name=source_name
        )
        extracted = dict(screenshot.structured_data)
        for key in FORBIDDEN_RECOMMENDATION_FIELDS:
            extracted.pop(key, None)
        trend = str(extracted.get("trend", "unknown")).lower()
        if trend not in ALLOWED_TRENDS:
            trend = "unknown"
        chart_data = {
            "ticker": extracted.get("ticker"),
            "timeframe": screenshot.timeframe,
            "chart_type": extracted.get("chart_type"),
            "visible_start_time": extracted.get("visible_start_time"),
            "visible_end_time": extracted.get("visible_end_time"),
            "trend": trend,
            "support_levels": extracted.get("support_levels", []),
            "resistance_levels": extracted.get("resistance_levels", []),
            "last_visible_price": extracted.get("last_visible_price"),
            "indicators": extracted.get("indicators", []),
            "source_platform": extracted.get("source_platform") or source_name,
        }
        warnings = list(screenshot.warnings)
        if screenshot.confidence < self.confidence_threshold:
            warnings.append(
                f"Chart extraction confidence is below the {self.confidence_threshold:.2f} threshold."
            )
        return ParsedEvidence(
            evidence_type=EvidenceType.CHART,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            extracted_text=screenshot.extracted_text,
            ticker_symbols=screenshot.ticker_symbols,
            timeframe=screenshot.timeframe,
            captured_at=screenshot.captured_at,
            confidence=screenshot.confidence,
            warnings=tuple(dict.fromkeys(warnings)),
            structured_data=chart_data,
            metadata=screenshot.metadata,
        )
