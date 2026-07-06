"""
RESEARCH ONLY — definitive OOS validation of the momentum-continuation filter.

The in-sample test derived thresholds AND measured WR on the same window. This
script does the honest tests:
  (A) Temporal split: TRAIN (first ~30d) vs TEST (held-out last ~15d). The filter
      thresholds are FIXED (set from the full-window discrimination), so TEST is
      data the thresholds' WR was never tuned on. Report per-trade WR/EV on each.
  (B) Weekly walk-forward: per-week filtered WR vs breakeven (per-LOG for n).
  (C) Re-derive thresholds on TRAIN ONLY (median split of each indicator on
      TRAIN wins vs losses) and apply to TEST — fully blind threshold test.

Reuses the replay machinery from bot_fixed_tpsl_replay.py. Touches nothing.
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
    SCOPES, MODELS, parse_iso, load_bars, replay_fixed, ev_per_trade,
    passes_filter, _fnum,
)

PAGE = 1000
SINCE = "2026-04-25T00:00:00+00:00"
SPLIT = "2026-05-27T00:00:00+00:00"   # train < SPLIT <= test  (~32d train / ~15d test)


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
        if res is None or res == "OPEN": continue   # unresolved is NOT a trade entry
        if busy is not None and cat < busy: continue
        trades.append((cat, res, p))
        busy = (exit_ts or cat) + timedelta(minutes=cooldown)
    return trades


def wr_ev(trades, lv):
    n = len(trades); w = sum(1 for t in trades if t[1] == "WIN")
    wr = w/n if n else 0; be = lv["sl"]/(lv["tp"]+lv["sl"])
    return n, wr, be, ev_per_trade(wr, lv["tp"], lv["sl"])


# ── (C) blind threshold derivation on TRAIN, with direction from discrimination ─
# Each tuple: (key, side) where side '>' means WIN-higher (gate keeps value>thr),
# '<' means WIN-lower (gate keeps value<thr). thr = median of TRAIN WINs.
BLIND_KEYS = {
    "NDX.INDX:BUY":     [("M15_stoch_k", ">"), ("M15_dist_ema20_atr", ">"), ("H1_sar_dist_atr", ">")],
    "GDAXI.INDX:SELL":  [("M15_dist_ema200_atr", "<"), ("H4_macd_hist", "<"), ("M15_adx_14", "<")],
    "USOIL.FOREX:SELL": [("M30_dist_ema20_atr", "<"), ("M30_macd_hist", "<"), ("H1_sar_dist_atr", "<")],
}


def main():
    c = get_supabase_client()
    for scope, lv in SCOPES.items():
        symbol, direction = scope.split(":")
        bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
        sigs = load_signals(c, symbol, direction)
        split_dt = parse_iso(SPLIT)

        # evaluate every signal once
        evald = []  # (cat, res, exit_ts, passed_fixedfilter, factors)
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
            evald.append((cat, res, exit_ts, passes_filter(scope, f), f))
        evald.sort(key=lambda x: x[0])
        train = [e for e in evald if e[0] < split_dt]
        test = [e for e in evald if e[0] >= split_dt]

        print(f"\n{'='*72}\n{scope}  tp{lv['tp']}/sl{lv['sl']}  "
              f"(train n={len(train)}, test n={len(test)}, split {SPLIT[:10]})")

        # ── (A) Fixed-threshold filter: TRAIN vs TEST per-trade ──
        for tag, subset in (("TRAIN", train), ("TEST ", test)):
            allt = dedup([(e[0], e[1], e[2], e[3]) for e in subset])
            n, wr, be, ev = wr_ev(allt, lv)
            ft = dedup([(e[0], e[1], e[2], e[3]) for e in subset if e[3] is True])
            fn, fwr, _, fev = wr_ev(ft, lv)
            print(f"  (A) {tag}  UNFILT n={n:3d} WR={wr*100:5.1f}% EV={ev:+.3f}R   "
                  f"||  MOMO n={fn:3d} WR={fwr*100:5.1f}% EV={fev:+.3f}R "
                  f"{'+EV' if fwr>be else '-EV'} (be={be*100:.1f}%)")

        # ── (C) Blind: derive thresholds (median of TRAIN wins) then apply to TEST ─
        wins_tr = [e for e in train if e[1] == "WIN"]
        thr = {}
        for k, side in BLIND_KEYS[scope]:
            vals = sorted(v for v in (_fnum(e[4].get(k)) for e in wins_tr) if v is not None)
            thr[k] = vals[len(vals)//2] if vals else None
        def blind_pass(f):
            for k, side in BLIND_KEYS[scope]:
                v = _fnum(f.get(k))
                if v is None or thr[k] is None: return None
                if side == ">" and not (v > thr[k]): return False
                if side == "<" and not (v < thr[k]): return False
            return True
        test_blind = dedup([(e[0], e[1], e[2], blind_pass(e[4])) for e in test
                            if blind_pass(e[4]) is True])
        n, wr, be, ev = wr_ev(test_blind, lv)
        thr_s = ", ".join(f"{k.split('_',1)[-1]}{s}{thr[k]:.2f}" if thr[k] is not None else f"{k}=NA"
                          for k, s in BLIND_KEYS[scope])
        print(f"  (C) BLIND thresholds from TRAIN [{thr_s}]")
        print(f"      → applied to TEST: n={n:3d} WR={wr*100:5.1f}% EV={ev:+.3f}R "
              f"{'+EV' if wr>be else '-EV'} (be={be*100:.1f}%)")

        # ── (B) Weekly walk-forward (per-LOG, filtered) ──
        byw = defaultdict(lambda: [0, 0])  # wk -> [win, loss] among filtered logs
        for cat, res, _, p, f in evald:
            if res is None or res == "OPEN" or p is not True: continue
            wk = (cat - timedelta(days=cat.weekday())).strftime("%m-%d")
            byw[wk][0 if res == "WIN" else 1] += 1
        be = lv["sl"]/(lv["tp"]+lv["sl"])
        cells = []
        for wk in sorted(byw):
            w, l = byw[wk]; n = w+l
            if n < 8: continue
            wr = w/n*100
            cells.append(f"{wk}:{wr:.0f}%(n={n}){'+' if wr/100>be else '-'}")
        print(f"  (B) weekly filtered WR vs be {be*100:.0f}%: " + "  ".join(cells))


if __name__ == "__main__":
    main()
