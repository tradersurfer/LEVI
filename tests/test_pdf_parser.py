import pytest

from levi.evidence.models import EvidenceType
from levi.evidence.parsers.base import ParserValidationError
from levi.evidence.parsers.pdf_parser import PdfEvidenceParser
from tests.evidence_helpers import make_pdf


def _parse(path):
    return PdfEvidenceParser().parse(file_path=path, user_id="u1", source_name="Upload")


def test_text_pdf_parsed(tmp_path):
    parsed = _parse(make_pdf(tmp_path / "report.pdf", "Research Report SPY"))
    assert "Research Report SPY" in parsed.extracted_text
    assert "SPY" in parsed.ticker_symbols


def test_page_count_recorded(tmp_path):
    parsed = _parse(make_pdf(tmp_path / "report.pdf", "Portfolio Report"))
    assert parsed.metadata["page_count"] == 1
    assert parsed.structured_data["pages"][0]["page"] == 1


def test_image_only_pdf_warns(tmp_path):
    parsed = _parse(make_pdf(tmp_path / "blank.pdf"))
    assert parsed.extracted_text is None
    assert any("image-only" in warning for warning in parsed.warnings)


def test_password_protected_pdf_rejected(tmp_path):
    path = make_pdf(tmp_path / "protected.pdf", "Private", encrypted=True)
    with pytest.raises(ParserValidationError, match="password-protected"):
        _parse(path)


def test_oversized_pdf_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_MAX_PDF_SIZE_MB", "0")
    with pytest.raises(ParserValidationError, match="size limit"):
        _parse(make_pdf(tmp_path / "report.pdf", "Report"))


def test_likely_broker_statement_detected(tmp_path):
    parsed = _parse(make_pdf(tmp_path / "statement.pdf", "Brokerage Statement SPY"))
    assert parsed.evidence_type is EvidenceType.BROKER_STATEMENT
    assert parsed.structured_data["document_type"] == "broker_statement"


def test_extracted_character_limit_enforced(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_MAX_EXTRACTED_CHARACTERS", "5")
    parsed = _parse(make_pdf(tmp_path / "report.pdf", "Research Report SPY"))
    assert len(parsed.extracted_text) <= 5
    assert any("truncated" in warning for warning in parsed.warnings)


def test_page_limit_enforced(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_MAX_PDF_PAGES", "0")
    with pytest.raises(ParserValidationError, match="page limit"):
        _parse(make_pdf(tmp_path / "report.pdf", "Report"))
