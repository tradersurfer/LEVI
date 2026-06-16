"""
╔══════════════════════════════════════════════════════════════════╗
║   market_state.py — Programmatic Market State Triggers           ║
║   Derived from live tape reading: Bull Trap / Waterfall / V-Bot  ║
╚══════════════════════════════════════════════════════════════════╝

The bot must recognize shifting intraday macro environments so it never
buys into algorithmic traps. Three states, hardcoded from session logs:

  STATE 1 — MORNING GAP-UP BULL TRAP
    Condition: index gaps up > 0.5% at open AND 15m RSI > 60
    Action:    bias = NEUTRAL. Hold execution until VWAP retest / gap-fill.

  STATE 2 — WATERFALL LIQUIDATION FLUSH
    Condition: index breaks VWAP, drops 1%+ from HOD, 15m RSI < 20
    Action:    LOCK short execution. Only scaled limit orders on
               long-dated (DTE >= 60) structural assets allowed.

  STATE 3 — ALGORITHMIC V-BOTTOM RECOVERY
    Condition: extreme washout earlier in session + price reclaiming VWAP
               with RSI recovering above 40
    Action:    ENFORCE PATIENCE. Hold long-dated positions. Suppress
               panic stops on DTE >= 60 contracts; alert instead.
"""

import json
import time
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─── STATES ──────────────────────────────────────────────────────────────────
class MarketState(Enum):
    NORMAL    = "NORMAL"
    BULL_TRAP = "BULL_TRAP"       # State 1
    WATERFALL = "WATERFALL"       # State 2
    V_BOTTOM  = "V_BOTTOM"        # State 3


@dataclass
class StateReport:
    state:        MarketState
    index:        str
    gap_pct:      float
    rsi15:        float
    rsi15_session_low: float
    vwap:         float
    last:         float
    drop_from_hod_pct: float
    above_vwap:   bool
    details:      str
    # Execution locks the bot must obey this cycle
    locks: dict = field(default_factory=dict)
    #   locks = {
    #     "bias_neutral":      bool,   # State 1 — no new entries on index/correlated
    #     "block_puts":        bool,   # State 2 — never chase puts into a spring
    #     "min_dte_override":  int,    # State 2 — only DTE >= 60 longs allowed
    #     "patience_matrix":   bool,   # State 3 — suppress stops on DTE >= 60
    #   }


# ─── DATA FETCH (Yahoo — no key) ─────────────────────────────────────────────
def _yahoo(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())

def fetch_intraday(symbol: str, interval: str = "15m") -> dict:
    """Returns dict with opens/highs/lows/closes/volumes + prev_close, today_open."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?interval={interval}&range=1d")
    raw    = _yahoo(url)
    result = raw["chart"]["result"][0]
    meta   = result.get("meta", {})
    q      = result["indicators"]["quote"][0]

    def clean(arr): return [x for x in (arr or []) if x is not None]

    closes  = clean(q.get("close"))
    return {
        "opens":      clean(q.get("open")),
        "highs":      clean(q.get("high")),
        "lows":       clean(q.get("low")),
        "closes":     closes,
        "volumes":    clean(q.get("volume")),
        "prev_close": float(meta.get("chartPreviousClose") or meta.get("previousClose") or 0),
        "today_open": closes[0] if closes else 0.0,
        "last":       closes[-1] if closes else 0.0,
    }


# ─── INDICATORS ──────────────────────────────────────────────────────────────
def rsi(values: list[float], period: int = 14) -> float:
    if len(values) < period + 1:
        return 50.0
    deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    gains  = [d if d > 0 else 0.0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0.0 for d in deltas[-period:]]
    ag, al = sum(gains) / period, sum(losses) / period
    return 100.0 if al == 0 else 100 - (100 / (1 + ag / al))

def rsi_series(values: list[float], period: int = 14) -> list[float]:
    """RSI value at each bar — used to find the session RSI low (washout proof)."""
    out = []
    for i in range(period + 1, len(values) + 1):
        out.append(rsi(values[:i], period))
    return out

def vwap(highs: list[float], lows: list[float],
         closes: list[float], volumes: list[float]) -> float:
    n = min(len(highs), len(lows), len(closes), len(volumes))
    if n == 0:
        return 0.0
    num = den = 0.0
    for i in range(n):
        tp   = (highs[i] + lows[i] + closes[i]) / 3
        num += tp * volumes[i]
        den += volumes[i]
    return num / den if den else closes[-1]


# ─── STATE ENGINE ────────────────────────────────────────────────────────────
class MarketStateEngine:
    """
    Call .detect() once per scan cycle. Returns a StateReport whose .locks
    dict the main bot MUST obey before any entry or exit.
    """

    def __init__(self, index_symbol: str = "SPY"):
        self.index = index_symbol
        self._last_report: Optional[StateReport] = None

    def detect(self) -> StateReport:
        try:
            d = fetch_intraday(self.index, "15m")
        except Exception as e:
            return StateReport(
                state=MarketState.NORMAL, index=self.index,
                gap_pct=0, rsi15=50, rsi15_session_low=50, vwap=0, last=0,
                drop_from_hod_pct=0, above_vwap=True,
                details=f"Data fetch failed ({e}) — defaulting NORMAL, no locks",
            )

        closes = d["closes"]
        if len(closes) < 3 or not d["prev_close"]:
            return StateReport(
                state=MarketState.NORMAL, index=self.index,
                gap_pct=0, rsi15=50, rsi15_session_low=50, vwap=0,
                last=d["last"], drop_from_hod_pct=0, above_vwap=True,
                details="Insufficient intraday bars — NORMAL",
            )

        gap_pct   = (d["today_open"] - d["prev_close"]) / d["prev_close"] * 100
        r_series  = rsi_series(closes, 14) or [50.0]
        rsi15     = r_series[-1]
        rsi_low   = min(r_series)
        vw        = vwap(d["highs"], d["lows"], closes, d["volumes"])
        last      = d["last"]
        hod       = max(d["highs"]) if d["highs"] else last
        drop_hod  = (hod - last) / hod * 100 if hod else 0
        above_vw  = last >= vw

        state   = MarketState.NORMAL
        locks   = {}
        details = "Normal regime — standard rules apply"

        # ── STATE 2: Waterfall Liquidation Flush ─────────────────────────────
        if (not above_vw) and drop_hod >= 1.0 and rsi15 < 20:
            state = MarketState.WATERFALL
            locks = {"block_puts": True, "min_dte_override": 60}
            details = (f"WATERFALL: {self.index} below VWAP {vw:.2f}, "
                       f"-{drop_hod:.1f}% from HOD, RSI15 {rsi15:.0f} < 20. "
                       f"Shorts LOCKED. Only DTE>=60 structural longs via limit.")

        # ── STATE 1: Morning Gap-Up Bull Trap ────────────────────────────────
        elif gap_pct > 0.5 and rsi15 > 60:
            state = MarketState.BULL_TRAP
            locks = {"bias_neutral": True}
            details = (f"BULL TRAP: gapped +{gap_pct:.2f}%, RSI15 {rsi15:.0f} > 60. "
                       f"Bias NEUTRAL — hold execution until VWAP retest / gap-fill.")

        # ── STATE 3: Algorithmic V-Bottom Recovery ───────────────────────────
        elif rsi_low < 25 and rsi15 > 40 and above_vw:
            state = MarketState.V_BOTTOM
            locks = {"patience_matrix": True}
            details = (f"V-BOTTOM: session RSI washout low {rsi_low:.0f}, now "
                       f"recovered to {rsi15:.0f} above VWAP {vw:.2f}. "
                       f"PATIENCE MATRIX — hold long-dated, no panic exits.")

        report = StateReport(
            state=state, index=self.index,
            gap_pct=round(gap_pct, 2), rsi15=round(rsi15, 1),
            rsi15_session_low=round(rsi_low, 1),
            vwap=round(vw, 2), last=round(last, 2),
            drop_from_hod_pct=round(drop_hod, 2),
            above_vwap=above_vw, details=details, locks=locks,
        )
        self._last_report = report
        return report


if __name__ == "__main__":
    eng = MarketStateEngine("SPY")
    rep = eng.detect()
    print(f"\n  STATE: {rep.state.value}")
    print(f"  {rep.details}")
    print(f"  gap {rep.gap_pct:+.2f}%  RSI15 {rep.rsi15}  "
          f"VWAP {rep.vwap}  last {rep.last}  locks {rep.locks}\n")
