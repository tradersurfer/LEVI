import codecs

import pytest

from levi.evidence.models import EvidenceType
from levi.evidence.parsers.base import ParserValidationError
from levi.evidence.parsers.csv_parser import CsvEvidenceParser


def _write(tmp_path, text, *, bom=False):
    path = tmp_path / "data.csv"
    payload = text.encode("utf-8")
    path.write_bytes((codecs.BOM_UTF8 if bom else b"") + payload)
    return path


def _parse(path):
    return CsvEvidenceParser().parse(file_path=path, user_id="u1", source_name="Upload")


def test_utf8_csv_parsed(tmp_path):
    parsed = _parse(_write(tmp_path, "symbol,quantity\nSPY,2\n"))
    assert parsed.structured_data["row_count"] == 1


def test_utf8_bom_csv_parsed(tmp_path):
    parsed = _parse(_write(tmp_path, "symbol,quantity\nSPY,2\n", bom=True))
    assert parsed.ticker_symbols == ("SPY",)


def test_options_chain_schema_detected(tmp_path):
    parsed = _parse(_write(tmp_path, "symbol,expiration,strike,bid,ask,delta\nSPY,2026-08-21,600,1,1.1,.4\n"))
    assert parsed.evidence_type is EvidenceType.OPTIONS_CHAIN
    assert parsed.structured_data["schema"] == "options_chain"


def test_portfolio_export_schema_detected(tmp_path):
    parsed = _parse(_write(tmp_path, "symbol,quantity,market_value,cost_basis\nAAPL,5,1000,800\n"))
    assert parsed.evidence_type is EvidenceType.PORTFOLIO_EXPORT


def test_trade_journal_schema_detected(tmp_path):
    parsed = _parse(_write(tmp_path, "symbol,entry_time,entry_price,exit_price,pnl\nNVDA,2026-01-01T10:00:00,10,12,2\n"))
    assert parsed.evidence_type is EvidenceType.TRADE_JOURNAL
    assert parsed.structured_data["parsed_timestamps"]


def test_generic_table_fallback(tmp_path):
    parsed = _parse(_write(tmp_path, "name,color\nalpha,blue\n"))
    assert parsed.evidence_type is EvidenceType.TABLE
    assert any("No known" in warning for warning in parsed.warnings)


def test_oversized_row_count_truncated_safely(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_MAX_CSV_ROWS", "1")
    parsed = _parse(_write(tmp_path, "symbol,quantity\nSPY,1\nAAPL,2\n"))
    assert parsed.structured_data["row_count"] == 1
    assert any("truncated" in warning for warning in parsed.warnings)


def test_excessive_columns_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_MAX_CSV_COLUMNS", "2")
    with pytest.raises(ParserValidationError, match="column limit"):
        _parse(_write(tmp_path, "a,b,c\n1,2,3\n"))


def test_tickers_extracted(tmp_path):
    parsed = _parse(_write(tmp_path, "ticker,shares,market_value\nspy,2,100\nAAPL,3,200\n"))
    assert parsed.ticker_symbols == ("AAPL", "SPY")


def test_ambiguous_schema_produces_warning(tmp_path):
    parsed = _parse(_write(tmp_path, "symbol,bid,quantity\nSPY,1,2\n"))
    assert any("ambiguous" in warning for warning in parsed.warnings)


def test_non_utf8_csv_rejected(tmp_path):
    path = tmp_path / "data.csv"
    path.write_bytes(b"symbol\n\xff\n")
    with pytest.raises(ParserValidationError, match="UTF-8"):
        _parse(path)


def test_semicolon_delimiter_detected(tmp_path):
    parsed = _parse(_write(tmp_path, "symbol;quantity;market_value\nSPY;2;100\n"))
    assert parsed.metadata["delimiter"] == ";"
