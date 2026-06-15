"""
RESEARCH ONLY — certification attempt for the SELL resistance-rejection edge.

The per-LOG separation is strong & consistent, but per-LOG overcounts correlated
duplicate logs of the same trade. The binding question is the DEDUPED (real-trade)
sample, which is thin per split. Here we use the LONGEST test window (split 05-20),
collect deduped rejection trades across NDX/USOIL/GDAXI SELL with each symbol's
TRAIN-derived tp/sl, convert outcomes to R-units (win=+tp/sl R after friction,
loss=-1R), POOL across symbols, and bootstrap P(mean R > 0).

Pooling in R is legitimate because R normalizes the different tp/sl per symbol.
Touches no production file.
"""
import sys, bisect, random, statistics as st
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client
from bot_fixed_tpsl_replay import MODELS, parse_iso, load_bars, _fnum, load_signals
from sell_resistance_reaction import (rejection_pass, quantile, excursion_pct,
                                      replay_pct_sell, dedup, FRIC_PCT)

random.seed(7)
SINCE = "2026-04-25T00:00:00+00:00"
SPLIT = "2026-05-20T00:00:00+00:00"   # longest held-out window
SCOPES = ["NDX.INDX:SELL", "USOIL.FOREX:SELL", "GDAXI.INDX:SELL"]


def main():
    c = get_supabase_client()
    split_dt = parse_iso(SPLIT)
    pooled_R = []           # per deduped trade, in R-units (friction-adjusted)
    per_symbol = {}
    for scope in SCOPES:
        symbol, direction = scope.rsplit(":", 1)
        bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
        sigs = load_signals(c, symbol, direction, SINCE)
        fric = FRIC_PCT[scope]

        prepped = []
        for s in sigs:
            cat = parse_iso(s.get("created_at"))
            if cat is None: continue
            lo = bisect.bisect_left(tsk, cat)
            if lo >= len(bars): continue
            entry = bars[lo][1]
            if entry <= 0: continue
            prepped.append((cat, entry, s.get("factors") or {}))
        prepped.sort(key=lambda x: x[0])
        train = [p for p in prepped if p[0] < split_dt]
        test  = [p for p in prepped if p[0] >= split_dt]

        tr_q33 = quantile([_fnum(p[2].get("H4_dist_swing_high_30_atr")) for p in train
                           if _fnum(p[2].get("H4_dist_swing_high_30_atr")) is not None], 0.33)
        mfes = []; maes = []
        for cat, entry, f in train:
            if rejection_pass(f, tr_q33) is not True: continue
            mfe, mae = excursion_pct(cat, entry, bars, tsk)
            if mfe is not None: mfes.append(mfe); maes.append(mae)
        tp_pct = st.median(mfes); sl_pct = quantile(maes, 0.70)

        rej_cands = []
        for cat, entry, f in test:
            if rejection_pass(f, tr_q33) is not True: continue
            res, ex = replay_pct_sell(cat, entry, tp_pct, sl_pct, bars, tsk)
            rej_cands.append((cat, res, ex))
        trades = dedup(rej_cands)
        win_R = (tp_pct - fric) / (sl_pct + fric)
        Rs = [win_R if r[1] == "WIN" else -1.0 for r in trades]
        pooled_R.extend(Rs)
        per_symbol[scope] = (len(Rs), st.mean(Rs) if Rs else 0.0, win_R, tp_pct, sl_pct)
        print(f"{scope:20s} deduped rej trades n={len(Rs):2d}  "
              f"TP={tp_pct:.3f}% SL={sl_pct:.3f}%  win={win_R:+.2f}R  "
              f"meanEV={st.mean(Rs) if Rs else 0:+.3f}R  trades={[r[1][0] for r in trades]}")

    n = len(pooled_R)
    print(f"\nPOOLED deduped rejection trades: n={n}  meanEV={st.mean(pooled_R):+.3f}R  "
          f"wins={sum(1 for x in pooled_R if x>0)}/{n}")
    if n >= 5:
        boots = []
        for _ in range(5000):
            s = [pooled_R[random.randrange(n)] for _ in range(n)]
            boots.append(sum(s)/n)
        boots.sort()
        lo = boots[int(0.025*5000)]; hi = boots[int(0.975*5000)-1]
        p_pos = sum(1 for b in boots if b > 0)/5000
        print(f"bootstrap 95% CI meanEV = [{lo:+.3f}R, {hi:+.3f}R]  P(EV>0) = {p_pos*100:.1f}%")
    else:
        print("pooled n too small for bootstrap")


if __name__ == "__main__":
    main()
