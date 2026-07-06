"""H1 Donchian breakout — the max-frequency variant. Signal on H1, intrabar TP/SL
fills on M15 (finer), D1 (and optional H4) uptrend confluence, BUY-only, dedup,
per-year, bootstrap. Question: does the edge still survive after friction at H1, or
has it decayed below zero like M15? Restricted to the M15-covered span (2022-02+)."""
from __future__ import annotations
import warnings; warnings.simplefilter("ignore")
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as _swv
from swing_battery import load, rsi, atr, simulate, stats, bootstrap_ev

FRICTION = 0.40

def rmax(s, w):
    a = np.asarray(s, float); o = np.full(len(a), np.nan)
    if len(a) >= w: o[w-1:] = _swv(a, w).max(axis=1)
    return o

def uptrend_on(target, src):
    up = (src["close"].values > src["close"].ewm(span=200, adjust=False).mean().values)
    j = np.searchsorted(src["ts"].values, target["ts"].values, side="right") - 1
    return np.where(j >= 0, up[j.clip(min=0)], False)

def backtest(mask, h1, fills, sl_atr, tp_atr, max_h1_bars):
    o, a, ts = h1["open"].values, h1["atr"].values, h1["ts"].values
    fts = fills["ts"].values
    idx = np.where(mask)[0]; rows = []; busy = np.datetime64("1900-01-01")
    max_fill = max_h1_bars * 4   # H1 → M15 bars
    for i in idx:
        if i+1 >= len(h1) or not np.isfinite(a[i]) or a[i] <= 0: continue
        ets = ts[i+1]
        if ets < busy: continue
        ep = o[i+1]; risk = sl_atr*a[i]; sl, tp = ep-risk, ep+tp_atr*a[i]
        xpx, bars = simulate("BUY", ep, sl, tp, ets, fills, max_fill)
        j = np.searchsorted(fts, ets, "left"); busy = fts[min(j+bars, len(fts)-1)]
        net = (xpx-ep) - FRICTION
        rows.append({"ts": pd.Timestamp(ets), "year": pd.Timestamp(ets).year,
                     "net": net, "R": net/risk, "bars": bars, "win": net > 0})
    return pd.DataFrame(rows)

def show(name, tr, days):
    if len(tr) < 12: print(f"{name:30} n={len(tr)} (too few)"); return
    s = stats(tr); ci = bootstrap_ev(tr["R"].values); yrs = tr["ts"].dt.year.nunique()
    py = "  ".join(f"{y}:{g['R'].sum():+.0f}" for y, g in tr.groupby("year"))
    flag = "  <<< +EV" if ci[0] > 0 else ""
    print(f"{name:30} n={s['n']:>3} ({s['n']/yrs:>4.0f}/yr {s['n']/(days*5/7):.2f}/day) "
          f"WR={s['WR']}% avgR={s['avgR']:+.3f} PF={s['PF']} DD={s['maxDD_R']}R CI={ci}{flag}")
    print(f"{'':30} per-yr sumR: {py}")

def main():
    d1 = load("D1"); h4 = load("H4")
    h1 = load("H1"); h1["ema200"] = h1["close"].ewm(span=200, adjust=False).mean()
    h1["atr"] = atr(h1, 14); h1["rsi"] = rsi(h1["close"], 14)
    m15 = load("M15")
    # restrict H1 signals to M15-covered span for honest fills
    start = m15["ts"].iloc[0]
    h1 = h1[h1["ts"] >= start].reset_index(drop=True)
    d1up = uptrend_on(h1, d1); h4up = uptrend_on(h1, h4)
    days = (h1["ts"].iloc[-1]-h1["ts"].iloc[0]).days
    print(f"H1 signals span {h1.ts.iloc[0].date()}→{h1.ts.iloc[-1].date()} ({days}d)  fills=M15  friction=${FRICTION}\n")

    hi = h1["high"].values; cl = h1["close"].values; em = h1["ema200"].values
    for N in (20, 30, 55):
        hh = rmax(hi, N)
        base = (cl >= np.roll(hh, 1)) & (cl > em); base[:N+1] = False
        print(f"--- H1 Donchian {N} ---")
        for label, filt in [("H1 only", base),
                            ("+D1 uptrend", base & d1up),
                            ("+D1&H4 uptrend", base & d1up & h4up)]:
            for sla, tpa, mh in [(2.0, 4.0, 48), (1.5, 3.0, 36)]:
                tr = backtest(filt, h1, m15, sla, tpa, mh)
                show(f"  {label} {sla}/{tpa}/{mh}h", tr, days)
        print()
    print("<<< +EV = bootstrap 95% CI lower bound > 0 after friction")

if __name__ == "__main__":
    main()
