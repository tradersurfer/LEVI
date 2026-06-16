"""
╔══════════════════════════════════════════════════════════════════╗
║   consensus_engine.py — Tri-Agent Consensus Network               ║
║                                                                  ║
║   GROK    → Sentiment & Momentum Agent  (sentiment_score)        ║
║   CLAUDE  → Technical Chart Analyst     (technical_bias)         ║
║   GEMINI  → Chief Risk Officer          (APPROVED / REJECTED)    ║
║                                                                  ║
║   3/3 UNANIMOUS vote required before any live execution routes. ║
╚══════════════════════════════════════════════════════════════════╝

DESIGN PRINCIPLE — code enforces, models advise:
The Master Risk Moat is validated PROGRAMMATICALLY in Python first.
A trade that violates the moat is rejected before a single API call.
The LLM layer is a second semantic veto, never the only line of defense.
"""

import os
import re
import json
import logging
import requests
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Optional

log = logging.getLogger("JECI.consensus")

# ─── API KEYS / MODELS (all overridable in .env) ─────────────────────────────
XAI_API_KEY       = os.getenv("XAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY    = os.getenv("GOOGLE_API_KEY", "")

GROK_MODEL   = os.getenv("GROK_MODEL",   "grok-4")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT_SEC", "25"))


# ═══════════════════════════════════════════════════════════════════════════════
# TRADE PROPOSAL
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TradeProposal:
    account_tier:   str      # ROBYHOOD | TRADERSURFER
    symbol:         str
    direction:      str      # CALL | PUT
    option_symbol:  str
    strike:         float
    dte:            int
    premium:        float    # per-contract mid
    quantity:       int
    net_liq:        float
    rsi15:          float    # 15-minute RSI at proposal time
    market_state:   str      # NORMAL | BULL_TRAP | WATERFALL | V_BOTTOM
    state_locks:    dict = field(default_factory=dict)

    @property
    def total_cost(self) -> float:
        return round(self.premium * 100 * self.quantity, 2)


@dataclass
class ConsensusResult:
    approved:        bool
    moat_passed:     bool
    sentiment_score: Optional[float]
    technical_bias:  Optional[str]
    cro_verdict:     Optional[str]
    votes:           str          # e.g. "3/3" or "MOAT-FAIL"
    notes:           list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# THE MASTER RISK MOAT — programmatic, runs first, cannot be talked around
# ═══════════════════════════════════════════════════════════════════════════════

SANDBOX_MAX_PREMIUM_DOLLARS = float(os.getenv("SANDBOX_MAX_PREMIUM", "150.00"))
LARGE_ACCT_MAX_POSITION_PCT = float(os.getenv("LARGE_ACCT_POSITION_PCT", "3.29"))
ABSOLUTE_MIN_DTE            = 4
RSI_LONG_LOCKOUT            = 60     # no CALL entries if RSI15 > 60 (FOMO chase)
RSI_SHORT_LOCKOUT           = 20     # no PUT entries if RSI15 < 20 (compressed spring)


class RiskMoat:
    """Hardcoded parameters. Violations = instant rejection, zero API spend."""

    @staticmethod
    def validate(p: TradeProposal) -> tuple[bool, list[str]]:
        fails: list[str] = []

        # ── 1. The 4DTE Minimum Buffer ───────────────────────────────────────
        if p.dte < ABSOLUTE_MIN_DTE:
            fails.append(f"4DTE RULE: {p.dte} DTE < {ABSOLUTE_MIN_DTE} minimum — "
                         f"0–3DTE theta traps are banned outright")

        # ── 2. Capital Allocation Rule ───────────────────────────────────────
        if p.account_tier == "ROBYHOOD":
            if p.total_cost > SANDBOX_MAX_PREMIUM_DOLLARS:
                fails.append(f"SANDBOX CAP: total premium ${p.total_cost:.2f} > "
                             f"${SANDBOX_MAX_PREMIUM_DOLLARS:.2f} hard ceiling")
        else:
            max_dollars = p.net_liq * (LARGE_ACCT_MAX_POSITION_PCT / 100)
            if p.total_cost > max_dollars:
                fails.append(f"POSITION RATIO: ${p.total_cost:,.0f} > "
                             f"{LARGE_ACCT_MAX_POSITION_PCT}% of net liq (${max_dollars:,.0f})")

        # ── 3. RSI Lockouts (anti-FOMO / anti-spring-chase) ──────────────────
        if p.direction == "CALL" and p.rsi15 > RSI_LONG_LOCKOUT:
            fails.append(f"RSI LOCKOUT: 15m RSI {p.rsi15:.0f} > {RSI_LONG_LOCKOUT} — "
                         f"long entries locked (gap-trap protection)")
        if p.direction == "PUT" and p.rsi15 < RSI_SHORT_LOCKOUT:
            fails.append(f"RSI LOCKOUT: 15m RSI {p.rsi15:.0f} < {RSI_SHORT_LOCKOUT} — "
                         f"short entries locked (liquidation-spring protection)")

        # ── 4. Market State Locks ────────────────────────────────────────────
        locks = p.state_locks or {}
        if locks.get("bias_neutral"):
            fails.append(f"STATE LOCK [{p.market_state}]: bias forced NEUTRAL — "
                         f"hold until VWAP retest / gap-fill")
        if locks.get("block_puts") and p.direction == "PUT":
            fails.append(f"STATE LOCK [{p.market_state}]: short execution LOCKED")
        min_dte_override = locks.get("min_dte_override")
        if min_dte_override and p.dte < min_dte_override:
            fails.append(f"STATE LOCK [{p.market_state}]: only DTE >= "
                         f"{min_dte_override} structural assets allowed (have {p.dte})")

        return (len(fails) == 0), fails


# ═══════════════════════════════════════════════════════════════════════════════
# JSON EXTRACTION HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 1 — GROK · Sentiment & Momentum Hub
# ═══════════════════════════════════════════════════════════════════════════════

class GrokSentimentAgent:
    def available(self) -> bool:
        return bool(XAI_API_KEY)

    def get_sentiment(self, symbol: str) -> Optional[float]:
        """Returns sentiment_score in [-1.0, 1.0] or None on failure."""
        if not self.available():
            return None
        prompt = (
            f"You are the Momentum & Sentiment Agent. Scan current social sentiment "
            f"velocity and breaking news flow for ticker {symbol}. Is sentiment "
            f"heavily extended to the upside or downside? "
            f'Return ONLY a JSON object: {{"sentiment_score": <float -1.0 to 1.0>}}'
        )
        try:
            r = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {XAI_API_KEY}",
                         "Content-Type": "application/json"},
                json={"model": GROK_MODEL,
                      "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.2},
                timeout=AGENT_TIMEOUT,
            )
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            data = _extract_json(text)
            score = float(data.get("sentiment_score")) if data else None
            return max(-1.0, min(1.0, score)) if score is not None else None
        except Exception as e:
            log.warning(f"Grok agent failed: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 2 — CLAUDE · Technical Chart Analyst
# ═══════════════════════════════════════════════════════════════════════════════

class ClaudeTechnicalAgent:
    def available(self) -> bool:
        return bool(ANTHROPIC_API_KEY)

    def get_bias(self, symbol: str, metrics: dict) -> Optional[str]:
        """Returns BUY / SELL / NEUTRAL or None on failure."""
        if not self.available():
            return None
        prompt = (
            f"You are the Technical Chart Analyst. Evaluate the current 15-minute "
            f"and daily chart metrics for ticker {symbol}:\n"
            f"{json.dumps(metrics, indent=2)}\n\n"
            f"Consider Bollinger Band variance, VWAP distance, EMA20/SMA50 structure, "
            f"and RSI levels. "
            f'Return ONLY a JSON object: {{"technical_bias": "BUY" | "SELL" | "NEUTRAL"}}'
        )
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": ANTHROPIC_API_KEY,
                         "anthropic-version": "2023-06-01",
                         "Content-Type": "application/json"},
                json={"model": CLAUDE_MODEL, "max_tokens": 200,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=AGENT_TIMEOUT,
            )
            r.raise_for_status()
            text = r.json()["content"][0]["text"]
            data = _extract_json(text)
            bias = (data or {}).get("technical_bias", "").upper()
            return bias if bias in ("BUY", "SELL", "NEUTRAL") else None
        except Exception as e:
            log.warning(f"Claude agent failed: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 3 — GEMINI · Chief Risk Officer (final veto)
# ═══════════════════════════════════════════════════════════════════════════════

class GeminiRiskOfficer:
    def available(self) -> bool:
        return bool(GOOGLE_API_KEY)

    def review(self, p: TradeProposal,
               sentiment: Optional[float], bias: Optional[str]) -> Optional[str]:
        """Returns APPROVED / REJECTED or None on failure."""
        if not self.available():
            return None
        prompt = (
            "You are the Chief Risk Officer. Cross-reference the proposed trade "
            "against the Master Risk Moat:\n"
            f"- Sandbox (ROBYHOOD) max total premium per trade: ${SANDBOX_MAX_PREMIUM_DOLLARS:.0f}\n"
            f"- Large account single-position max: {LARGE_ACCT_MAX_POSITION_PCT}% of net liq\n"
            f"- Mandatory {ABSOLUTE_MIN_DTE} DTE minimum buffer (0–3 DTE banned)\n"
            f"- Absolute lockout: 15m RSI < {RSI_SHORT_LOCKOUT} blocks shorts, "
            f"15m RSI > {RSI_LONG_LOCKOUT} blocks longs\n"
            "- Limit orders only; averaging down is banned\n\n"
            "PROPOSED TRADE:\n" + json.dumps({
                'account': p.account_tier, 'symbol': p.symbol,
                'direction': p.direction, 'option': p.option_symbol,
                'strike': p.strike, 'dte': p.dte,
                'premium': p.premium, 'quantity': p.quantity,
                'total_cost': p.total_cost, 'net_liq': p.net_liq,
                'rsi15': p.rsi15, 'market_state': p.market_state,
            }, indent=2) + "\n\n"
            f"AGENT INPUTS: grok_sentiment={sentiment}, claude_bias={bias}\n\n"
            'Return ONLY a JSON object: {"verdict": "APPROVED" | "REJECTED", '
            '"reason": "<one sentence>"}'
        )
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=AGENT_TIMEOUT,
            )
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            data = _extract_json(text)
            verdict = (data or {}).get("verdict", "").upper()
            if verdict in ("APPROVED", "REJECTED"):
                if data.get("reason"):
                    log.info(f"  CRO reason: {data['reason']}")
                return verdict
            return None
        except Exception as e:
            log.warning(f"Gemini CRO failed: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# CONSENSUS ROUTER — fires Grok + Claude in parallel, Gemini last
# ═══════════════════════════════════════════════════════════════════════════════

SENTIMENT_ALIGN_THRESHOLD = 0.15   # CALL needs > +0.15, PUT needs < -0.15

class ConsensusEngine:
    def __init__(self):
        self.grok   = GrokSentimentAgent()
        self.claude = ClaudeTechnicalAgent()
        self.gemini = GeminiRiskOfficer()

    def agents_online(self) -> dict:
        return {"grok": self.grok.available(),
                "claude": self.claude.available(),
                "gemini": self.gemini.available()}

    def evaluate(self, p: TradeProposal, metrics: dict) -> ConsensusResult:
        notes: list[str] = []

        # ── LAYER 0: Programmatic Risk Moat (free, instant, absolute) ─────────
        moat_ok, fails = RiskMoat.validate(p)
        if not moat_ok:
            for f in fails:
                notes.append(f"⛔ {f}")
            return ConsensusResult(
                approved=False, moat_passed=False,
                sentiment_score=None, technical_bias=None, cro_verdict=None,
                votes="MOAT-FAIL", notes=notes,
            )
        notes.append("✅ Risk Moat passed (programmatic)")

        online = self.agents_online()
        if not all(online.values()):
            missing = [k for k, v in online.items() if not v]
            notes.append(f"⚠ Agents offline: {', '.join(missing)} — "
                         f"3/3 unanimous vote impossible. Trade NOT approved for "
                         f"live routing. (Set API keys or CONSENSUS_REQUIRED=false.)")
            return ConsensusResult(
                approved=False, moat_passed=True,
                sentiment_score=None, technical_bias=None, cro_verdict=None,
                votes=f"{sum(online.values())}/3-OFFLINE", notes=notes,
            )

        # ── LAYER 1: Grok + Claude in parallel ────────────────────────────────
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_sent = pool.submit(self.grok.get_sentiment, p.symbol)
            f_bias = pool.submit(self.claude.get_bias, p.symbol, metrics)
            try:
                sentiment = f_sent.result(timeout=AGENT_TIMEOUT + 5)
                bias      = f_bias.result(timeout=AGENT_TIMEOUT + 5)
            except FuturesTimeout:
                sentiment, bias = None, None

        if sentiment is None or bias is None:
            notes.append("⚠ Agent response failure — no unanimous vote possible")
            return ConsensusResult(
                approved=False, moat_passed=True,
                sentiment_score=sentiment, technical_bias=bias, cro_verdict=None,
                votes="AGENT-FAIL", notes=notes,
            )

        notes.append(f"Grok sentiment_score: {sentiment:+.2f}")
        notes.append(f"Claude technical_bias: {bias}")

        # ── Alignment check ───────────────────────────────────────────────────
        sentiment_aligned = (
            (p.direction == "CALL" and sentiment > SENTIMENT_ALIGN_THRESHOLD) or
            (p.direction == "PUT"  and sentiment < -SENTIMENT_ALIGN_THRESHOLD)
        )
        bias_aligned = (
            (p.direction == "CALL" and bias == "BUY") or
            (p.direction == "PUT"  and bias == "SELL")
        )

        if not sentiment_aligned:
            notes.append(f"✗ Grok VOTE: sentiment {sentiment:+.2f} does not "
                         f"support {p.direction}")
        if not bias_aligned:
            notes.append(f"✗ Claude VOTE: bias {bias} does not support {p.direction}")

        if not (sentiment_aligned and bias_aligned):
            return ConsensusResult(
                approved=False, moat_passed=True,
                sentiment_score=sentiment, technical_bias=bias, cro_verdict=None,
                votes=f"{int(sentiment_aligned)+int(bias_aligned)}/3", notes=notes,
            )

        # ── LAYER 2: Gemini CRO final veto ────────────────────────────────────
        verdict = self.gemini.review(p, sentiment, bias)
        if verdict != "APPROVED":
            notes.append(f"✗ Gemini CRO: {verdict or 'NO-RESPONSE'}")
            return ConsensusResult(
                approved=False, moat_passed=True,
                sentiment_score=sentiment, technical_bias=bias,
                cro_verdict=verdict, votes="2/3", notes=notes,
            )

        notes.append("✓ Gemini CRO: APPROVED")
        notes.append("🏛 CONSENSUS: 3/3 UNANIMOUS — cleared for routing")
        return ConsensusResult(
            approved=True, moat_passed=True,
            sentiment_score=sentiment, technical_bias=bias,
            cro_verdict="APPROVED", votes="3/3", notes=notes,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Smoke test the moat with a deliberately bad trade (1 DTE)
    bad = TradeProposal(
        account_tier="ROBYHOOD", symbol="SPY", direction="CALL",
        option_symbol="SPY 260612C00750000", strike=750, dte=1,
        premium=1.50, quantity=2, net_liq=1200, rsi15=72,
        market_state="BULL_TRAP", state_locks={"bias_neutral": True},
    )
    ok, fails = RiskMoat.validate(bad)
    print(f"\nMoat passed: {ok}")
    for f in fails:
        print(f"  ⛔ {f}")
