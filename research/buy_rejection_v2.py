"""
RESEARCH ONLY — BUY "reaction off 4H support / lower trend-channel band" with an
EMPIRICALLY DERIVED tp/sl, mirroring sell_rejection_v2.py for the BUY side.

Why: the earlier BUY structure test (structure_filter_oos.py) was judged −EV, but
it replayed against the bot's WIDE FIXED tp/sl — NOT a tp/sl matched to the actual
up-move after a support bounce. SELL only worked once tp/sl was derived from the
empirical move (+ reduced to p33 + a channel variant). This script gives BUY the
SAME treatment so the comparison is apples-to-apples.

Two entry variants (features from prediction_logs.factors, no lookahead):
  SWING : near 4H swing-low support   H4_dist_swing_low_30_atr <= TRAIN q33
  CHAN  : near lower trend-channel band H4_chan_pct             <= TRAIN q33
  both also require bullish turn:        H1_sar_dist_atr > 0

Derive (TRAIN): TP = p33 of MFE_up (favorable rise), SL = p50 of MAE_down
(adverse drop). Then TEST per-LOG + deduped + friction, pooled bootstrap on the
longest window. Touches no production file.
"""
import sys, bisect, random, statistics as st
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client
from bot_fixed_tpsl_replay import MODELS, parse_iso, load_bars, _fnum, load_signals
from sell_resistance_reaction import (quantile, dedup, wr_of, be_fric, ev_fric)

random.seed(7)
SINCE = "2026-04-25T00:00:00+00:00"
SPLITS = ["2026-05-20T00:00:00+00:00",
          "2026-05-27T00:00:00+00:00",
          "2026-06-03T00:00:00+00:00"]
SCOPES = ["NDX.INDX:BUY", "USOIL.FOREX:BUY", "GDAXI.INDX:BUY"]
FRIC_PCT = {"NDX.INDX:BUY": 0.004, "USOIL.FOREX:BUY": 0.03, "GDAXI.INDX:BUY": 0.006}
MAX_HOLD_MIN = 1440
TP_PCTL = 0.33
SL_PCTL = 0.50


def excursion_buy(entry_ts, entry, bars, tsk):
    """BUY excursion: (MFE_up%, MAE_down%) over horizon."""
    end_ts = entry_ts + timedelta(minutes=MAX_HOLD_MIN)
    lo = bisect.bisect_left(tsk, entry_ts)
    mfe = 0.0; mae = 0.0; seen = False
    for i in range(lo, len(bars)):
        ts, o, h, l, cl = bars[i]
        if ts > end_ts: break
        seen = True
        mfe = max(mfe, (h - entry) / entry * 100.0)   # favorable rise
        mae = max(mae, (entry - l) / entry * 100.0)   # adverse drop
    return (mfe, mae) if seen else (None, None)


def replay_pct_buy(entry_ts, entry, tp_pct, sl_pct, bars, tsk):
    """First-touch BUY replay with %-based tp/sl. Returns (res, exit_ts)."""
    tp_px = entry * (1 + tp_pct / 100.0)
    sl_px = entry * (1 - sl_pct / 100.0)
    end_ts = entry_ts + timedelta(minutes=MAX_HOLD_MIN)
    lo = bisect.bisect_left(tsk, entry_ts)
    for i in range(lo, len(bars)):
        ts, o, h, l, cl = bars[i]
        if ts > end_ts: break
        hit_tp = h >= tp_px; hit_sl = l <= sl_px
        if hit_tp and hit_sl:
            bearish = cl < o
            return ("LOSS" if bearish else "WIN"), ts   # BUY: bearish bar -> SL first
        if hit_tp: return "WIN", ts
        if hit_sl: return "LOSS", ts
    return "OPEN", None


def variant_pass(name, f, thr):
    g = lambda k: _fnum(f.get(k))
    sar = g("H1_sar_dist_atr")
    if sar is None or sar <= 0:          # bullish turn for BUY
        return False
    if name == "SWING":
        v = g("H4_dist_swing_low_30_atr")
        return v is not None and thr is not None and v <= thr
    if name == "CHAN":
        v = g("H4_chan_pct")
        return v is not None and thr is not None and v <= thr   # lower band
    return False


def derive_thr(name, train):
    key = "H4_dist_swing_low_30_atr" if name == "SWING" else "H4_chan_pct"
    vals = [_fnum(f.get(key)) for _, _, f in train if _fnum(f.get(key)) is not None]
    if not vals: return None
    return quantile(vals, 0.33)          # both near-low: small value = near support/band


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

    out = []
    for split_iso in SPLITS:
        split_dt = parse_iso(split_iso)
        train = [p for p in prepped if p[0] < split_dt]
        test  = [p for p in prepped if p[0] >= split_dt]
        thr = derive_thr(variant, train)

        mfes = []; maes = []
        for cat, entry, f in train:
            if not variant_pass(variant, f, thr): continue
            mfe, mae = excursion_buy(cat, entry, bars, tsk)
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
            res, ex = replay_pct_buy(cat, entry, tp, sl, bars, tsk)
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
        print(f"\n{'#'*90}\n# BUY VARIANT = {variant}   (TP=p{int(TP_PCTL*100)} of up-move, SL=p{int(SL_PCTL*100)} of adverse)\n{'#'*90}")
        pooled = {}
        for scope in SCOPES:
            res = run(c, scope, variant)
            print(f"\n{scope}")
            for r in res:
                if r.get("skip"):
                    print(f"  split {r['split']}: too few train reactions (n={r.get('n_train','?')}) — skip")
                    continue
                print(f"  split {r['split']}: TP={r['tp']}% SL={r['sl']}% (win {r['win_R']:+.2f}R, be {r['be']*100:.1f}%)")
                print(f"     per-LOG REACT k={r['kr']:3d} WR={r['rwr_log']*100:5.1f}%  vs NON k={r['kn']:4d} "
                      f"WR={r['nwr_log']*100:5.1f}%  edge={(r['rwr_log']-r['nwr_log'])*100:+.1f}pp")
                print(f"     deduped trades n={r['rn']:2d} WR={r['rwr']*100:5.1f}% EV={r['ev']:+.3f}R "
                      f"{'+EV' if r['rn'] and r['rwr']>r['be'] else '-EV'}  {r['trades']}")
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
            print(f"\n  >>> BUY {variant} POOLED deduped (split 05-20) n={n} meanEV={mean:+.3f}R wins={wins}/{n}")
            print(f"      bootstrap 95% CI [{lo:+.3f}R, {hi:+.3f}R]  P(EV>0)={p_pos*100:.1f}%")
        else:
            print(f"\n  >>> BUY {variant} POOLED n={n} — too small for bootstrap")


if __name__ == "__main__":
    main()
