"""
RESEARCH ONLY — SELL "rejection off 4H resistance" entry with an EMPIRICALLY
DERIVED tp/sl (not the bot's wide fixed tp/sl).

Why a custom tp/sl: the prior structure test showed reaction entries die against
the bot's far fixed TP because a bounce lacks the momentum to reach it. User's
fix: measure how far price ACTUALLY drops after rejecting from prior resistance,
and size TP to that typical down-move so the target matches the entry thesis.

Two phases, kept OOS:
  PHASE 1 (TRAIN only) — for every resistance-rejection SELL entry, walk 1m bars
    forward (<= MAX_HOLD) and record:
       MFE_down% = max favorable drop  = max(entry - low)/entry*100
       MAE_up%   = max adverse rally    = max(high - entry)/entry*100
    Report the distributions. Derive:
       TP% = median MFE_down (the "average down-move" requested)
       SL% = 70th pct of MAE_up (tolerate typical pre-move noise / invalidation)
  PHASE 2 (TEST only) — replay TEST rejections with the TRAIN-derived (TP%,SL%),
    first-touch resolution, dedup to real trades, friction sweep. Compare to
    UNFILTERED (same derived tp/sl) and to the bot's fixed tp/sl as reference.

Resistance-rejection SELL entry (features from prediction_logs.factors, no lookahead):
    near 4H resistance:  H4_dist_swing_high_30_atr <= TRAIN q33   (small = near res)
    bearish turn:        H1_sar_dist_atr < 0                      (sar above price)

Touches no production file. Pure read + compute.
"""
import sys, bisect, statistics as st
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client
from bot_fixed_tpsl_replay import MODELS, parse_iso, load_bars, _fnum, load_signals

SINCE = "2026-04-25T00:00:00+00:00"
SPLITS = ["2026-05-20T00:00:00+00:00",
          "2026-05-27T00:00:00+00:00",
          "2026-06-03T00:00:00+00:00"]
MAX_HOLD_MIN = 1440

# bot fixed tp/sl (reference) — index in points, USOIL in %
BOT_FIXED = {
    "NDX.INDX:SELL":    {"tp": 80.0, "sl": 110.0, "is_pct": False},
    "USOIL.FOREX:SELL": {"tp": 1.04, "sl": 1.49,  "is_pct": True},
    "GDAXI.INDX:SELL":  {"tp": 67.0, "sl": 119.0, "is_pct": False},
}
SCOPES = ["NDX.INDX:SELL", "USOIL.FOREX:SELL", "GDAXI.INDX:SELL"]
FRIC_PCT = {  # 1x friction as % of price (entry+exit), rough
    "NDX.INDX:SELL":    0.004,
    "USOIL.FOREX:SELL": 0.03,
    "GDAXI.INDX:SELL":  0.006,
}


def rejection_pass(f, tr_res_q33):
    """near 4H resistance AND bearish turn."""
    g = lambda k: _fnum(f.get(k))
    dh = g("H4_dist_swing_high_30_atr"); sar = g("H1_sar_dist_atr")
    if dh is None or sar is None or tr_res_q33 is None:
        return None
    return (dh <= tr_res_q33) and (sar < 0)


def quantile(vals, q):
    if not vals: return None
    s = sorted(vals); i = int(q * (len(s) - 1))
    return s[i]


def excursion_pct(entry_ts, entry, bars, tsk):
    """SELL excursion: return (MFE_down%, MAE_up%) over MAX_HOLD horizon."""
    end_ts = entry_ts + timedelta(minutes=MAX_HOLD_MIN)
    lo = bisect.bisect_left(tsk, entry_ts)
    mfe = 0.0; mae = 0.0; seen = False
    for i in range(lo, len(bars)):
        ts, o, h, l, cl = bars[i]
        if ts > end_ts: break
        seen = True
        mfe = max(mfe, (entry - l) / entry * 100.0)   # favorable drop
        mae = max(mae, (h - entry) / entry * 100.0)   # adverse rally
    return (mfe, mae) if seen else (None, None)


def replay_pct_sell(entry_ts, entry, tp_pct, sl_pct, bars, tsk):
    """First-touch SELL replay with %-based tp/sl. Returns (res, exit_ts)."""
    tp_px = entry * (1 - tp_pct / 100.0)
    sl_px = entry * (1 + sl_pct / 100.0)
    end_ts = entry_ts + timedelta(minutes=MAX_HOLD_MIN)
    lo = bisect.bisect_left(tsk, entry_ts)
    for i in range(lo, len(bars)):
        ts, o, h, l, cl = bars[i]
        if ts > end_ts: break
        hit_tp = l <= tp_px; hit_sl = h >= sl_px
        if hit_tp and hit_sl:
            bullish = cl >= o
            return ("LOSS" if bullish else "WIN"), ts   # SELL: bullish bar -> SL first
        if hit_tp: return "WIN", ts
        if hit_sl: return "LOSS", ts
    return "OPEN", None


def be_fric(tp, sl, cout):
    return (sl + cout) / ((tp - cout) + (sl + cout))


def ev_fric(wr, tp, sl, cout):
    return wr * ((tp - cout) / (sl + cout)) - (1 - wr)


def dedup(cands, cooldown=30):
    trades = []; busy = None
    for cat, res, exit_ts in cands:
        if res is None or res == "OPEN": continue
        if busy is not None and cat < busy: continue
        trades.append((cat, res)); busy = (exit_ts or cat) + timedelta(minutes=cooldown)
    return trades


def wr_of(trades):
    n = len(trades); w = sum(1 for t in trades if t[1] == "WIN")
    return (w / n if n else 0.0), n


def main():
    c = get_supabase_client()
    for scope in SCOPES:
        symbol, direction = scope.rsplit(":", 1)
        bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
        sigs = load_signals(c, symbol, direction, SINCE)
        fric = FRIC_PCT[scope]

        prepped = []  # (cat, entry, factors)
        for s in sigs:
            cat = parse_iso(s.get("created_at"))
            if cat is None: continue
            lo = bisect.bisect_left(tsk, cat)
            if lo >= len(bars): continue
            entry = bars[lo][1]
            if entry <= 0: continue
            prepped.append((cat, entry, s.get("factors") or {}))
        prepped.sort(key=lambda x: x[0])

        print(f"\n{'='*88}\n{scope}  ({len(bars)} bars, {len(prepped)} signals)  friction≈{fric}% each side")

        for split_iso in SPLITS:
            split_dt = parse_iso(split_iso)
            train = [p for p in prepped if p[0] < split_dt]
            test  = [p for p in prepped if p[0] >= split_dt]

            # near-resistance threshold from TRAIN
            tr_res_q33 = quantile(
                [_fnum(p[2].get("H4_dist_swing_high_30_atr")) for p in train
                 if _fnum(p[2].get("H4_dist_swing_high_30_atr")) is not None], 0.33)

            # PHASE 1: TRAIN excursion distribution on rejection entries
            mfes = []; maes = []
            for cat, entry, f in train:
                if rejection_pass(f, tr_res_q33) is not True: continue
                mfe, mae = excursion_pct(cat, entry, bars, tsk)
                if mfe is not None:
                    mfes.append(mfe); maes.append(mae)

            if len(mfes) < 8:
                print(f"\n  split {split_iso[5:10]}: train rejection n={len(mfes)} — too few to derive tp/sl, skip")
                continue

            tp_pct = round(st.median(mfes), 3)
            sl_pct = round(quantile(maes, 0.70), 3)
            cout = fric
            be = be_fric(tp_pct, sl_pct, cout)

            def pct_stat(v):
                return (f"med={st.median(v):.3f} mean={st.mean(v):.3f} "
                        f"p25={quantile(v,.25):.3f} p75={quantile(v,.75):.3f} max={max(v):.3f}")

            print(f"\n  split {split_iso[5:10]}  train_rej n={len(mfes)}  res_q33={tr_res_q33:.2f} ATR")
            print(f"    MFE_down%: {pct_stat(mfes)}")
            print(f"    MAE_up%  : {pct_stat(maes)}")
            print(f"    -> derived TP={tp_pct}%  SL={sl_pct}%  (R:R 1:{sl_pct/tp_pct:.2f})  be@1x={be*100:.1f}%")

            # PHASE 2: TEST replay with derived tp/sl
            rej_cands = []; unf_cands = []
            log_rej = []; log_nonrej = []   # per-LOG (no dedup) WIN/LOSS
            for cat, entry, f in test:
                res, ex = replay_pct_sell(cat, entry, tp_pct, sl_pct, bars, tsk)
                unf_cands.append((cat, res, ex))
                is_rej = rejection_pass(f, tr_res_q33) is True
                if is_rej:
                    rej_cands.append((cat, res, ex))
                if res in ("WIN", "LOSS"):
                    (log_rej if is_rej else log_nonrej).append(1 if res == "WIN" else 0)
            unf = dedup(unf_cands); uwr, un = wr_of(unf)
            rej = dedup(rej_cands); rwr, rn = wr_of(rej)
            print(f"    TEST  UNFILT(derived tp/sl) trades n={un:3d} WR={uwr*100:5.1f}% "
                  f"EV={ev_fric(uwr,tp_pct,sl_pct,cout):+.3f}R {'+EV' if uwr>be else '-EV'}")
            print(f"    TEST  REJECTION             trades n={rn:3d} WR={rwr*100:5.1f}% "
                  f"EV={ev_fric(rwr,tp_pct,sl_pct,cout):+.3f}R {'+EV' if rwr>be else '-EV'}")
            # per-LOG (bigger n, less dedup noise) — does the filter actually separate?
            kr = len(log_rej); kn = len(log_nonrej)
            rwr_l = sum(log_rej)/kr if kr else 0.0
            nwr_l = sum(log_nonrej)/kn if kn else 0.0
            print(f"      per-LOG: REJECTION k={kr:3d} WR={rwr_l*100:5.1f}% "
                  f"{'+EV' if rwr_l>be else '-EV'}  |  NON-REJ k={kn:3d} WR={nwr_l*100:5.1f}%  "
                  f"(filter edge = {(rwr_l-nwr_l)*100:+.1f}pp)")

            # friction sweep on the rejection set
            for mult in (0, 1, 2):
                co = fric * mult
                be_m = be_fric(tp_pct, sl_pct, co)
                ev_m = ev_fric(rwr, tp_pct, sl_pct, co)
                print(f"      friction {mult}x: be={be_m*100:.1f}%  EV={ev_m:+.3f}R "
                      f"{'+EV' if rwr>be_m else '-EV'}")


if __name__ == "__main__":
    main()
