"""
RESEARCH ONLY — SELL rejection v2: reduced (more conservative) tp/sl + a NEW
trend-channel variant, both OOS-tested. Successor to sell_resistance_reaction.py.

Changes vs v1 (per user 2026-06-15):
  - tp came out too ambitious (USOIL 3.8% etc.). REDUCE: derive TP from a LOWER
    percentile of the down-move (p33 — reached by ~2/3 of rejections), SL from
    p50 of the adverse rally. Tighter, more reachable targets.
  - add a TREND-CHANNEL entry variant: reject off the UPPER channel band
    (H4_chan_pct >= TRAIN q67) instead of the 30-bar swing high.

Two entry variants (features from prediction_logs.factors, no lookahead):
  SWING : near 4H swing-high resistance  H4_dist_swing_high_30_atr <= TRAIN q33
  CHAN  : near upper trend-channel band   H4_chan_pct              >= TRAIN q67
  both also require bearish turn:          H1_sar_dist_atr < 0

Battery per split: TRAIN-derived reduced tp/sl -> TEST per-LOG (rejection vs
non-rejection) + deduped real trades + friction. Then pooled deduped bootstrap
on the longest window. Touches no production file.
"""
import sys, bisect, random, statistics as st
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client
from bot_fixed_tpsl_replay import MODELS, parse_iso, load_bars, _fnum, load_signals
from sell_resistance_reaction import (quantile, excursion_pct, replay_pct_sell,
                                      dedup, wr_of, be_fric, ev_fric, FRIC_PCT)

random.seed(7)
SINCE = "2026-04-25T00:00:00+00:00"
SPLITS = ["2026-05-20T00:00:00+00:00",
          "2026-05-27T00:00:00+00:00",
          "2026-06-03T00:00:00+00:00"]
SCOPES = ["NDX.INDX:SELL", "USOIL.FOREX:SELL", "GDAXI.INDX:SELL"]
TP_PCTL = 0.33   # reduced: down-move level reached by ~2/3 of rejections
SL_PCTL = 0.50   # reduced: median adverse rally


def variant_pass(name, f, thr):
    g = lambda k: _fnum(f.get(k))
    sar = g("H1_sar_dist_atr")
    if sar is None or sar >= 0:
        return False
    if name == "SWING":
        v = g("H4_dist_swing_high_30_atr")
        return v is not None and thr is not None and v <= thr
    if name == "CHAN":
        v = g("H4_chan_pct")
        return v is not None and thr is not None and v >= thr
    return False


def derive_thr(name, train):
    vals = []
    for _, _, f in train:
        v = _fnum(f.get("H4_dist_swing_high_30_atr") if name == "SWING" else f.get("H4_chan_pct"))
        if v is not None: vals.append(v)
    if not vals: return None
    return quantile(vals, 0.33 if name == "SWING" else 0.67)


def run(c, scope, variant):
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

    out = []  # per split dict
    for split_iso in SPLITS:
        split_dt = parse_iso(split_iso)
        train = [p for p in prepped if p[0] < split_dt]
        test  = [p for p in prepped if p[0] >= split_dt]
        thr = derive_thr(variant, train)

        mfes = []; maes = []
        for cat, entry, f in train:
            if not variant_pass(variant, f, thr): continue
            mfe, mae = excursion_pct(cat, entry, bars, tsk)
            if mfe is not None: mfes.append(mfe); maes.append(mae)
        if len(mfes) < 8:
            out.append({"split": split_iso[5:10], "n_train": len(mfes), "skip": True}); continue
        tp = round(quantile(mfes, TP_PCTL), 3)
        sl = round(quantile(maes, SL_PCTL), 3)
        if tp <= fric or sl <= 0:
            out.append({"split": split_iso[5:10], "skip": True}); continue
        be = be_fric(tp, sl, fric)

        rej_cands = []; log_rej = []; log_non = []
        for cat, entry, f in test:
            res, ex = replay_pct_sell(cat, entry, tp, sl, bars, tsk)
            is_r = variant_pass(variant, f, thr)
            if is_r: rej_cands.append((cat, res, ex))
            if res in ("WIN", "LOSS"):
                (log_rej if is_r else log_non).append(1 if res == "WIN" else 0)
        trades = dedup(rej_cands); rwr, rn = wr_of(trades)
        kr = len(log_rej); kn = len(log_non)
        out.append({
            "split": split_iso[5:10], "tp": tp, "sl": sl, "be": be, "fric": fric,
            "rn": rn, "rwr": rwr, "ev": ev_fric(rwr, tp, sl, fric),
            "kr": kr, "rwr_log": (sum(log_rej)/kr if kr else 0),
            "kn": kn, "nwr_log": (sum(log_non)/kn if kn else 0),
            "trades": [t[1][0] for t in trades],
            "win_R": (tp - fric) / (sl + fric),
        })
    return out


def main():
    c = get_supabase_client()
    for variant in ("SWING", "CHAN"):
        print(f"\n{'#'*90}\n# VARIANT = {variant}   (TP=p{int(TP_PCTL*100)} of down-move, SL=p{int(SL_PCTL*100)} of adverse)\n{'#'*90}")
        pooled = {}  # scope -> R list on split 05-20
        for scope in SCOPES:
            res = run(c, scope, variant)
            print(f"\n{scope}")
            for r in res:
                if r.get("skip"):
                    print(f"  split {r['split']}: too few train rejections (n={r.get('n_train','?')}) — skip")
                    continue
                print(f"  split {r['split']}: TP={r['tp']}% SL={r['sl']}% (win {r['win_R']:+.2f}R, be {r['be']*100:.1f}%)")
                print(f"     per-LOG REJ k={r['kr']:3d} WR={r['rwr_log']*100:5.1f}%  vs NON-REJ k={r['kn']:4d} "
                      f"WR={r['nwr_log']*100:5.1f}%  edge={(r['rwr_log']-r['nwr_log'])*100:+.1f}pp")
                print(f"     deduped trades n={r['rn']:2d} WR={r['rwr']*100:5.1f}% EV={r['ev']:+.3f}R "
                      f"{'+EV' if r['rn'] and r['rwr']>r['be'] else '-EV'}  {r['trades']}")
            # pooled bootstrap material = split 05-20 deduped trades in R
            r0 = res[0]
            if not r0.get("skip"):
                Rs = [r0["win_R"] if t == "W" else -1.0 for t in r0["trades"]]
                pooled[scope] = Rs

        allR = [x for v in pooled.values() for x in v]
        n = len(allR)
        if n >= 5:
            mean = st.mean(allR); wins = sum(1 for x in allR if x > 0)
            boots = []
            for _ in range(5000):
                s = [allR[random.randrange(n)] for _ in range(n)]
                boots.append(sum(s)/n)
            boots.sort()
            lo = boots[int(0.025*5000)]; hi = boots[int(0.975*5000)-1]
            p_pos = sum(1 for b in boots if b > 0)/5000
            print(f"\n  >>> {variant} POOLED deduped (split 05-20) n={n} meanEV={mean:+.3f}R wins={wins}/{n}")
            print(f"      bootstrap 95% CI [{lo:+.3f}R, {hi:+.3f}R]  P(EV>0)={p_pos*100:.1f}%")
        else:
            print(f"\n  >>> {variant} POOLED n={n} — too small for bootstrap")


if __name__ == "__main__":
    main()
