from datetime import datetime, timedelta, timezone

from levi.contracts.what_you_need import build_what_you_need
from levi.evidence.models import EvidenceRecord, EvidenceType
from levi.evidence.parsers.chart_parser import ChartParser
from levi.evidence.parsers.screenshot_parser import VisionExtraction
from levi.evidence.registry import EvidenceRegistry
from levi.profiles.models import ExecutionMode, InstrumentType, TradingMode, UserTradingProfile
from tests.evidence_helpers import make_image


class StubVision:
    def __init__(self, data=None, confidence=0.9, text="SPY 5m"):
        self.result = VisionExtraction(
            extracted_text=text, confidence=confidence, structured_data=data or {},
        )

    def extract(self, image_path):
        return self.result


def _profile():
    return UserTradingProfile(
        user_id="u1", display_name="User", trading_mode=TradingMode.DAY_TRADING,
        instrument_type=InstrumentType.OPTIONS, execution_mode=ExecutionMode.PAPER_TRADING,
        account_value=10000, buying_power=5000,
    )


def _record(*, ticker="SPY", timeframe="5m", confidence=0.9):
    return EvidenceRecord(
        evidence_id=f"{ticker}-{timeframe}-{confidence}", user_id="u1",
        evidence_type=EvidenceType.CHART, source_name="TradingView",
        ticker_symbols=[ticker], timeframe=timeframe, confidence=confidence,
    )


def test_low_confidence_chart_does_not_satisfy_strict_requirement():
    registry = EvidenceRegistry()
    registry.register(_record(confidence=0.4))
    result = build_what_you_need(_profile(), registry, "trade_analysis", "SPY")
    assert "5-minute chart" in result.missing_items
    assert any("low confidence" in item for item in result.already_available)


def test_detected_five_minute_chart_satisfies_requirement():
    registry = EvidenceRegistry()
    registry.register(_record())
    result = build_what_you_need(_profile(), registry, "trade_analysis", "SPY")
    assert "5-minute chart" not in result.missing_items


def test_daily_chart_does_not_satisfy_five_minute_requirement():
    registry = EvidenceRegistry()
    registry.register(_record(timeframe="1d"))
    result = build_what_you_need(_profile(), registry, "trade_analysis", "SPY")
    assert "5-minute chart" in result.missing_items


def test_aapl_chart_does_not_satisfy_spy_requirement():
    registry = EvidenceRegistry()
    registry.register(_record(ticker="AAPL"))
    result = build_what_you_need(_profile(), registry, "trade_analysis", "SPY")
    assert "5-minute chart" in result.missing_items


def test_unknown_trend_remains_unknown(tmp_path):
    path = make_image(tmp_path / "chart.png")
    parsed = ChartParser(StubVision({"trend": "not-sure"})).parse(
        file_path=path, user_id="u1", source_name="TradingView"
    )
    assert parsed.structured_data["trend"] == "unknown"


def test_parser_does_not_generate_trade_recommendations(tmp_path):
    path = make_image(tmp_path / "chart.png")
    parsed = ChartParser(StubVision({
        "trend": "uptrend", "entry": 100, "stop": 95, "target": 110,
        "probability": 0.8, "support_levels": [98],
    })).parse(file_path=path, user_id="u1", source_name="TradingView")
    assert not {"entry", "stop", "target", "probability"}.intersection(parsed.structured_data)
    assert parsed.structured_data["support_levels"] == [98]


def test_chart_below_threshold_adds_warning(tmp_path):
    path = make_image(tmp_path / "chart.png")
    parsed = ChartParser(StubVision(confidence=0.5)).parse(
        file_path=path, user_id="u1", source_name="TradingView"
    )
    assert any("below" in warning for warning in parsed.warnings)


def test_stale_live_feed_does_not_satisfy_current_spot():
    registry = EvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="stale", user_id="u1", evidence_type=EvidenceType.LIVE_FEED,
        source_name="Feed", ticker_symbols=["SPY"], confidence=1.0,
        captured_at=datetime.now(timezone.utc) - timedelta(hours=1),
    ))
    result = build_what_you_need(_profile(), registry, "trade_analysis", "SPY")
    assert "current spot" in result.missing_items


def test_fresh_live_feed_satisfies_current_spot_and_timestamp():
    registry = EvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="fresh", user_id="u1", evidence_type=EvidenceType.LIVE_FEED,
        source_name="Feed", ticker_symbols=["SPY"], confidence=1.0,
        captured_at=datetime.now(timezone.utc),
    ))
    result = build_what_you_need(_profile(), registry, "trade_analysis", "SPY")
    assert "current spot" not in result.missing_items
    assert "timestamp" not in result.missing_items
