"""Stage 2 — drift-control & robustness for the BUY survivors.

The battery showed DONCH20/55_BUY + RSI_MR_BUY are +EV OOS. But gold rose +157%
over the window, so we must prove the edge is NOT just buy&hold drift:
  1. DEDUP entries (one position at a time → independent trades, no clustered correlation)
  2. PER-YEAR breakdown — must survive 2022 (gold fell ~25% mid-year) & choppy years
  3. WALK-FORWARD 5 folds
  4. BUY&HOLD per-year benchmark — does the rule beat simply being long?
"""
from __future__ import annotations
import warnings; warnings.simplefilter("ignore")
import numpy as np
import pandas as pd
from swing_battery import load, add_indicators, simulate, strategies, stats, bootstrap_ev, FRICTION


def backtest_dedup(signals, side, d, h1, sl_atr, tp_atr, max_days):
    """Same as battery.backtest but ENFORCES one open position at a time:
    skip any signal whose entry falls before the previous trade's exit time."""
    rows = []
    o, a, ts = d["open"].values, d["atr"].values, d["ts"].values
    h1ts = h1["ts"].values
    idx = np.where(signals)[0]
    max_bars = max_days * 24
    busy_until = np.datetime64("1900-01-01")
    for i in idx:
        if i + 1 >= len(d) or not np.isfinite(a[i]) or a[i] <= 0:
            continue
        entry_ts = ts[i+1]
        if entry_ts < busy_until:           # still in a trade → skip (dedup)
            continue
        entry_px = o[i+1]
        risk = sl_atr * a[i]
        if side == "BUY":
            sl, tp = entry_px - risk, entry_px + tp_atr * a[i]
        else:
            sl, tp = entry_px + risk, entry_px - tp_atr * a[i]
        exit_px, bars = simulate(side, entry_px, sl, tp, entry_ts, h1, max_bars)
        # exit timestamp ≈ entry H1 index + bars
        j = np.searchsorted(h1ts, entry_ts, "left")
        busy_until = h1ts[min(j + bars, len(h1ts)-1)]
        gross = (exit_px - entry_px) if side == "BUY" else (entry_px - exit_px)
        net = gross - FRICTION
        rows.append({"ts": pd.Timestamp(entry_ts), "year": pd.Timestamp(entry_ts).year,
                     "net": net, "R": net / risk, "bars": bars, "win": net > 0})
    return pd.DataFrame(rows)


def per_year(tr):
    out = []
    for y, g in tr.groupby("year"):
        s = stats(g)
        out.append((y, s["n"], s["WR"], s["avgR"], s["sumR"]))
    return out


def gold_year_returns(d):
    d = d.copy(); d["year"] = d["ts"].dt.year
    r = {}
    for y, g in d.groupby("year"):
        r[y] = round(100*(g["close"].iloc[-1]/g["close"].iloc[0]-1), 1)
    return r


def walk_forward(tr, k=5):
    tr = tr.sort_values("ts").reset_index(drop=True)
    folds = np.array_split(tr, k)
    return [((f["ts"].iloc[0].date().isoformat() if len(f) else "-"),
             len(f), round(100*f["win"].mean(),1) if len(f) else 0,
             round(f["R"].mean(),3) if len(f) else 0,
             round(f["R"].sum(),1) if len(f) else 0) for f in folds]


def main():
    d = add_indicators(load("D1"))
    h1 = load("H1")
    sig = strategies(d)
    gyr = gold_year_returns(d)
    print("Gold per-year close-to-close return:")
    print("  " + "  ".join(f"{y}:{v:+.0f}%" for y, v in gyr.items()))
    print("  (2022 = the stress year; if the rule survives 2022 it's not just drift)\n")

    candidates = [
        ("DONCH20_BUY", 1.5, 3.0, 15),
        ("DONCH55_BUY", 1.5, 3.0, 15),
        ("DONCH55_BUY", 2.0, 4.0, 20),
        ("RSI_MR_BUY",  1.0, 2.0, 10),
    ]
    for name, sla, tpa, md in candidates:
        mask, side = sig[name]
        tr = backtest_dedup(mask, side, d, h1, sla, tpa, md)
        s = stats(tr)
        ci = bootstrap_ev(tr["R"].values)
        print("="*92)
        print(f"{name}  exit {sla}/{tpa}/{md}d  [DEDUP — one position at a time]")
        print(f"  trades={s['n']}  WR={s['WR']}%  avgR={s['avgR']}  sumR={s['sumR']}  "
              f"PF={s['PF']}  maxDD={s['maxDD_R']}R  EV95CI={ci}")
        print("  per-year:  year   n   WR    avgR    sumR   | gold yr-ret")
        for y, n, wr, ar, sr in per_year(tr):
            flag = "  <-- gold DOWN/flat" if gyr.get(y, 0) < 5 else ""
            print(f"             {y}  {n:>3}  {wr:>5}  {ar:>6}  {sr:>6}   | {gyr.get(y,'?'):>5}%{flag}")
        print("  walk-forward 5 folds (start, n, WR, avgR, sumR):")
        for f in walk_forward(tr):
            print(f"             {f}")
    print("\navgR>0 with CI lower bound>0 AND positive in gold's down/flat years = genuine edge, not drift.")


if __name__ == "__main__":
    main()
