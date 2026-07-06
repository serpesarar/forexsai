"""Stage 3 — friction stress + parameter-neighborhood robustness for the winner
DONCH(N)_BUY. If +EV survives 5x friction and forms a plateau (not a lucky cell),
it's deployable."""
from __future__ import annotations
import warnings; warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import swing_battery as sb
import validate
from validate import backtest_dedup
from swing_battery import load, add_indicators, stats, bootstrap_ev


def donch_buy_mask(d, N):
    up = d["close"] > d["ema200"]
    return ((d["close"] >= d["high"].rolling(N).max().shift(1)) & up).values


def main():
    d = add_indicators(load("D1")); h1 = load("H1")

    print("### Friction stress — DONCH55_BUY 2.0/4.0/20d (round-trip $ per oz)")
    mask = donch_buy_mask(d, 55)
    for fr in [0.40, 1.00, 2.00, 4.00, 8.00]:
        sb.FRICTION = fr; validate.FRICTION = fr   # backtest_dedup reads validate.FRICTION
        tr = backtest_dedup(mask, "BUY", d, h1, 2.0, 4.0, 20)
        s = stats(tr); ci = bootstrap_ev(tr["R"].values)
        print(f"  friction=${fr:<4}  n={s['n']}  WR={s['WR']}%  avgR={s['avgR']}  sumR={s['sumR']}  PF={s['PF']}  CI={ci}")
    sb.FRICTION = 0.40

    print("\n### Parameter neighborhood (Donchian N x exit) — avgR / n  [friction $0.40]")
    print(f"  {'N':>4} | " + " ".join(f"{f'{sla}/{tpa}/{md}d':>12}" for sla,tpa,md in
          [(1.5,3.0,15),(2.0,4.0,20),(2.0,3.0,20),(2.5,5.0,25)]))
    for N in [40, 50, 55, 60, 70]:
        mask = donch_buy_mask(d, N)
        cells = []
        for sla,tpa,md in [(1.5,3.0,15),(2.0,4.0,20),(2.0,3.0,20),(2.5,5.0,25)]:
            tr = backtest_dedup(mask, "BUY", d, h1, sla, tpa, md)
            s = stats(tr)
            cells.append(f"{s.get('avgR','-'):>6}/{s.get('n',0):<3}" if s['n'] else f"{'-':>10}")
        print(f"  {N:>4} | " + " ".join(f"{c:>12}" for c in cells))
    print("\n  (a robust edge shows a PLATEAU of positive avgR across N and exits, not one lucky cell)")


if __name__ == "__main__":
    main()
