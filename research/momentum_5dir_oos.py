"""
RESEARCH ONLY — OOS battery for the 5 UNTESTED bot directions.

The bot only trades 3 scopes (NDX:BUY, GDAXI:SELL, USOIL:SELL). This runs the
same honest battery (A temporal TRAIN/TEST, B weekly walk-forward, C blind
thresholds) on the 5 directions the bot has never traded, to see whether ANY of
them carries a momentum-continuation edge against a bot-style FIXED tp/sl.

tp/sl choice (NOT cherry-picked):
  - opposite-direction scopes reuse their SYMBOL's fixed tp/sl (symmetric
    point/pct distance the bot already uses for the validated direction)
  - XAUUSD has no walk-forward tp/sl → use the live target_config ladder
    TP1=8 / SL=15 ($-based). NOTE be = 15/23 = 65.2% — a hard bar.

Momentum filter templates (same structure that survived OOS on the 3 traded scopes):
  BUY  continuation:  {sfx}_stoch_k>70 & {sfx}_dist_ema20_atr>0.8 & H1_sar_dist_atr>0
  SELL continuation:  {sfx}_dist_ema20_atr<0 & {sfx}_macd_hist<0 & H1_sar_dist_atr<0
  sfx = M15 (NDX/GDAXI) or M30 (USOIL/XAUUSD).

Touches nothing. Pure read + compute.
"""
import sys, bisect
from datetime import datetime, timedelta, timezone
from collections import defaultdict

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client

from bot_fixed_tpsl_replay import (
    MODELS, parse_iso, load_bars, replay_fixed, ev_per_trade, _fnum,
)

PAGE = 1000
SINCE = "2026-04-25T00:00:00+00:00"
SPLIT = "2026-05-27T00:00:00+00:00"

# scope -> tp/sl + the timeframe suffix that holds its momentum factors
NEW_SCOPES = {
    "NDX.INDX:SELL":    {"tp": 80.0,  "sl": 110.0, "is_pct": False, "sfx": "M15"},
    "GDAXI.INDX:BUY":   {"tp": 67.0,  "sl": 119.0, "is_pct": False, "sfx": "M15"},
    "USOIL.FOREX:BUY":  {"tp": 1.04,  "sl": 1.49,  "is_pct": True,  "sfx": "M30"},
    "XAUUSD:BUY":       {"tp": 8.0,   "sl": 15.0,  "is_pct": False, "sfx": "M30"},
    "XAUUSD:SELL":      {"tp": 8.0,   "sl": 15.0,  "is_pct": False, "sfx": "M30"},
}


def momo_pass(direction, sfx, f):
    """Fixed-threshold momentum-continuation filter (same shape as the 3 validated)."""
    g = lambda k: _fnum(f.get(k))
    sar = g("H1_sar_dist_atr")
    if direction == "BUY":
        sk = g(f"{sfx}_stoch_k"); de = g(f"{sfx}_dist_ema20_atr")
        if None in (sk, de, sar): return None
        return (sk > 70) and (de > 0.8) and (sar > 0)
    else:
        de = g(f"{sfx}_dist_ema20_atr"); mh = g(f"{sfx}_macd_hist")
        if None in (de, mh, sar): return None
        return (de < 0) and (mh < 0) and (sar < 0)


def blind_keys(direction, sfx):
    if direction == "BUY":
        return [(f"{sfx}_stoch_k", ">"), (f"{sfx}_dist_ema20_atr", ">"), ("H1_sar_dist_atr", ">")]
    return [(f"{sfx}_dist_ema20_atr", "<"), (f"{sfx}_macd_hist", "<"), ("H1_sar_dist_atr", "<")]


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


def dedup(cands, cooldown=30):
    trades = []; busy = None
    for cat, res, exit_ts, p in cands:
        if res is None or res == "OPEN": continue
        if busy is not None and cat < busy: continue
        trades.append((cat, res, p))
        busy = (exit_ts or cat) + timedelta(minutes=cooldown)
    return trades


def wr_ev(trades, lv):
    n = len(trades); w = sum(1 for t in trades if t[1] == "WIN")
    wr = w/n if n else 0; be = lv["sl"]/(lv["tp"]+lv["sl"])
    return n, wr, be, ev_per_trade(wr, lv["tp"], lv["sl"])


def main():
    c = get_supabase_client()
    split_dt = parse_iso(SPLIT)
    for scope, lv in NEW_SCOPES.items():
        symbol, direction = scope.rsplit(":", 1)
        sfx = lv["sfx"]
        bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
        sigs = load_signals(c, symbol, direction)

        evald = []
        for s in sigs:
            cat = parse_iso(s.get("created_at"))
            if cat is None: continue
            lo = bisect.bisect_left(tsk, cat)
            if lo >= len(bars): continue
            entry = bars[lo][1]
            if entry <= 0: continue
            res, exit_ts = replay_fixed(cat, entry, direction, lv["tp"], lv["sl"],
                                        lv["is_pct"], bars, tsk)
            f = s.get("factors") or {}
            evald.append((cat, res, exit_ts, momo_pass(direction, sfx, f), f))
        evald.sort(key=lambda x: x[0])
        train = [e for e in evald if e[0] < split_dt]
        test = [e for e in evald if e[0] >= split_dt]

        be = lv["sl"]/(lv["tp"]+lv["sl"])
        print(f"\n{'='*72}\n{scope}  tp{lv['tp']}/sl{lv['sl']}{'%' if lv['is_pct'] else ''}  "
              f"be={be*100:.1f}%  ({len(bars)} bars, train n={len(train)}, test n={len(test)})")

        for tag, subset in (("TRAIN", train), ("TEST ", test)):
            allt = dedup([(e[0], e[1], e[2], e[3]) for e in subset])
            n, wr, _, ev = wr_ev(allt, lv)
            ft = dedup([(e[0], e[1], e[2], e[3]) for e in subset if e[3] is True])
            fn, fwr, _, fev = wr_ev(ft, lv)
            print(f"  (A) {tag}  UNFILT n={n:3d} WR={wr*100:5.1f}% EV={ev:+.3f}R   "
                  f"||  MOMO n={fn:3d} WR={fwr*100:5.1f}% EV={fev:+.3f}R "
                  f"{'+EV' if fwr>be else '-EV'}")

        # (C) blind thresholds from TRAIN wins
        wins_tr = [e for e in train if e[1] == "WIN"]
        bk = blind_keys(direction, sfx); thr = {}
        for k, side in bk:
            vals = sorted(v for v in (_fnum(e[4].get(k)) for e in wins_tr) if v is not None)
            thr[k] = vals[len(vals)//2] if vals else None
        def blind_pass(f):
            for k, side in bk:
                v = _fnum(f.get(k))
                if v is None or thr[k] is None: return None
                if side == ">" and not (v > thr[k]): return False
                if side == "<" and not (v < thr[k]): return False
            return True
        test_blind = dedup([(e[0], e[1], e[2], blind_pass(e[4])) for e in test
                            if blind_pass(e[4]) is True])
        n, wr, _, ev = wr_ev(test_blind, lv)
        thr_s = ", ".join(f"{k.split('_',1)[-1]}{s}{thr[k]:.2f}" if thr[k] is not None else f"{k}=NA"
                          for k, s in bk)
        print(f"  (C) BLIND [{thr_s}] → TEST: n={n:3d} WR={wr*100:5.1f}% EV={ev:+.3f}R "
              f"{'+EV' if wr>be else '-EV'}")

        # (B) weekly filtered (per-LOG)
        byw = defaultdict(lambda: [0, 0])
        for cat, res, _, p, f in evald:
            if res is None or res == "OPEN" or p is not True: continue
            wk = (cat - timedelta(days=cat.weekday())).strftime("%m-%d")
            byw[wk][0 if res == "WIN" else 1] += 1
        cells = []
        for wk in sorted(byw):
            w, l = byw[wk]; nn = w+l
            if nn < 8: continue
            wr = w/nn*100
            cells.append(f"{wk}:{wr:.0f}%(n={nn}){'+' if wr/100>be else '-'}")
        print(f"  (B) weekly filtered WR vs be {be*100:.0f}%: " + ("  ".join(cells) if cells else "(no week ≥8 filtered logs)"))


if __name__ == "__main__":
    main()
