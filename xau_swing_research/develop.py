"""Stage 4 — raise frequency without breaking the edge.

Two levers vs the D1 Donchian winner:
  (A) move the breakout to H4 (≈6x more bars) with a D1-uptrend confluence filter
  (B) add a 2nd entry: oversold-DIP buy inside an established uptrend (buys weakness;
      complements the breakout which buys strength)
Then build a COMBINED book (union, deduped to one position at a time) and report
trades/year + edge. Same rigor: dedup, per-year, OOS, friction, bootstrap.
"""
from __future__ import annotations
import warnings; warnings.simplefilter("ignore")
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as _swv
from swing_battery import load, rsi, atr, simulate, stats, bootstrap_ev

FRICTION = 0.40


def roll_max(s, w):
    a = np.asarray(s, float); o = np.full(len(a), np.nan)
    if len(a) >= w: o[w-1:] = _swv(a, w).max(axis=1)
    return o

def roll_min(s, w):
    a = np.asarray(s, float); o = np.full(len(a), np.nan)
    if len(a) >= w: o[w-1:] = _swv(a, w).min(axis=1)
    return o


def prep(tf, hours_per_bar):
    d = load(tf)
    d["ema200"] = d["close"].ewm(span=200, adjust=False).mean()
    d["ema50"] = d["close"].ewm(span=50, adjust=False).mean()
    d["rsi"] = rsi(d["close"], 14)
    d["atr"] = atr(d, 14)
    d["hpb"] = hours_per_bar
    return d


def d1_uptrend_flag(d_tf, d1):
    """Map D1 'close>EMA200' onto the tf bars by timestamp (last CLOSED D1 bar)."""
    d1up = (d1["close"].values > d1["close"].ewm(span=200, adjust=False).mean().values)
    j = np.searchsorted(d1["ts"].values, d_tf["ts"].values, side="right") - 1
    return np.where(j >= 0, d1up[j.clip(min=0)], False)


def gen_entries(mask, d, h1, sl_atr, tp_atr, max_hold_bars):
    """Yield deduped trades for one rule on timeframe d (fills/walk on h1)."""
    o, a, ts = d["open"].values, d["atr"].values, d["ts"].values
    hpb = int(d["hpb"].iloc[0])
    h1ts = h1["ts"].values
    idx = np.where(mask)[0]
    rows, busy = [], np.datetime64("1900-01-01")
    max_h1 = max_hold_bars * hpb
    for i in idx:
        if i+1 >= len(d) or not np.isfinite(a[i]) or a[i] <= 0: continue
        ets = ts[i+1]
        if ets < busy: continue
        ep = o[i+1]; risk = sl_atr*a[i]
        sl, tp = ep-risk, ep+tp_atr*a[i]
        xpx, bars = simulate("BUY", ep, sl, tp, ets, h1, max_h1)
        j = np.searchsorted(h1ts, ets, "left")
        busy = h1ts[min(j+bars, len(h1ts)-1)]
        net = (xpx-ep) - FRICTION
        rows.append({"ts": pd.Timestamp(ets), "year": pd.Timestamp(ets).year,
                     "net": net, "R": net/risk, "bars": bars, "win": net > 0})
    return pd.DataFrame(rows)


def show(name, tr):
    if len(tr) < 8:
        print(f"{name:34} n={len(tr)} (too few)"); return
    s = stats(tr); ci = bootstrap_ev(tr["R"].values)
    yrs = tr["ts"].dt.year.nunique()
    py = "  ".join(f"{y}:{g['R'].sum():+.0f}" for y, g in tr.groupby("year"))
    flag = " <<<" if ci[0] > 0 else ""
    print(f"{name:34} n={s['n']:>3} ({s['n']/yrs:.0f}/yr) WR={s['WR']}% avgR={s['avgR']:+.3f} "
          f"PF={s['PF']} DD={s['maxDD_R']}R CI={ci}{flag}")
    print(f"{'':34} per-yr sumR: {py}")


def main():
    d1 = prep("D1", 24)
    h4 = prep("H4", 4)
    h1 = load("H1")
    d1up_on_h4 = d1_uptrend_flag(h4, d1)
    print(f"D1={len(d1)}  H4={len(h4)}  H1={len(h1)}   friction=${FRICTION}\n")

    # ---- (A) H4 Donchian breakout + D1 confluence ----
    print("=== (A) H4 Donchian breakout, D1-uptrend confluence ===")
    for N in (20, 30, 55):
        hh = roll_max(h4["high"].values, N)
        mask = (h4["close"].values >= np.roll(hh, 1)) & (h4["close"].values > h4["ema200"].values) & d1up_on_h4
        mask[:N+1] = False
        for sla, tpa, mh in [(2.0, 4.0, 30), (1.5, 3.0, 24)]:
            tr = gen_entries(mask, h4, h1, sla, tpa, mh)
            show(f"H4_DONCH{N} {sla}/{tpa}/{mh}b", tr)

    # ---- (B) H4 oversold-dip in uptrend ----
    print("\n=== (B) H4 oversold-DIP buy inside uptrend (RSI dip + bullish bar) ===")
    rsi_v = h4["rsi"].values; cl = h4["close"].values; op = h4["open"].values
    for thr in (35, 40):
        mask = (cl > h4["ema200"].values) & d1up_on_h4 & (rsi_v < thr) & (cl > op)
        for sla, tpa, mh in [(1.5, 3.0, 24), (2.0, 4.0, 30)]:
            tr = gen_entries(mask, h4, h1, sla, tpa, mh)
            show(f"H4_DIP<{thr} {sla}/{tpa}/{mh}b", tr)

    # ---- (C) Combined book: D1-Donch + H4-Donch + H4-dip, union deduped ----
    print("\n=== (C) COMBINED book (D1 Donch55 + H4 Donch30 + H4 dip<40), one position at a time ===")
    # D1 breakout
    hhd = roll_max(d1["high"].values, 55)
    md = (d1["close"].values >= np.roll(hhd, 1)) & (d1["close"].values > d1["ema200"].values); md[:56] = False
    td = gen_entries(md, d1, h1, 2.0, 4.0, 20); td["src"] = "D1brk"
    # H4 breakout
    hh4 = roll_max(h4["high"].values, 30)
    m4 = (h4["close"].values >= np.roll(hh4, 1)) & (h4["close"].values > h4["ema200"].values) & d1up_on_h4; m4[:31] = False
    t4 = gen_entries(m4, h4, h1, 2.0, 4.0, 30); t4["src"] = "H4brk"
    # H4 dip
    mdip = (cl > h4["ema200"].values) & d1up_on_h4 & (rsi_v < 40) & (cl > op)
    tdip = gen_entries(mdip, h4, h1, 1.5, 3.0, 24); tdip["src"] = "H4dip"

    allt = pd.concat([td, t4, tdip]).sort_values("ts").reset_index(drop=True)
    # re-dedup across sources (one position at a time): approximate via 5-day lockout after entry
    kept, busy = [], pd.Timestamp("1900-01-01")
    for _, r in allt.iterrows():
        if r["ts"] < busy: continue
        kept.append(r); busy = r["ts"] + pd.Timedelta(hours=int(r["bars"]) )  # bars are H1 → hours
    comb = pd.DataFrame(kept)
    show("COMBINED", comb)
    print("\n  <<< = bootstrap 95% CI lower bound > 0 after friction")


if __name__ == "__main__":
    main()
