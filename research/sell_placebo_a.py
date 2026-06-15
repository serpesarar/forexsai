"""
RESEARCH ONLY — PLACEBO A (random-entry) for the SELL rejection edge.

The SELL v2 verdict (sell_rejection_v2.py) rested on a POOLED bootstrap
(P(EV>0)≈99.7% SWING / 99.9% CHAN) but never asked the geometry-vs-selection
question that just sank GDAXI:BUY CHAN: does the rejection FILTER actually pick
better entries, or does the favorable derived tp/sl make ANY SELL entry +EV?

Placebo A: for each scope, draw the SAME number of RANDOM entry timestamps from
the full test pool, replay with the SAME derived tp/sl, dedup, convert to R, POOL
across scopes (R normalizes per-scope tp/sl), and compare the pooled mean to the
observed (filtered) pooled mean. p = P(random pooled meanEV >= observed).

If p is small, the filter is genuinely selecting; if p is large (like GDAXI:BUY's
0.42), the edge is just R:R geometry and the filter adds nothing independent.

Run on the longest held-out window (split 05-20), both variants. No prod touch.
"""
import sys, bisect, random, statistics as st

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client
from bot_fixed_tpsl_replay import parse_iso, load_bars, _fnum, load_signals
from sell_resistance_reaction import (quantile, excursion_pct, replay_pct_sell,
                                      dedup, wr_of, be_fric, ev_fric, FRIC_PCT)
from sell_rejection_v2 import variant_pass, derive_thr, TP_PCTL, SL_PCTL, SCOPES

random.seed(11)
SINCE = "2026-04-25T00:00:00+00:00"
SPLIT = "2026-05-20T00:00:00+00:00"
NPLACEBO = 5000


def prep(c, scope):
    symbol, direction = scope.rsplit(":", 1)
    bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
    sigs = load_signals(c, symbol, direction, SINCE)
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
    return bars, tsk, prepped


def main():
    c = get_supabase_client()
    split_dt = parse_iso(SPLIT)

    for variant in ("SWING", "CHAN"):
        print(f"\n{'#'*84}\n# SELL PLACEBO A — variant {variant} (split {SPLIT[5:10]})\n{'#'*84}")
        per_scope = {}   # scope -> dict(test, tp, sl, fric, win_R, obs_R, rn)
        obs_pool = []
        for scope in SCOPES:
            bars, tsk, prepped = prep(c, scope)
            fric = FRIC_PCT[scope]
            train = [p for p in prepped if p[0] < split_dt]
            test  = [p for p in prepped if p[0] >= split_dt]
            thr = derive_thr(variant, train)

            mfes = []; maes = []
            for cat, entry, f in train:
                if not variant_pass(variant, f, thr): continue
                mfe, mae = excursion_pct(cat, entry, bars, tsk)
                if mfe is not None: mfes.append(mfe); maes.append(mae)
            if len(mfes) < 8:
                print(f"  {scope}: too few train reactions — skip"); continue
            tp = round(quantile(mfes, TP_PCTL), 3)
            sl = round(quantile(maes, SL_PCTL), 3)
            win_R = (tp - fric) / (sl + fric)

            rej_cands = []
            for cat, entry, f in test:
                if not variant_pass(variant, f, thr): continue
                res, ex = replay_pct_sell(cat, entry, tp, sl, bars, tsk)
                rej_cands.append((cat, res, ex))
            trades = dedup(rej_cands); rwr, rn = wr_of(trades)
            obs_R = [win_R if t[1] == "WIN" else -1.0 for t in trades]
            obs_pool.extend(obs_R)
            per_scope[scope] = dict(bars=bars, tsk=tsk, test=test, tp=tp, sl=sl,
                                    fric=fric, win_R=win_R, rn=rn)
            print(f"  {scope}: TP={tp}% SL={sl}% win {win_R:+.2f}R  "
                  f"obs reaction n={rn} WR={rwr*100:.1f}% meanEV={st.mean(obs_R) if obs_R else 0:+.3f}R")

        if not obs_pool:
            print("  no observed trades"); continue
        obs_mean = st.mean(obs_pool)
        n_obs = len(obs_pool)

        # pooled random-entry placebo
        ge = 0
        for _ in range(NPLACEBO):
            pool = []
            for scope, d in per_scope.items():
                test = d["test"]; rn = d["rn"]
                if rn == 0 or not test: continue
                idx = random.sample(range(len(test)), min(rn, len(test)))
                cands = []
                for i in idx:
                    cat, entry, f = test[i]
                    res, ex = replay_pct_sell(cat, entry, d["tp"], d["sl"], d["bars"], d["tsk"])
                    cands.append((cat, res, ex))
                tr = dedup(cands)
                pool.extend([d["win_R"] if t[1] == "WIN" else -1.0 for t in tr])
            if pool and (st.mean(pool) >= obs_mean):
                ge += 1
        p = ge / NPLACEBO
        print(f"\n  >>> {variant} POOLED observed n={n_obs} meanEV={obs_mean:+.3f}R")
        print(f"      PLACEBO A: P(random meanEV ≥ observed) = {p:.4f}  "
              f"{'PASS (filter selects)' if p <= 0.05 else 'FAIL (geometry only)'}")


if __name__ == "__main__":
    main()
