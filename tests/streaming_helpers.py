from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from levi.agents.models import AgentDecision, AgentVerdict
from levi.market_data.models import QuoteValidationResult
from levi.profiles.models import UserTradingProfile
from levi.risk.models import TradeRiskRequest


def profile(user_id: str = "u1") -> UserTradingProfile:
    return UserTradingProfile(
        user_id=user_id,
        display_name="Streaming User",
        account_value=10_000,
        buying_power=5_000,
    )


def profile_loader(user_id: str) -> UserTradingProfile:
    if user_id == "missing":
        raise FileNotFoundError(user_id)
    return profile(user_id)


class FixedAgent:
    def __init__(self, name: str, verdict: AgentVerdict = AgentVerdict.BULLISH, confidence: float = 0.9):
        self.agent_name = name
        self.verdict = verdict
        self.confidence = confidence
        self.calls = 0

    def analyze(self, request):
        self.calls += 1
        return AgentDecision(
            decision_id=f"{self.agent_name.lower()}-{self.calls}",
            user_id=request.user_id,
            symbol=request.symbol,
            agent_name=self.agent_name,
            verdict=self.verdict,
            confidence=self.confidence,
            summary=f"{self.agent_name} summary",
            reasoning=("fixture",),
            evidence_ids=(),
            warnings=(),
            created_at=datetime.now(timezone.utc),
            processing_time_ms=1,
        )


class SlowAgent(FixedAgent):
    def analyze(self, request):
        import time
        time.sleep(0.1)
        return super().analyze(request)


def allowed_risk(profile_value, _request):
    return TradeRiskRequest(
        profile=profile_value,
        dte=10,
        maximum_loss=50,
        daily_loss_pct=0,
        weekly_loss_pct=0,
        open_positions=0,
        correlated_positions=0,
        averaging_down=False,
        order_type="limit",
        limit_price=1,
        quote_validation=QuoteValidationResult(True, [], []),
        quote_age_seconds=1,
        buying_power=profile_value.buying_power,
        approval_reference="test-approval",
    )


async def collect_run(runner, bus, user_id="u1", symbol="SPY"):
    queue = bus.subscribe(user_id)
    request_id = runner.run(user_id, symbol)
    result = await runner.wait(request_id)
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())
    bus.unsubscribe(user_id, queue)
    return request_id, result, events


def run(coroutine):
    return asyncio.run(coroutine)
