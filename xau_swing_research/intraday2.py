"""Serious intraday battery — target ~1 trade/day, BUY-only gold. Tests the styles
the user named that weren't covered yet: momentum-continuation, opening-range
breakout (ORB), oscillator mean-reversion (the indices edge), EMA pullback. Each
run with TIGHT targets (user wants tight TP) AND fair-RR targets, real friction.
Honest goal: find any daily-frequency +EV config, or prove the tight-TP trap in numbers.
"""
from __future__ import annotations
import warnings; warnings.simplefilter("ignore")
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as _swv
from swing_battery import load, rsi, atr, stats, bootstrap_ev

FRICTION = 0.40


def rmax(s, w):
    a = np.asarray(s, float); o = np.full(len(a), np.nan)
    if len(a) >= w: o[w-1:] = _swv(a, w).max(axis=1)
    return o

def rmin(s, w):
    a = np.asarray(s, float); o = np.full(len(a), np.nan)
    if len(a) >= w: o[w-1:] = _swv(a, w).min(axis=1)
    return o


def prep():
    d = load("M15")
    d["ema20"] = d["close"].ewm(span=20, adjust=False).mean()
    d["ema50"] = d["close"].ewm(span=50, adjust=False).mean()
    d["ema200"] = d["close"].ewm(span=200, adjust=False).mean()
    d["rsi"] = rsi(d["close"], 14)
    d["atr"] = atr(d, 14)
    d["hour"] = d["ts"].dt.hour
    d["hi8"] = rmax(d["high"].values, 8)     # 2h
    d["hi4"] = rmax(d["high"].values, 4)     # 1h
    # stoch %K (14)
    ll = rmin(d["low"].values, 14); hh = rmax(d["high"].values, 14)
    d["stoch"] = 100*(d["close"].values - ll)/np.where((hh-ll) == 0, np.nan, hh-ll)
    return d


def backtest(mask, d, sl_atr, tp_atr, max_bars, fr=FRICTION):
    o, hi, lo, cl, a, ts = (d[c].values for c in ["open","high","low","close","atr","ts"])
    idx = np.where(mask)[0]; rows = []; busy = -1
    for i in idx:
        if i+1 >= len(d) or not np.isfinite(a[i]) or a[i] <= 0: continue
        if i+1 <= busy: continue
        ep = o[i+1]; risk = sl_atr*a[i]; sl = ep-risk; tp = ep+tp_atr*a[i]
        end = min(i+1+max_bars, len(cl)); xpx = cl[end-1]; bars = end-(i+1)
        for j in range(i+1, end):
            if lo[j] <= sl: xpx, bars = sl, j-i; break
            if hi[j] >= tp: xpx, bars = tp, j-i; break
        busy = i+1+bars
        net = (xpx-ep)-fr
        rows.append({"ts": pd.Timestamp(ts[i+1]), "net": net, "R": net/risk, "bars": bars, "win": net > 0})
    return pd.DataFrame(rows)


def main():
    d = prep()
    days = (d["ts"].iloc[-1]-d["ts"].iloc[0]).days
    up_intra = (d["close"] > d["ema50"]) & (d["ema50"] > d["ema200"])
    strats = {
        "MOM_CONT (break 2h + uptrend)": (d["close"].values >= np.roll(d["hi8"].values,1)) & up_intra.values,
        "ORB (London/NY open break)":    ((d["hour"].isin([8,9,14,15])).values &
                                          (d["close"].values >= np.roll(d["hi4"].values,1)) & (d["close"].values>d["ema50"].values)),
        "OSC_MR (RSI<35 bounce, uptr)":  (d["rsi"].values<35) & (d["close"].values>d["ema200"].values) & (d["close"].values>d["open"].values),
        "STOCH_MR (stoch<20 bounce)":    (d["stoch"].values<20) & (d["close"].values>d["ema200"].values) & (d["close"].values>d["open"].values),
        "EMA20_PB (pullback in uptrend)":(d["low"].values<=d["ema20"].values) & (d["close"].values>d["ema20"].values) & (d["ema20"].values>d["ema50"].values) & (d["ema50"].values>d["ema200"].values),
    }
    exits = {
        "TIGHT 1:1 (0.5/0.5)":  (0.5, 0.5, 16),
        "TIGHTwr (1.0/0.5)":    (1.0, 0.5, 16),   # high-WR trap demo
        "FAIR (1.0/1.5)":       (1.0, 1.5, 24),
        "FAIR+ (1.0/2.0)":      (1.0, 2.0, 32),
    }
    print(f"M15 {d.ts.iloc[0].date()}→{d.ts.iloc[-1].date()} ({days}d ≈ {days*5//7} trading days)  friction=${FRICTION}\n")
    print(f"{'strategy':32}{'exit':22}{'n':>5}{'/day':>6}{'WR':>6}{'avgR':>7}{'PF':>6} {'EV95CI'}")
    print("-"*108)
    for sname, mask in strats.items():
        for ename,(sla,tpa,mb) in exits.items():
            tr = backtest(mask, d, sla, tpa, mb)
            if len(tr) < 20: continue
            s = stats(tr); ci = bootstrap_ev(tr["R"].values)
            perday = len(tr)/(days*5/7)
            mark = "  <<< +EV" if ci[0] > 0 else ""
            print(f"{sname:32}{ename:22}{s['n']:>5}{perday:>6.2f}{s['WR']:>6}{s['avgR']:>7.3f}{s['PF']:>6}  {ci}{mark}")
        print()
    print("<<< +EV = bootstrap 95% CI lower bound > 0 after friction.")
    print("Watch: TIGHTwr lifts WR but check avgR — high WR + negative avgR = the trap.")


if __name__ == "__main__":
    main()
