"""HK-1 — 3 EMA (10/25/50) dizilim kesişimi (PROTOCOL.md)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import OUT, SPREAD, SYMS, ema, load, run_with_placebo, simulate


def signals(d: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    e10, e25, e50 = ema(d.close, 10), ema(d.close, 25), ema(d.close, 50)
    up = (e10 > e25) & (e25 > e50)
    dn = (e10 < e25) & (e25 < e50)
    warm = np.arange(len(d)) >= 150
    b = np.where(warm & up & ~np.r_[False, up[:-1]])[0]
    s = np.where(warm & dn & ~np.r_[False, dn[:-1]])[0]
    sig = pd.DataFrame({"i": np.r_[b, s], "dir": np.r_[np.ones(len(b)), -np.ones(len(s))].astype(int)})
    return sig.sort_values("i").reset_index(drop=True), e10, e25


def maker(d: pd.DataFrame, sym: str, exit_kind: str, e10: np.ndarray, e25: np.ndarray):
    a, sp = d.atr.values, SPREAD[sym]

    def mk(i: int, direction: int, ref):
        if exit_kind == "X1":
            if ref is None:   # kitap çıkışı: EMA10 EMA25'i ters kesince
                fn = (lambda j: e10[j] < e25[j]) if direction > 0 else (lambda j: e10[j] > e25[j])
                return simulate(d, i, direction, 2 * a[i], None, 500, sp, exit_fn=fn)
            return simulate(d, i, direction, 2 * a[i], None, ref.exit_i - ref.entry_i + 1, sp)   # süre-eşli
        if exit_kind == "X2":
            return simulate(d, i, direction, 1.5 * a[i], 3 * a[i], 60, sp)
        return simulate(d, i, direction, 3 * a[i], None, 20, sp)
    return mk


def main() -> None:
    allt = []
    for tf in ["30m", "1h"]:
        for sym in SYMS:
            d = load(sym, tf)
            sig, e10, e25 = signals(d)
            for x in ["X1", "X2", "X3"]:
                t = run_with_placebo(d, sig, sym, maker(d, sym, x, e10, e25))
                t["tf"], t["exit"] = tf, x
                allt.append(t)
                print(tf, sym, x, len(t), round(t.r.mean(), 3), round(t.d.mean(), 3), flush=True)
    pd.concat(allt).to_parquet(OUT / "hk1_trades.parquet")


if __name__ == "__main__":
    main()
