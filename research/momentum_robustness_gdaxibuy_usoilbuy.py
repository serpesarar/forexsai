"""
RESEARCH ONLY — failure-hunting robustness battery for GDAXI:BUY & USOIL:BUY
before wiring them into the live backend gate.

Tests designed to BREAK the edge if it's an artifact:
  (A) Tie-break sensitivity: re-resolve every trade with pessimistic (ambiguous
      bar -> LOSS) and optimistic (-> WIN) rules, vs the OHLC heuristic. Also
      count how many resolutions were ambiguous (exposure to the heuristic).
  (B) Bootstrap 95% CI on filtered TEST WR (2000 resamples) vs breakeven.
  (C) Placebo: momentum filter vs 2000 random same-size subsets of the TEST
      universe (per-LOG). Report the percentile the momentum WR lands at.

Controls GDAXI:SELL & USOIL:SELL (already live) included for reference.
Touches nothing. Pure read + compute.
"""
import sys, bisect, random
from datetime import datetime, timedelta, timezone
from collections import defaultdict

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client
from bot_fixed_tpsl_replay import MODELS, parse_iso, load_bars, _fnum

random.seed(1234)
PAGE = 1000
SINCE = "2026-04-25T00:00:00+00:00"
SPLIT = "2026-05-27T00:00:00+00:00"
MAX_HOLD_MIN = 1440

SCOPES = {
    "GDAXI.INDX:BUY":   {"tp": 67.0,  "sl": 119.0, "is_pct": False, "sfx": "M15", "fric": 1.5},
    "USOIL.FOREX:BUY":  {"tp": 1.04,  "sl": 1.49,  "is_pct": True,  "sfx": "M30", "fric": 0.03},
    "GDAXI.INDX:SELL":  {"tp": 67.0,  "sl": 119.0, "is_pct": False, "sfx": "M15", "fric": 1.5},  # ctrl
    "USOIL.FOREX:SELL": {"tp": 1.04,  "sl": 1.49,  "is_pct": True,  "sfx": "M30", "fric": 0.03}, # ctrl
}


def momo_pass(direction, sfx, f):
    g = lambda k: _fnum(f.get(k))
    sar = g("H1_sar_dist_atr")
    if direction == "BUY":
        sk = g(f"{sfx}_stoch_k"); de = g(f"{sfx}_dist_ema20_atr")
        if None in (sk, de, sar): return None
        return (sk > 70) and (de > 0.8) and (sar > 0)
    de = g(f"{sfx}_dist_ema20_atr"); mh = g(f"{sfx}_macd_hist")
    if None in (de, mh, sar): return None
    return (de < 0) and (mh < 0) and (sar < 0)


def load_signals(c, symbol, direction):
    out = []; off = 0
    while True:
        r = (c.table("prediction_logs").select("created_at,factors")
             .eq("symbol", symbol).eq("ml_direction", direction).in_("model_type", MODELS)
             .gte("created_at", SINCE).order("created_at", desc=False)
             .range(off, off+PAGE-1).execute())
        page = r.get("data") if isinstance(r, dict) else getattr(r, "data", [])
        if not page: break
        out.extend(page)
        if len(page) < PAGE: break
        off += PAGE
    return out


def replay(entry_open, direction, tp, sl, is_pct, cin, bars, tsk, entry_ts, tie):
    """Return (res, exit_ts, ambiguous_bool). tie in {'heur','pess','opt'}."""
    s = 1 if direction == "BUY" else -1
    if is_pct:
        fill = entry_open * (1 + s*cin/100.0)
        tp_px = fill * (1 + s*tp/100.0); sl_px = fill * (1 - s*sl/100.0)
    else:
        fill = entry_open + s*cin
        tp_px = fill + s*tp; sl_px = fill - s*sl
    end_ts = entry_ts + timedelta(minutes=MAX_HOLD_MIN)
    lo = bisect.bisect_left(tsk, entry_ts)
    for i in range(lo, len(bars)):
        ts, o, h, l, cl = bars[i]
        if ts > end_ts: break
        if direction == "BUY":
            hit_tp = h >= tp_px; hit_sl = l <= sl_px
        else:
            hit_tp = l <= tp_px; hit_sl = h >= sl_px
        if hit_tp and hit_sl:
            if tie == "pess": return "LOSS", ts, True
            if tie == "opt":  return "WIN", ts, True
            bullish = cl >= o
            tp_first = (not bullish) if direction == "BUY" else bullish
            return ("WIN" if tp_first else "LOSS"), ts, True
        if hit_tp: return "WIN", ts, False
        if hit_sl: return "LOSS", ts, False
    return "OPEN", None, False


def dedup(cands, cooldown=30):
    trades = []; busy = None
    for cat, res, exit_ts, p in cands:
        if res is None or res == "OPEN": continue
        if busy is not None and cat < busy: continue
        trades.append((cat, res, p)); busy = (exit_ts or cat) + timedelta(minutes=cooldown)
    return trades


def be_fric(tp, sl, cout): return (sl+cout)/((tp-cout)+(sl+cout))
def wr_of(trades):
    n=len(trades); w=sum(1 for t in trades if t[1]=="WIN"); return (w/n if n else 0.0), n


def main():
    c = get_supabase_client()
    split_dt = parse_iso(SPLIT)
    for scope, lv in SCOPES.items():
        symbol, direction = scope.rsplit(":", 1)
        sfx = lv["sfx"]; tp=lv["tp"]; sl=lv["sl"]; ip=lv["is_pct"]; cin=lv["fric"]
        bars = load_bars(c, symbol); tsk=[b[0] for b in bars]
        sigs = load_signals(c, symbol, direction)
        be = be_fric(tp, sl, cin)

        prepped = []  # (cat, eo, pass, factors)
        for sgl in sigs:
            cat = parse_iso(sgl.get("created_at"))
            if cat is None: continue
            lo = bisect.bisect_left(tsk, cat)
            if lo >= len(bars): continue
            eo = bars[lo][1]
            if eo <= 0: continue
            f = sgl.get("factors") or {}
            prepped.append((cat, eo, momo_pass(direction, sfx, f), f))
        prepped.sort(key=lambda x: x[0])

        print(f"\n{'='*74}\n{scope}  tp{tp}/sl{sl}{'%' if ip else ''}  be@1x={be*100:.1f}%  "
              f"({len(prepped)} signals)")

        # ── (A) tie-break sensitivity on filtered TEST (per-trade dedup) ──
        def filtered_test_trades(tie):
            amb = 0; rows = []
            for cat, eo, p, f in prepped:
                if cat < split_dt: continue
                res, ex, a = replay(eo, direction, tp, sl, ip, cin, bars, tsk, cat, tie)
                if a: amb += 1
                rows.append((cat, res, ex, p))
            ft = dedup([r for r in rows if r[3] is True])
            return ft, amb
        for tie, label in (("heur","heuristic"),("pess","pessimistic→LOSS"),("opt","optimistic→WIN")):
            ft, amb = filtered_test_trades(tie)
            wr, n = wr_of(ft)
            print(f"  (A) {label:18s}: MOMO TEST n={n:3d} WR={wr*100:5.1f}% "
                  f"{'+EV' if wr>be else '-EV'}   (ambiguous bar resolutions in pool: {amb})")

        # heuristic filtered trades reused for bootstrap
        ft_heur, _ = filtered_test_trades("heur")
        results = [1 if t[1]=="WIN" else 0 for t in ft_heur]
        n = len(results)

        # ── (B) bootstrap 95% CI on filtered TEST WR ──
        if n > 0:
            boots = []
            for _ in range(2000):
                s = [results[random.randrange(n)] for _ in range(n)]
                boots.append(sum(s)/n)
            boots.sort()
            lo5 = boots[int(0.025*2000)]; hi95 = boots[int(0.975*2000)-1]; med = boots[1000]
            frac_above = sum(1 for b in boots if b > be)/2000
            print(f"  (B) bootstrap WR 95% CI = [{lo5*100:.1f}%, {hi95*100:.1f}%] median {med*100:.1f}% "
                  f"| P(WR>be) = {frac_above*100:.1f}%   (be={be*100:.1f}%)")
        else:
            print("  (B) bootstrap: n=0")

        # ── (C) placebo: momentum vs random same-size subset (per-LOG TEST) ──
        # per-LOG universe: every resolved test log under heuristic
        univ = []  # (res, passed)
        for cat, eo, p, f in prepped:
            if cat < split_dt: continue
            res, ex, a = replay(eo, direction, tp, sl, ip, cin, bars, tsk, cat, "heur")
            if res in ("WIN","LOSS"):
                univ.append((1 if res=="WIN" else 0, p))
        momo_logs = [u[0] for u in univ if u[1] is True]
        k = len(momo_logs); N = len(univ)
        if k > 0 and N > k:
            momo_wr = sum(momo_logs)/k
            pool = [u[0] for u in univ]
            ge = 0
            for _ in range(2000):
                samp = random.sample(pool, k)
                if sum(samp)/k >= momo_wr: ge += 1
            pct = (1 - ge/2000)*100
            print(f"  (C) placebo per-LOG: momentum k={k}/{N} WR={momo_wr*100:.1f}% "
                  f"vs random same-size → momentum beats {pct:.1f}% of random draws "
                  f"(p={ge/2000:.3f})")
        else:
            print(f"  (C) placebo: k={k} N={N} — insufficient")


if __name__ == "__main__":
    main()
