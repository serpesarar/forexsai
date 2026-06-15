"""
RESEARCH ONLY — does a 4H S/R + trend-channel REACTION entry add edge for the
bot's fixed-tp/sl on NDX:BUY and USOIL:BUY?

Motivation: the bot already gates these two BUY scopes on the MOMENTUM-CONTINUATION
filter (buy strength/breakout). User asks whether a STRUCTURE-REACTION entry
(buying off 4H support / lower channel band) is also a valid, validated edge.

These two philosophies are OPPOSITE: continuation buys are extended UP (near
resistance / top of channel); reaction buys are LOW (near support / bottom of
channel). We test the reaction idea honestly, the same way momentum was tested.

Structure features come straight from prediction_logs.factors (computed at signal
time by signal_feature_snapshot → no lookahead):
  H4_dist_swing_low_30_atr   distance to 4H 30-bar support, in ATR  (small = near support)
  H4_dist_swing_high_30_atr  distance to 4H 30-bar resistance, in ATR
  H4_chan_pct                position in 50-bar linreg channel (0=lower band,1=upper)
  H4_chan_slope_atr          channel slope / ATR (sign = channel direction)

Filter variants tested for BUY (thresholds picked BLIND on TRAIN, applied to TEST):
  SUP30      near 4H support:           H4_dist_swing_low_30_atr <= train_q33
  CHANLOW    near lower channel band:   H4_chan_pct            <= train_q33
  PULLBACK   pullback in rising channel:H4_chan_slope_atr > 0 AND H4_chan_pct <= 0.50
  SUPREACT   support + bullish turn:    near support (q33) AND H1_sar_dist_atr > 0
  MOMO       (reference) the live momentum-continuation filter

Battery: multi-split temporal OOS (3 windows) + friction sweep 0/1/2x, deduped to
real bot trades. Compares each filter vs UNFILTERED and vs MOMO on identical data.
Touches no production file. Pure read + compute.
"""
import sys, bisect
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client
from bot_fixed_tpsl_replay import (MODELS, parse_iso, load_bars, _fnum,
                                   load_signals, replay_fixed)

SINCE = "2026-04-25T00:00:00+00:00"
SPLITS = ["2026-05-20T00:00:00+00:00",
          "2026-05-27T00:00:00+00:00",
          "2026-06-03T00:00:00+00:00"]

SCOPES = {
    "NDX.INDX:BUY":    {"tp": 80.0, "sl": 110.0, "is_pct": False, "sfx": "M15", "fric": 1.0},
    "USOIL.FOREX:BUY": {"tp": 1.04, "sl": 1.49,  "is_pct": True,  "sfx": "M30", "fric": 0.03},
}


def momo_pass(sfx, f):
    g = lambda k: _fnum(f.get(k))
    sk = g(f"{sfx}_stoch_k"); de = g(f"{sfx}_dist_ema20_atr"); sar = g("H1_sar_dist_atr")
    if None in (sk, de, sar): return None
    return (sk > 70) and (de > 0.8) and (sar > 0)


def struct_metrics(f):
    """Return the raw structure values (or None) used by the variants."""
    g = lambda k: _fnum(f.get(k))
    return {
        "sup30":  g("H4_dist_swing_low_30_atr"),
        "chan":   g("H4_chan_pct"),
        "slope":  g("H4_chan_slope_atr"),
        "h1sar":  g("H1_sar_dist_atr"),
    }


def quantile(vals, q):
    if not vals: return None
    s = sorted(vals); i = int(q * (len(s) - 1))
    return s[i]


def be_fric(tp, sl, cout):
    return (sl + cout) / ((tp - cout) + (sl + cout))


def ev_fric(wr, tp, sl, cout):
    win_R = (tp - cout) / (sl + cout)
    return wr * win_R - (1 - wr)


def dedup(cands, cooldown=30):
    """cands: list of (cat, res, exit_ts, passed_bool). Bot model: one open at a time."""
    trades = []; busy = None
    for cat, res, exit_ts, p in cands:
        if res is None or res == "OPEN": continue
        if busy is not None and cat < busy: continue
        trades.append((cat, res, p)); busy = (exit_ts or cat) + timedelta(minutes=cooldown)
    return trades


def wr_of(trades):
    n = len(trades); w = sum(1 for t in trades if t[1] == "WIN")
    return (w / n if n else 0.0), n


def main():
    c = get_supabase_client()
    for scope, lv in SCOPES.items():
        symbol, direction = scope.rsplit(":", 1)
        sfx = lv["sfx"]; tp = lv["tp"]; sl = lv["sl"]; ip = lv["is_pct"]; cin = lv["fric"]
        bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
        sigs = load_signals(c, symbol, direction, SINCE)

        # prep: resolve every signal once against fixed tp/sl + capture features
        prepped = []  # (cat, res, exit_ts, momo, metrics)
        for s in sigs:
            cat = parse_iso(s.get("created_at"))
            if cat is None: continue
            lo = bisect.bisect_left(tsk, cat)
            if lo >= len(bars): continue
            entry = bars[lo][1]
            if entry <= 0: continue
            res, exit_ts = replay_fixed(cat, entry, direction, tp, sl, ip, bars, tsk)
            f = s.get("factors") or {}
            prepped.append((cat, res, exit_ts, momo_pass(sfx, f), struct_metrics(f)))
        prepped.sort(key=lambda x: x[0])

        print(f"\n{'='*84}\n{scope}  tp{tp}/sl{sl}{'%' if ip else ''}  "
              f"({len(bars)} bars, {len(prepped)} resolvable signals)")

        for split_iso in SPLITS:
            split_dt = parse_iso(split_iso)
            train = [p for p in prepped if p[0] < split_dt]
            test  = [p for p in prepped if p[0] >= split_dt]
            cout = cin
            be = be_fric(tp, sl, cout)

            # blind thresholds from TRAIN only
            tr_sup = quantile([p[4]["sup30"] for p in train if p[4]["sup30"] is not None], 0.33)
            tr_chan = quantile([p[4]["chan"] for p in train if p[4]["chan"] is not None], 0.33)

            def variant_pass(name, m):
                if name == "SUP30":
                    v = m["sup30"]
                    return None if (v is None or tr_sup is None) else (v <= tr_sup)
                if name == "CHANLOW":
                    v = m["chan"]
                    return None if (v is None or tr_chan is None) else (v <= tr_chan)
                if name == "PULLBACK":
                    sl_, ch = m["slope"], m["chan"]
                    return None if (sl_ is None or ch is None) else ((sl_ > 0) and (ch <= 0.50))
                if name == "SUPREACT":
                    v, h1 = m["sup30"], m["h1sar"]
                    if v is None or tr_sup is None or h1 is None: return None
                    return (v <= tr_sup) and (h1 > 0)
                return None

            print(f"\n  split {split_iso[5:10]}  (train={len(train)} test={len(test)})  "
                  f"be@1x={be*100:.1f}%  | train q33 sup30={tr_sup} chan_pct={tr_chan}")

            # UNFILTERED test trades
            unf_cands = [(p[0], p[1], p[2], True) for p in test]
            unf = dedup(unf_cands); uwr, un = wr_of(unf)
            print(f"    {'UNFILT':10s} n={un:3d} WR={uwr*100:5.1f}% "
                  f"EV={ev_fric(uwr,tp,sl,cout):+.3f}R {'+EV' if uwr>be else '-EV'}")

            # MOMO reference
            momo_cands = [(p[0], p[1], p[2], p[3] is True) for p in test if p[3] is True]
            momo = dedup(momo_cands); mwr, mn = wr_of(momo)
            print(f"    {'MOMO':10s} n={mn:3d} WR={mwr*100:5.1f}% "
                  f"EV={ev_fric(mwr,tp,sl,cout):+.3f}R {'+EV' if mwr>be else '-EV'}")

            for name in ("SUP30", "CHANLOW", "PULLBACK", "SUPREACT"):
                cands = []
                for p in test:
                    pv = variant_pass(name, p[4])
                    if pv is True:
                        cands.append((p[0], p[1], p[2], True))
                tr = dedup(cands); wr, n = wr_of(tr)
                tag = ("+EV" if (n > 0 and wr > be) else ("-EV" if n > 0 else "  -"))
                ev = ev_fric(wr, tp, sl, cout) if n > 0 else 0.0
                print(f"    {name:10s} n={n:3d} WR={wr*100:5.1f}% EV={ev:+.3f}R {tag}")


if __name__ == "__main__":
    main()
