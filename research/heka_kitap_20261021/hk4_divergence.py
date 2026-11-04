"""HK-4 — RSI Sınıf A diverjansı giriş olarak (PROTOCOL.md). Yapısal kontrol: aynı yeni-uç yapısı, diverjans YOK."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import OUT, SPREAD, SYMS, load, rsi, run_with_placebo, simulate

W, GAP_MIN, GAP_MAX, DIV_PTS = 3, 5, 60, 2.0


def events(d: pd.DataFrame) -> pd.DataFrame:
    h, l, r = d.high.values, d.low.values, rsi(d.close)
    piv = {1: [], -1: []}            # 1: dipler (boğa), -1: tepeler (ayı)
    rows = []
    for t in range(2 * W + 150, len(d)):
        k = t - W
        for side, px, ok in ((1, l[k], l[k] == l[k - W:k + W + 1].min()), (-1, h[k], h[k] == h[k - W:k + W + 1].max())):
            if not ok or not np.isfinite(r[k]):
                continue
            prev = [p for p in piv[side] if GAP_MIN <= k - p[0] <= GAP_MAX]
            if prev:
                kp, pp, rp = prev[-1]
                new_extreme = px < pp if side > 0 else px > pp
                if new_extreme:
                    div = (r[k] >= rp + DIV_PTS) if side > 0 else (r[k] <= rp - DIV_PTS)
                    conf = (r[k] < rp) if side > 0 else (r[k] > rp)
                    if div or conf:
                        rows.append(dict(i=t, dir=side, kind="div" if div else "nodiv",
                                         extreme_prev=(rp < 30) if side > 0 else (rp > 70)))
            piv[side].append((k, px, r[k]))
            piv[side] = [p for p in piv[side] if k - p[0] <= GAP_MAX]
    return pd.DataFrame(rows)


def main() -> None:
    out = []
    for tf in ["30m", "1h"]:
        for sym in SYMS:
            d = load(sym, tf)
            ev = events(d)
            a, sp = d.atr.values, SPREAD[sym]
            mks = {"X2": lambda i, direction, ref: simulate(d, i, direction, 1.5 * a[i], 3 * a[i], 60, sp),
                   "X3": lambda i, direction, ref: simulate(d, i, direction, 3 * a[i], None, 20, sp)}
            for var in ["V1", "V2"]:
                e = ev if var == "V1" else ev[ev.extreme_prev]
                for kind in ["div", "nodiv"]:
                    sig = e[e.kind == kind][["i", "dir"]]
                    for x, mk in mks.items():
                        t = run_with_placebo(d, sig, sym, mk)
                        t["tf"], t["exit"], t["var"], t["kind"] = tf, x, var, kind
                        out.append(t)
            res = pd.concat(out[-8:])
            print(tf, sym, res.groupby(["var", "kind", "exit", "dir"]).r.agg(["size", "mean"]).round(3).unstack("dir").to_string(),
                  flush=True)
    pd.concat(out).to_parquet(OUT / "hk4_trades.parquet")


if __name__ == "__main__":
    main()
