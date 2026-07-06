"""Intraday BUY-only tests on M15 — the user's idea: support-zone bounce + upward
breakout from a base, faster/shorter holds than the daily swing. Gold = BUY-only
(label-independent finding). The danger: intraday friction. We test honestly.

Signal on closed M15 bar i, fill at M15 open[i+1], simulate forward on M15
(pessimistic SL-first), ATR(14) TP/SL + time-stop, friction in $.
"""
from __future__ import annotations
import warnings; warnings.simplefilter("ignore")
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as _swv
from swing_battery import load, rsi, atr, stats, bootstrap_ev

FRICTION = 0.40
TF = "M15"
BARS_PER_DAY = 96   # M15


# pandas .rolling().min/max is broken on large arrays in this env (py3.14/pd2.2.2);
# use numpy sliding-window instead.
def roll_min(s, w):
    a = np.asarray(s, float); out = np.full(len(a), np.nan)
    if len(a) >= w: out[w-1:] = _swv(a, w).min(axis=1)
    return out

def roll_max(s, w):
    a = np.asarray(s, float); out = np.full(len(a), np.nan)
    if len(a) >= w: out[w-1:] = _swv(a, w).max(axis=1)
    return out


def prep(tf):
    d = load(tf)
    d["ema50"] = d["close"].ewm(span=50, adjust=False).mean()
    d["ema200"] = d["close"].ewm(span=200, adjust=False).mean()
    d["rsi"] = rsi(d["close"], 14)
    d["atr"] = atr(d, 14)
    d["sup"] = roll_min(d["low"], 48)          # support = 48-bar (~12h) low
    d["res"] = roll_max(d["high"], 48)
    d["hh20"] = roll_max(d["high"], 20)
    d["year"] = d["ts"].dt.year
    return d


def simulate_same_tf(entry_px, sl, tp, i0, hi, lo, cl, max_bars):
    end = min(i0 + max_bars, len(cl))
    for j in range(i0, end):
        if lo[j] <= sl: return sl, j - i0 + 1
        if hi[j] >= tp: return tp, j - i0 + 1
    return (cl[end-1], end - i0) if end > i0 else (entry_px, 0)


def backtest(mask, d, sl_atr, tp_atr, max_bars, fr=FRICTION):
    o, hi, lo, cl, a, ts = (d[c].values for c in ["open", "high", "low", "close", "atr", "ts"])
    idx = np.where(mask)[0]
    rows, busy = [], -1
    for i in idx:
        if i + 1 >= len(d) or not np.isfinite(a[i]) or a[i] <= 0: continue
        if i + 1 <= busy: continue          # one position at a time
        ep = o[i+1]; risk = sl_atr * a[i]
        sl, tp = ep - risk, ep + tp_atr * a[i]
        xpx, bars = simulate_same_tf(ep, sl, tp, i+1, hi, lo, cl, max_bars)
        busy = i + 1 + bars
        net = (xpx - ep) - fr
        rows.append({"ts": pd.Timestamp(ts[i+1]), "year": pd.Timestamp(ts[i+1]).year,
                     "net": net, "R": net/risk, "bars": bars, "win": net > 0})
    return pd.DataFrame(rows)


def main():
    d = prep(TF)
    h1 = load("H1"); h1["ema200"] = h1["close"].ewm(span=200, adjust=False).mean()
    # H1 uptrend flag mapped onto M15 by timestamp (no lookahead: use last closed H1)
    h1idx = np.searchsorted(h1["ts"].values, d["ts"].values, side="right") - 1
    h1up = (h1["close"].values > h1["ema200"].values)
    d["h1_up"] = np.where(h1idx >= 0, h1up[h1idx.clip(min=0)], False)
    print(f"{TF} bars={len(d)}  {d.ts.iloc[0].date()}→{d.ts.iloc[-1].date()}  friction=${FRICTION}\n")

    near_sup = d["low"] <= d["sup"].shift(1) + 0.3*d["atr"]      # tagged support zone
    bull = (d["close"] > d["open"]) & (d["close"] > (d["high"]+d["low"])/2)
    up15 = d["close"] > d["ema200"]
    brk = d["close"] >= d["hh20"].shift(1)                        # 20-bar intraday breakout

    strats = {
        "SUP_BOUNCE (raw)":            (near_sup & bull).values,
        "SUP_BOUNCE +M15up":           (near_sup & bull & up15).values,
        "SUP_BOUNCE +H1up":            (near_sup & bull & d["h1_up"]).values,
        "SUP_BOUNCE +H1up +RSI<40":    (near_sup & bull & d["h1_up"] & (d["rsi"]<40)).values,
        "BREAKOUT_UP +H1up":           (brk & d["h1_up"]).values,
        "BREAKOUT_from_base +H1up":    (brk & d["h1_up"] & (d["close"].shift(1) <= d["sup"].shift(1)+0.5*d["atr"])).values,
    }
    exits = [(1.0, 1.5, 32), (1.0, 2.0, 64), (1.5, 3.0, 96)]   # max_bars in M15 (32≈8h,64≈16h,96≈1d)

    print(f"{'strategy':28} {'exit(SL/TP/bars)':18} {'n':>5} {'WR':>5} {'avgR':>6} {'sumR':>7} {'PF':>5} {'EV95CI'}")
    print("-"*100)
    for name, mask in strats.items():
        for sla, tpa, mb in exits:
            tr = backtest(mask, d, sla, tpa, mb)
            if len(tr) < 15: continue
            s = stats(tr); ci = bootstrap_ev(tr["R"].values)
            tag = f"{sla}/{tpa}/{mb}b"
            mark = "  <<<" if ci[0] > 0 else ""
            print(f"{name:28} {tag:18} {s['n']:>5} {s['WR']:>5} {s['avgR']:>6.3f} "
                  f"{s['sumR']:>7.1f} {s['PF']:>5} {ci}{mark}")
    print("\n  <<< = bootstrap 95% CI lower bound > 0 after friction (survivor)")


if __name__ == "__main__":
    main()
