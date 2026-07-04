"""
╔══════════════════════════════════════════════════════════════════╗
║     JECI OPTIONS BOT v2  ·  Tri-Tier + Consensus + State Engine  ║
║                                                                  ║
║  Core  — Master Swing Desk    (institutional alpha)     ║
║  Sandbox      — Kids' Sandbox        ($150 cap · 4DTE min)     ║
║  Family HODL   — Generational Trust   (equity alerts only)      ║
║                                                                  ║
║  NEW IN v2 (merged from live-tape session):                      ║
║   · Market State Engine  — Bull Trap / Waterfall / V-Bottom     ║
║   · Tri-Agent Consensus  — Grok + Claude + DeepSeek, 3/3 vote   ║
║   · Master Risk Moat     — programmatic, runs before any LLM    ║
║   · Averaging-down ban   + daily re-entry blocklist after stops ║
║   · Patience Matrix      — no panic stops on DTE>=60 in flush   ║
║   · STAX alpha tickers   — GLXY, NOK added to Core      ║
╚══════════════════════════════════════════════════════════════════╝

RUN:
  pip install requests pandas numpy python-dotenv schedule
  cp .env.example .env   (fill in credentials)
  python jeci_options_bot.py
"""

import os, time, json, logging, schedule, urllib.request
from datetime import datetime, date
from dataclasses import dataclass
from typing import Optional
import requests
from dotenv import load_dotenv

from bot.market_state import MarketStateEngine, MarketState, rsi as rsi_calc
from bot.consensus_engine import (
    ConsensusEngine, TradeProposal, RiskMoat,
    SANDBOX_MAX_PREMIUM_DOLLARS, LARGE_ACCT_MAX_POSITION_PCT,
)
from agents.scout import Scout as _Scout
from agents.atlas import Atlas as _Atlas
from agents.lens import Lens as _Lens

# Module-level sub-agent singletons (instantiated once, reused every scan)
SCOUT = _Scout()
ATLAS = _Atlas()
LENS  = _Lens()

load_dotenv()

# ── White-label config ────────────────────────────────────────────────────────
import json as _json
LEVI_CONFIG_PATH = os.getenv("LEVI_CONFIG_PATH", "./levi_config.json")
try:
    with open(LEVI_CONFIG_PATH) as _f:
        LEVI_CONFIG = _json.load(_f)
except FileNotFoundError:
    LEVI_CONFIG = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(), logging.FileHandler("jeci_bot.log")],
)
log = logging.getLogger("JECI")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

PAPER              = os.getenv("TASTYTRADE_PAPER", "true").lower() == "true"
AUTO_EXECUTE       = os.getenv("AUTO_EXECUTE", "false").lower() == "true"
CONSENSUS_REQUIRED = os.getenv("CONSENSUS_REQUIRED", "true").lower() == "true"

TT_USERNAME = os.getenv("TT_USERNAME", "")
TT_PASSWORD = os.getenv("TT_PASSWORD", "")

ACCT_CORE = os.getenv("ACCT_CORE", "")
ACCT_SANDBOX     = os.getenv("ACCT_SANDBOX", "")
ACCT_HODL         = os.getenv("ACCT_HODL", "")

BASE_URL = "https://api.cert.tastyworks.com" if PAPER else "https://api.tastyworks.com"

# ─── TIER 1: SANDBOX ────────────────────────────────────────────────────────
SANDBOX_WATCHLIST = ["CLSK","MARA","RIOT","HUT","QS","SOFI","RKLB","TWST","PHAR"]
SANDBOX_RULES = {
    "max_alloc_pct":   15,
    "max_premium_dollars": SANDBOX_MAX_PREMIUM_DOLLARS,  # $150 hard ceiling per trade
    "min_dte":         4,
    "max_premium":     2.00,
    "use_spreads_on":  ["SPY","XSP"],
    "runner_trigger":  1.00,
    "stop_loss_pct":   0.33,        # tightened — SPY $740P ledger entry cut at -33%
    "profit_target":   1.50,
}

# ─── TIER 2: CORE (+ STAX institutional alpha) ───────────────────────
CORE_WATCHLIST = [
    "SNOW","MU","ASTS","ARM","QCOM","TTD","ACN","NVDA","AMZN","GOOGL",
    "GLXY",   # STAX verified: $500K block sweeps Jun 26 $31/$32 Calls — crypto infra momentum
    "NOK",    # STAX verified: Sep 18 $15C + Jan 2027 $30C accumulation — near-zero theta (-0.0133)
]
CORE_RULES = {
    "min_premium":      3.00,
    "max_premium":      20.00,
    "max_position_pct": LARGE_ACCT_MAX_POSITION_PCT,   # ~3.29% of net liq per position
    "lock_in_velocity": True,
    "cut_dead_weight":  True,
    "idle_cash_deploy": "VGT",
    "runner_trigger":   1.00,
    "stop_loss_pct":    0.50,
    "profit_target":    2.55,
}

# ─── TIER 3: FAMILY HODL ─────────────────────────────────────────────────────
HODL_WATCHLIST = {
    "digital_assets":    ["MSTR","IBIT","MTPLF"],
    "monopolistic_tech": ["AMZN","GOOGL","NVDA","AAPL","MSFT"],
    "defense_intel":     ["PLTR","KTOS","LMT"],
}
HODL_RULES = {"options_allowed": False, "hold_horizon": "30-50yr"}

MARKET_OPEN_MIN  = 9 * 60 + 45
MARKET_CLOSE_MIN = 15 * 60 + 45


# ═══════════════════════════════════════════════════════════════════════════════
# TASTYTRADE SESSION
# ═══════════════════════════════════════════════════════════════════════════════

class TastytradeSession:
    def __init__(self):
        self.token: Optional[str] = None
        self.accounts: dict[str, str] = {}
        self.s = requests.Session()

    def login(self) -> bool:
        if not TT_USERNAME or not TT_PASSWORD:
            log.error("Missing TT_USERNAME / TT_PASSWORD in .env")
            return False
        try:
            r = self.s.post(f"{BASE_URL}/sessions", json={
                "login": TT_USERNAME, "password": TT_PASSWORD, "remember-me": True})
            r.raise_for_status()
            self.token = r.json()["data"]["session-token"]
            self.s.headers.update({"Authorization": self.token})
            log.info(f"✅  Tastytrade login OK ({'PAPER' if PAPER else '🔴 LIVE'})")
            self._map_accounts()
            return True
        except Exception as e:
            log.error(f"Login failed: {e}")
            return False

    def _map_accounts(self):
        r = self.s.get(f"{BASE_URL}/customers/me/accounts")
        r.raise_for_status()
        nums = [i["account"]["account-number"] for i in r.json()["data"]["items"]]
        for label, num in [("CORE", ACCT_CORE),
                           ("SANDBOX", ACCT_SANDBOX), ("HODL", ACCT_HODL)]:
            if num and num in nums:
                self.accounts[label] = num
                log.info(f"   {label}: {num}")
            elif num:
                log.warning(f"   {label}: {num} not found on this login")

    def get_balance(self, acct: str) -> float:
        r = self.s.get(f"{BASE_URL}/accounts/{acct}/balances")
        r.raise_for_status()
        return float(r.json()["data"].get("net-liquidating-value", 0))

    def get_option_chain(self, symbol: str) -> list:
        r = self.s.get(f"{BASE_URL}/option-chains/{symbol}/nested")
        r.raise_for_status()
        return r.json()["data"]["items"]

    def get_quote(self, symbol: str) -> dict:
        r = self.s.get(f"{BASE_URL}/market-data/quotes", params={"symbols[]": symbol})
        r.raise_for_status()
        items = r.json()["data"]["items"]
        return items[0] if items else {}

    def place_order(self, acct: str, option_symbol: str, qty: int,
                    action: str, price: float) -> dict:
        """LIMIT ORDERS ONLY — Master Risk Moat execution protocol."""
        payload = {
            "time-in-force": "Day",
            "order-type": "Limit",          # never market — avoids liquidity haircuts
            "price": str(round(price, 2)),
            "price-effect": "Debit" if "Open" in action and "Buy" in action else "Credit",
            "legs": [{"instrument-type": "Equity Option", "symbol": option_symbol,
                      "quantity": qty, "action": action}],
        }
        r = self.s.post(f"{BASE_URL}/accounts/{acct}/orders", json=payload)
        r.raise_for_status()
        return r.json()["data"]["order"]


# ═══════════════════════════════════════════════════════════════════════════════
# DAILY INDICATORS (Yahoo)
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_closes(symbol: str, days: int = 60) -> list[float]:
    try:
        end, start = int(time.time()), int(time.time()) - (days + 5) * 86400
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
               f"?interval=1d&period1={start}&period2={end}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            raw = json.loads(r.read())
        closes = raw["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c is not None]
    except Exception as e:
        log.warning(f"  fetch_closes({symbol}): {e}")
        return []

def fetch_rsi15(symbol: str) -> float:
    """15-minute RSI for the entry lockout checks."""
    try:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
               f"?interval=15m&range=1d")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            raw = json.loads(r.read())
        closes = [c for c in raw["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                  if c is not None]
        return round(rsi_calc(closes, 14), 1)
    except Exception:
        return 50.0

def ema(p: list[float], n: int) -> float:
    if len(p) < n: return p[-1] if p else 0.0
    k, v = 2/(n+1), p[0]
    for x in p[1:]: v = x*k + v*(1-k)
    return v

def sma(p: list[float], n: int) -> float:
    return sum(p[-n:])/n if len(p) >= n else (p[-1] if p else 0.0)

def bollinger(p: list[float], n: int = 20, m: float = 2.0):
    if len(p) < n:
        x = p[-1] if p else 0.0; return x, x, x
    w   = p[-n:]
    mid = sum(w)/n
    std = (sum((x-mid)**2 for x in w)/n) ** 0.5
    return mid + m*std, mid, mid - m*std


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Signal:
    symbol: str; tier: str; direction: str
    price: float; ema20: float; sma50: float; rsi14: float
    bb_upper: float; bb_lower: float; pct5d: float
    reasons: list; confidence: str

def generate_signal(symbol: str, tier: str) -> Signal:
    closes = fetch_closes(symbol, 60)
    if len(closes) < 20:
        return Signal(symbol, tier, "NEUTRAL", 0,0,0,50,0,0,0, ["Insufficient data"], "LOW")

    px, e20, s50 = closes[-1], ema(closes,20), sma(closes,50)
    r14          = rsi_calc(closes, 14)
    bb_u, _, bb_l = bollinger(closes)
    p5d          = (closes[-1]-closes[-5])/closes[-5]*100 if len(closes) >= 5 else 0

    if tier == "HODL":
        d, rs, pts = "HOLD", [], 0
        if px <= e20 * 1.015: d, pts = "ACCUMULATE", 2; rs.append(f"At EMA20 ${e20:.2f}")
        elif px <= s50 * 1.015: d, pts = "ACCUMULATE", 1; rs.append(f"At SMA50 ${s50:.2f}")
        conf = "HIGH" if pts >= 2 else "MED" if pts else "LOW"
        return Signal(symbol, tier, d, round(px,2), round(e20,2), round(s50,2),
                      round(r14,1), round(bb_u,2), round(bb_l,2), round(p5d,2),
                      rs or ["No accumulation zone"], conf)

    cp, pp, cr, pr = 0, 0, [], []
    if e20 > s50: cp += 1; cr.append(f"EMA20 {e20:.0f} > SMA50 {s50:.0f}")
    else:         pp += 1; pr.append(f"EMA20 {e20:.0f} < SMA50 {s50:.0f}")
    if abs(px-bb_l)/px < 0.02: cp += 2; cr.append(f"BB lower bounce ${bb_l:.2f}")
    if abs(px-bb_u)/px < 0.02: pp += 2; pr.append(f"BB upper rejection ${bb_u:.2f}")
    if 45 < r14 < 65: cp += 1; cr.append(f"RSI {r14:.1f} bullish zone")
    if 58 < r14 < 78: pp += 1; pr.append(f"RSI {r14:.1f} extended")
    if p5d > 0.4:  cp += 1; cr.append(f"+{p5d:.1f}%/5d momentum")
    if p5d < -0.4: pp += 1; pr.append(f"{p5d:.1f}%/5d pressure")

    need = 4 if tier == "SANDBOX" else 3
    if cp >= need and cp >= pp:   d, pts, rs = "CALL", cp, cr
    elif pp >= need and pp > cp:  d, pts, rs = "PUT", pp, pr
    else:                          d, pts, rs = "NEUTRAL", 0, ["No clear edge"]

    conf = "HIGH" if pts >= 5 else "MED" if pts >= 3 else "LOW"
    return Signal(symbol, tier, d, round(px,2), round(e20,2), round(s50,2),
                  round(r14,1), round(bb_u,2), round(bb_l,2), round(p5d,2), rs, conf)


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION SELECTOR  (+ vertical debit spread compressor)
# ═══════════════════════════════════════════════════════════════════════════════

def find_option(chain: list, signal: Signal, rules: dict,
                min_dte_override: Optional[int] = None) -> Optional[dict]:
    today    = date.today()
    opt_type = "C" if signal.direction == "CALL" else "P"
    min_dte  = max(rules.get("min_dte", 4), min_dte_override or 0)
    min_p    = rules.get("min_premium", 0.05)
    max_p    = rules.get("max_premium", 99.0)
    px       = signal.price

    out = []
    for expiry in chain:
        try:
            exp = datetime.strptime(expiry.get("expiration-date",""), "%Y-%m-%d").date()
        except ValueError:
            continue
        dte = (exp - today).days
        if dte < min_dte:
            continue
        for sd in expiry.get("strikes", []):
            strike = float(sd.get("strike-price", 0))
            lo, hi = (0.95, 1.10) if opt_type == "C" else (0.90, 1.05)
            if not (px*lo <= strike <= px*hi):
                continue
            leg   = sd.get("call" if opt_type == "C" else "put", {})
            bid   = float(leg.get("bid", 0) or 0)
            ask   = float(leg.get("ask", 0) or 0)
            mid   = round((bid+ask)/2, 2)
            delta = abs(float(leg.get("delta", 0) or 0))
            sym   = leg.get("symbol", "")
            if not sym or not (min_p <= mid <= max_p):
                continue
            out.append({"symbol": sym, "strike": strike, "dte": dte,
                        "delta": delta, "bid": bid, "ask": ask, "mid": mid})
    if not out:
        return None
    return min(out, key=lambda x: abs(x["delta"] - 0.35))


def build_spread(chain: list, signal: Signal, rules: dict) -> Optional[dict]:
    """
    Vertical Debit Spread compressor — when an institutional alpha contract is
    too expensive, programmatically compress entry cost under the risk ceiling.
    """
    long_leg = find_option(chain, signal, {**rules, "max_premium": 99.0})
    if not long_leg:
        return None
    width  = 2.0
    target = long_leg["strike"] + width if signal.direction == "CALL" else long_leg["strike"] - width
    key    = "call" if signal.direction == "CALL" else "put"

    for expiry in chain:
        if expiry.get("expiration-date","") == "":
            continue
        for sd in expiry.get("strikes", []):
            if float(sd.get("strike-price", 0)) != target:
                continue
            leg = sd.get(key, {})
            sym = leg.get("symbol", "")
            bid = float(leg.get("bid", 0) or 0)
            ask = float(leg.get("ask", 0) or 0)
            if not sym or sym.split()[0] != long_leg["symbol"].split()[0]:
                continue
            mid = round((bid+ask)/2, 2)
            return {
                "long_leg":  long_leg,
                "short_leg": {"symbol": sym, "strike": target, "mid": mid},
                "net_debit": round(long_leg["mid"] - mid, 2),
                "max_profit": round(width - (long_leg["mid"] - mid), 2),
                "dte": long_leg["dte"],
            }
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# TRADE RECORD
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OpenTrade:
    account: str; symbol: str; option_symbol: str; direction: str
    entry: float; quantity: int; qty_remaining: int
    target: float; stop: float; dte: int
    runner_fired: bool = False
    entry_time: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN BOT
# ═══════════════════════════════════════════════════════════════════════════════

class JECIOptionsBot:
    def __init__(self):
        self.tt        = TastytradeSession()
        self.state_eng = MarketStateEngine("SPY")
        self.consensus = ConsensusEngine()
        self.trades: dict[str, OpenTrade] = {}
        self.stopped_out_today: set[str] = set()    # averaging-down / revenge-trade ban
        self._blocklist_day: date = date.today()

    # ── lifecycle ─────────────────────────────────────────────────────────────
    def start(self):
        online = self.consensus.agents_online()
        for line in [
            "═"*66,
            "  JECI OPTIONS BOT v2 · State Engine + Tri-Agent Consensus",
            f"  Mode: {'PAPER' if PAPER else '🔴 LIVE'}   Auto-execute: {AUTO_EXECUTE}   "
            f"Consensus required: {CONSENSUS_REQUIRED}",
            f"  Agents online — Grok: {online['grok']}  Claude: {online['claude']}  "
            f"DeepSeek: {online['deepseek']}",
            f"  Sandbox cap: ${SANDBOX_RULES['max_premium_dollars']:.0f}/trade · "
            f"4DTE min · spreads on SPY/XSP",
            f"  Core position cap: {CORE_RULES['max_position_pct']}% net liq",
            "═"*66,
        ]:
            log.info(line)

        if CONSENSUS_REQUIRED and not all(online.values()):
            log.warning("⚠  CONSENSUS_REQUIRED=true but agents are offline — bot will "
                        "run in ALERT-ONLY mode for entries until all 3 keys are set.")

        if not self.tt.login():
            log.error("Aborting — login failed.")
            return

        self.scan_all()
        schedule.every(30).minutes.do(self.scan_all)
        while True:
            schedule.run_pending()
            time.sleep(30)

    def _market_open(self) -> bool:
        now = datetime.now()
        if now.weekday() >= 5: return False
        mins = now.hour*60 + now.minute
        return MARKET_OPEN_MIN <= mins <= MARKET_CLOSE_MIN

    def _reset_daily_blocklist(self):
        if date.today() != self._blocklist_day:
            self.stopped_out_today.clear()
            self._blocklist_day = date.today()

    # ── master scan ───────────────────────────────────────────────────────────
    def scan_all(self):
        if not self._market_open():
            log.info(f"🕐 Outside market hours ({datetime.now().strftime('%H:%M')})")
            return
        self._reset_daily_blocklist()

        # ── STEP 1: detect market state ───────────────────────────────────────
        report = self.state_eng.detect()
        log.info(f"\n{'─'*58}")
        log.info(f"🌐 MARKET STATE: {report.state.value}  "
                 f"(gap {report.gap_pct:+.2f}% · RSI15 {report.rsi15} · "
                 f"{'above' if report.above_vwap else 'BELOW'} VWAP {report.vwap})")
        log.info(f"   {report.details}")

        # ── STEP 2: scan tiers under state locks ──────────────────────────────
        for sym in CORE_WATCHLIST:
            self._handle("CORE", sym, report)
        for sym in SANDBOX_WATCHLIST:
            self._handle("SANDBOX", sym, report)
        for sym in sum(HODL_WATCHLIST.values(), []):
            try:
                sig = generate_signal(sym, "HODL")
                if sig.direction == "ACCUMULATE":
                    log.info(f"  🏛  HODL ALERT {sym:6s} ${sig.price}  "
                             f"{' | '.join(sig.reasons)} [{sig.confidence}]")
            except Exception as e:
                log.error(f"  HODL {sym}: {e}")

    def _handle(self, tier: str, sym: str, report):
        key = f"{tier}:{sym}"
        try:
            if key in self.trades:
                self._check_exit(key, report)
            else:
                if sym in self.stopped_out_today:
                    return   # averaging-down / revenge-entry ban for the day
                need = "HIGH" if tier == "SANDBOX" else ("MED", "HIGH")
                sig  = generate_signal(sym, tier)
                self._log_signal(sig)
                ok_conf = sig.confidence == need if isinstance(need, str) else sig.confidence in need
                if sig.direction in ("CALL","PUT") and ok_conf:
                    self._attempt_entry(tier, sig, report)
        except Exception as e:
            log.error(f"  {tier} {sym}: {e}")

    def _log_signal(self, s: Signal):
        arrow = {"CALL":"↑ CALL","PUT":"↓ PUT"}.get(s.direction, "  ----")
        log.info(f"  [{s.tier[:2]}] {s.symbol:6s} ${s.price:>8.2f}  RSI {s.rsi14:5.1f}  "
                 f"{arrow} [{s.confidence}]  {' · '.join(s.reasons[:2])}")

    # ── entry pipeline: signal → option → moat → consensus → execute ─────────
    def _attempt_entry(self, tier: str, sig: Signal, report):
        acct = self.tt.accounts.get(tier)
        if not acct:
            return
        rules    = SANDBOX_RULES if tier == "SANDBOX" else CORE_RULES
        net_liq  = self.tt.get_balance(acct)
        chain    = self.tt.get_option_chain(sig.symbol)
        dte_override = (report.locks or {}).get("min_dte_override")

        # Index symbols on Sandbox → spread compressor path
        is_spread = tier == "SANDBOX" and sig.symbol in rules.get("use_spreads_on", [])
        if is_spread:
            sp = build_spread(chain, sig, rules)
            if not sp:
                return
            entry_px, opt_sym, dte = sp["net_debit"], sp["long_leg"]["symbol"], sp["dte"]
        else:
            opt = find_option(chain, sig, rules, dte_override)
            if not opt:
                log.warning(f"  No suitable option for {sig.symbol} ({tier})")
                return
            # Spread compressor fallback: alpha contract too rich for the ceiling
            if tier == "SANDBOX" and opt["mid"] > rules["max_premium"]:
                sp = build_spread(chain, sig, rules)
                if sp and sp["net_debit"] <= rules["max_premium"]:
                    log.info(f"  🛡  Premium ${opt['mid']:.2f} too rich — compressed to "
                             f"spread, net debit ${sp['net_debit']:.2f}")
                    is_spread = True
                    entry_px, opt_sym, dte = sp["net_debit"], sp["long_leg"]["symbol"], sp["dte"]
                else:
                    log.warning(f"  Premium ${opt['mid']:.2f} > ${rules['max_premium']:.2f} "
                                f"cap and no viable spread — skip")
                    return
            else:
                entry_px, opt_sym, dte = opt["mid"], opt["symbol"], opt["dte"]

        # ── position sizing under tier caps ───────────────────────────────────
        if tier == "SANDBOX":
            cap = min(net_liq * rules["max_alloc_pct"]/100, rules["max_premium_dollars"])
        else:
            cap = net_liq * rules["max_position_pct"]/100
        qty = max(1, int(cap / (entry_px * 100)))
        if entry_px * 100 * qty > cap and qty == 1 and tier == "SANDBOX":
            log.warning(f"  Even 1 contract (${entry_px*100:.0f}) exceeds "
                        f"${cap:.0f} cap — skip")
            return

        # -- LEVI Sub-Agent Pre-Consensus Layer --------------------------------
        scout_out = SCOUT.scan(sig.symbol)
        atlas_out = ATLAS.analyze(sig.symbol)
        lens_out  = LENS.analyze(sig.symbol, sig.direction)
        # -- LAYER 0+1+2: Risk Moat -> SCOUT/ATLAS/LENS -> Tri-Agent Consensus -
        rsi15 = fetch_rsi15(sig.symbol)
        proposal = TradeProposal(
            account_tier=tier, symbol=sig.symbol, direction=sig.direction,
            option_symbol=opt_sym, strike=0.0, dte=dte,
            premium=entry_px, quantity=qty, net_liq=net_liq,
            rsi15=rsi15, market_state=report.state.value,
            state_locks=report.locks,
        )
        metrics = {"price": sig.price, "ema20": sig.ema20, "sma50": sig.sma50,
                   "rsi14_daily": sig.rsi14, "rsi15_intraday": rsi15,
                   "bb_upper": sig.bb_upper, "bb_lower": sig.bb_lower,
                   "pct_5d": sig.pct5d, "market_state": report.state.value,
                   "local_signal": sig.direction, "confidence": sig.confidence,
                   "x_sentiment":    scout_out["sentiment"],
                   "x_confidence":   scout_out["confidence"],
                   "x_signals":      scout_out["key_signals"],
                   "macro_regime":   atlas_out["macro_regime"],
                   "macro_bias":     atlas_out["trade_bias"],
                   "catalysts":      atlas_out["catalysts_ahead"],
                   "setup_quality":  lens_out["setup_quality"],
                   "lens_confidence":lens_out["confidence"],
                   "trace_triggered":lens_out["trace_triggered"]}

        if CONSENSUS_REQUIRED:
            result = self.consensus.evaluate(proposal, metrics)
            for n in result.notes:
                log.info(f"    {n}")
            if not result.approved:
                log.info(f"  ⛔ Consensus {result.votes} — {sig.symbol} {sig.direction} "
                         f"NOT routed")
                return
        else:
            ok, fails = RiskMoat.validate(proposal)   # moat always runs, even solo
            if not ok:
                for f in fails: log.info(f"    ⛔ {f}")
                return

        # ── execute ───────────────────────────────────────────────────────────
        log.info(f"  🎯 {tier} {sig.direction} {opt_sym}  DTE {dte}  "
                 f"${entry_px:.2f} x{qty}  (total ${entry_px*100*qty:.0f})")
        if not self._confirm(f"Execute {tier} {sig.direction} x{qty} {opt_sym} "
                             f"@ ${entry_px:.2f}"):
            return

        lim = round(entry_px * 1.02, 2)
        if is_spread:
            self.tt.place_order(acct, sp["long_leg"]["symbol"], qty, "Buy to Open",
                                round(sp["long_leg"]["mid"]*1.02, 2))
            self.tt.place_order(acct, sp["short_leg"]["symbol"], qty, "Sell to Open",
                                round(sp["short_leg"]["mid"]*0.98, 2))
        else:
            self.tt.place_order(acct, opt_sym, qty, "Buy to Open", lim)

        rules_pt = rules["profit_target"]; rules_sl = rules["stop_loss_pct"]
        self.trades[f"{tier}:{sig.symbol}"] = OpenTrade(
            account=acct, symbol=sig.symbol, option_symbol=opt_sym,
            direction=sig.direction, entry=entry_px, quantity=qty,
            qty_remaining=qty, dte=dte,
            target=round(entry_px*(1+rules_pt), 2),
            stop=round(entry_px*(1-rules_sl), 2),
            entry_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        log.info(f"  ✅ Opened · Target ${entry_px*(1+rules_pt):.2f} · "
                 f"Stop ${entry_px*(1-rules_sl):.2f}")

    # ── exit pipeline: runner → patience matrix → target/stop/dead-weight ────
    def _check_exit(self, key: str, report):
        trade = self.trades[key]
        tier  = key.split(":")[0]
        rules = CORE_RULES if tier == "CORE" else SANDBOX_RULES
        try:
            q   = self.tt.get_quote(trade.option_symbol)
            bid = float(q.get("bid", 0) or 0); ask = float(q.get("ask", 0) or 0)
            mid = (bid+ask)/2 if (bid and ask) else 0
            if mid <= 0: return
            pnl = (mid - trade.entry)/trade.entry*100

            # ── Runner Mechanic: harvest half at +100%, stop → breakeven ─────
            if (pnl >= rules["runner_trigger"]*100 and not trade.runner_fired
                    and trade.qty_remaining > 1):
                h = trade.qty_remaining // 2
                log.info(f"  🏃 RUNNER {trade.symbol} +{pnl:.0f}% — harvesting {h}, "
                         f"keeping {trade.qty_remaining-h} risk-free")
                self.tt.place_order(trade.account, trade.option_symbol, h,
                                    "Sell to Close", round(mid*0.98, 2))
                trade.qty_remaining -= h
                trade.runner_fired   = True
                trade.stop           = trade.entry

            hit_t = mid >= trade.target
            hit_s = mid <= trade.stop
            dead  = tier == "CORE" and mid <= trade.entry*0.01

            # ── Patience Matrix: in flush/recovery, DTE>=60 stops become alerts ─
            patience = (report.locks or {}).get("patience_matrix") or \
                       report.state in (MarketState.WATERFALL, MarketState.V_BOTTOM)
            if hit_s and patience and trade.dte >= 60 and not dead:
                log.info(f"  🧘 PATIENCE MATRIX [{report.state.value}] — {trade.symbol} "
                         f"DTE {trade.dte} at stop level (P&L {pnl:+.1f}%) but holding. "
                         f"Long-dated structure rides the recovery.")
                return

            log.info(f"  [{tier[:2]}] {trade.symbol:6s} OPEN  ${trade.entry:.2f}→${mid:.2f} "
                     f"P&L {pnl:+.1f}%  rem {trade.qty_remaining}")

            if hit_t or hit_s or dead:
                tag = "TARGET ✅" if hit_t else "DEAD WEIGHT 🗑" if dead else "STOP 🛑"
                log.info(f"  {tag} — closing {trade.qty_remaining}x {trade.option_symbol}")
                self.tt.place_order(trade.account, trade.option_symbol,
                                    trade.qty_remaining, "Sell to Close",
                                    round(mid*0.98, 2))
                if hit_s or dead:
                    self.stopped_out_today.add(trade.symbol)   # no averaging down today
                    log.info(f"  🚫 {trade.symbol} blocklisted for re-entry today "
                             f"(no revenge trades, no averaging down)")
                del self.trades[key]
        except Exception as e:
            log.error(f"  Exit check ({key}): {e}")

    def _confirm(self, prompt: str) -> bool:
        if AUTO_EXECUTE:
            return True
        try:
            return input(f"\n  {prompt} (y/n): ").strip().lower() == "y"
        except EOFError:
            return False


if __name__ == "__main__":
    JECIOptionsBot().start()
