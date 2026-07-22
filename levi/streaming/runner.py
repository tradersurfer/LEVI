"""Orchestrate the existing LEVI specialists and stream their real results."""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from levi.agents import AtlasAgent, ConsensusEngine, GuardianAgent, LensAgent, ScoutAgent, ScribeAgent
from levi.agents.models import AgentAnalysisRequest, AgentDecision, AgentVerdict, ConsensusDecision
from levi.evidence.registry import EvidenceRegistry
from levi.llm import MockLLMAdapter, OpenRouterAdapter
from levi.market_data.models import QuoteValidationResult
from levi.profiles.models import UserTradingProfile
from levi.risk.models import TradeRiskRequest

from .bus import EventBus
from .events import AgentProgressEvent, AgentStatus


class ConcurrentAnalysisError(RuntimeError):
    """Raised when a user already has an active analysis run."""


RiskRequestFactory = Callable[[UserTradingProfile, AgentAnalysisRequest], TradeRiskRequest]


class PipelineRunner:
    """Run the canonical specialists, GUARDIAN, and consensus exactly once per user."""

    def __init__(
        self,
        *,
        registry: EvidenceRegistry,
        profile_loader: Callable[[str], UserTradingProfile],
        bus: EventBus,
        agents: tuple[Any, ...] | None = None,
        guardian: GuardianAgent | None = None,
        consensus: ConsensusEngine | None = None,
        scribe: ScribeAgent | None = None,
        risk_request_factory: RiskRequestFactory | None = None,
    ) -> None:
        self.registry = registry
        self.profile_loader = profile_loader
        self.bus = bus
        llm = self._configured_llm()
        self.agents = agents or (ScoutAgent(llm), AtlasAgent(llm), LensAgent(llm))
        self.guardian = guardian or GuardianAgent()
        self.consensus = consensus or ConsensusEngine()
        self.scribe = scribe or ScribeAgent()
        self.risk_request_factory = risk_request_factory or self._safe_risk_request
        self._active: dict[str, str] = {}
        self._tasks: dict[str, asyncio.Task[ConsensusDecision | None]] = {}
        self._results: dict[str, ConsensusDecision] = {}

    def run(self, user_id: str, symbol: str) -> str:
        """Start a run and return its correlation ID without waiting for analysis."""
        owner = user_id.strip()
        ticker = symbol.strip().upper()
        if not owner:
            raise ValueError("user_id is required")
        if not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", ticker):
            raise ValueError("symbol is invalid")
        if owner in self._active:
            raise ConcurrentAnalysisError("analysis already running for this user")
        request_id = str(uuid4())
        self._active[owner] = request_id
        task = asyncio.create_task(self._execute(request_id, owner, ticker))
        self._tasks[request_id] = task
        return request_id

    async def wait(self, request_id: str) -> ConsensusDecision | None:
        task = self._tasks.get(request_id)
        if task is None:
            return self._results.get(request_id)
        return await task

    def result(self, request_id: str) -> ConsensusDecision | None:
        return self._results.get(request_id)

    def is_active(self, user_id: str) -> bool:
        return user_id in self._active

    async def _execute(self, request_id: str, user_id: str, symbol: str) -> ConsensusDecision | None:
        sequence = 0

        async def emit(agent_name: str, status: AgentStatus, **values: Any) -> None:
            nonlocal sequence
            sequence += 1
            await self.bus.publish(AgentProgressEvent(
                event_id=str(uuid4()), request_id=request_id, user_id=user_id,
                symbol=symbol, agent_name=agent_name, status=status,
                verdict=values.get("verdict"), confidence=values.get("confidence"),
                summary=values.get("summary"), sequence=sequence,
            ))

        try:
            profile = self.profile_loader(user_id)
            request = AgentAnalysisRequest(
                user_id=user_id,
                symbol=symbol,
                trading_mode=profile.trading_mode,
                instrument_type=profile.instrument_type,
                evidence=tuple(self.registry.by_user(user_id)),
                quote=None,
                portfolio_context={
                    "account_value": profile.account_value,
                    "buying_power": profile.buying_power,
                },
            )
            decisions: list[AgentDecision] = []
            for agent in self.agents:
                await emit(agent.agent_name, AgentStatus.QUEUED)
                await emit(agent.agent_name, AgentStatus.RUNNING)
                decision = await asyncio.to_thread(agent.analyze, request)
                decisions.append(decision)
                await emit(
                    agent.agent_name, AgentStatus.COMPLETE,
                    verdict=decision.verdict, confidence=decision.confidence,
                    summary=decision.summary,
                )

            await emit("GUARDIAN", AgentStatus.QUEUED)
            await emit("GUARDIAN", AgentStatus.RUNNING)
            risk_request = self.risk_request_factory(profile, request)
            guardian = await asyncio.to_thread(self.guardian.analyze, risk_request)
            guardian_status = AgentStatus.COMPLETE if guardian.allowed else AgentStatus.BLOCKED
            await emit(
                "GUARDIAN", guardian_status,
                verdict=None if guardian.allowed else AgentVerdict.BLOCK,
                confidence=1.0,
                summary="Risk rules passed" if guardian.allowed else "; ".join(guardian.violations),
            )

            consensus = await asyncio.to_thread(
                self.consensus.evaluate,
                user_id=user_id,
                symbol=symbol,
                decisions=tuple(decisions),
                guardian=guardian,
            )
            self._results[request_id] = consensus

            # The existing Phase 4 SCRIBE contract narrates completed consensus,
            # so its real call correctly occurs after consensus evaluation.
            await emit("SCRIBE", AgentStatus.QUEUED)
            await emit("SCRIBE", AgentStatus.RUNNING)
            narrative = await asyncio.to_thread(self.scribe.summarize, tuple(decisions), consensus)
            await emit(
                "SCRIBE", AgentStatus.COMPLETE, verdict=consensus.verdict,
                confidence=consensus.confidence, summary=narrative.summary,
            )

            await emit("CONSENSUS", AgentStatus.QUEUED)
            await emit("CONSENSUS", AgentStatus.RUNNING)
            await emit(
                "CONSENSUS",
                AgentStatus.COMPLETE if consensus.approved else AgentStatus.BLOCKED,
                verdict=consensus.verdict,
                confidence=consensus.confidence,
                summary="Consensus approved" if consensus.approved else "; ".join(consensus.warnings),
            )
            return consensus
        except Exception as exc:
            await emit(
                "CONSENSUS", AgentStatus.ERROR,
                verdict=AgentVerdict.BLOCK,
                summary=f"Analysis failed safely: {type(exc).__name__}",
            )
            return None
        finally:
            self._active.pop(user_id, None)
            self._tasks.pop(request_id, None)

    @staticmethod
    def _configured_llm():
        models = ("LEVI_SCOUT_MODEL", "LEVI_ATLAS_MODEL", "LEVI_LENS_MODEL")
        if os.getenv("OPENROUTER_API_KEY") and all(os.getenv(name) for name in models):
            return OpenRouterAdapter()
        safe_response = {
            "verdict": AgentVerdict.INSUFFICIENT_EVIDENCE.value,
            "confidence": 0.0,
            "summary": "Mock adapter used; no hosted model is configured",
            "reasoning": [],
            "warnings": ["Hosted specialist model is not configured"],
        }
        return MockLLMAdapter((safe_response, safe_response, safe_response))

    @staticmethod
    def _safe_risk_request(profile: UserTradingProfile, request: AgentAnalysisRequest) -> TradeRiskRequest:
        """Build a fail-closed risk request when no execution proposal exists."""
        return TradeRiskRequest(
            profile=profile,
            dte=0,
            maximum_loss=0,
            daily_loss_pct=0,
            weekly_loss_pct=0,
            open_positions=0,
            correlated_positions=0,
            averaging_down=False,
            order_type="limit",
            limit_price=None,
            quote_validation=QuoteValidationResult(False, ["quote unavailable"], []),
            quote_age_seconds=None,
            buying_power=profile.buying_power,
            approval_reference=None,
        )
