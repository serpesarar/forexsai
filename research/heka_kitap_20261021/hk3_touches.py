"""HK-3 — "S/R ne kadar çok test edilirse kırılma olasılığı o kadar yüksek" (PROTOCOL.md)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import OUT, SPLIT, SPREAD, SYMS, load, run_with_placebo, simulate

W, CLUSTER_ATR, MAX_AGE, BREAK_ATR, COOLDOWN = 3, 0.5, 300, 0.1, 12
APPROACH_ATR, APPROACH_H = 0.3, 12


def bucket(n: int) -> str:
    return "2" if n == 2 else ("3" if n == 3 else "4+")


def scan(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    h, l, c, a = d.high.values, d.low.values, d.close.values, d.atr.values
    lv: list[dict] = []
    brk, appr = [], []
    for t in range(2 * W + 150, len(d)):
        k = t - W                                    # bu barda teyit edilen pivot adayı
        for px, is_hi in ((h[k], h[k] == h[k - W:k + W + 1].max()), (l[k], l[k] == l[k - W:k + W + 1].min())):
            if not is_hi:
                continue
            near = [x for x in lv if abs(x["p"] - px) <= CLUSTER_ATR * a[t]]
            if near:
                x = min(near, key=lambda z: abs(z["p"] - px))
                x["p"] = (x["p"] * x["n"] + px) / (x["n"] + 1)
                x["n"] += 1
            else:
                lv.append(dict(p=px, n=1, born=t, ev=-10**9))
        lv = [x for x in lv if t - x["born"] <= MAX_AGE]
        for x in lv:
            if x["n"] < 2:
                continue
            p, thr = x["p"], BREAK_ATR * a[t]
            if t - x["ev"] >= COOLDOWN:
                if c[t] > p + thr and c[t - 1] <= p:
                    brk.append(dict(i=t, dir=1, touches=x["n"]))
                    x["ev"] = t
                elif c[t] < p - thr and c[t - 1] >= p:
                    brk.append(dict(i=t, dir=-1, touches=x["n"]))
                    x["ev"] = t
            dist, pdist = abs(c[t] - p), abs(c[t - 1] - p)
            if dist <= APPROACH_ATR * a[t] < pdist and t + APPROACH_H < len(d):
                side = 1 if c[t - 1] < p else -1          # aşağıdan yaklaşma → yukarı kırılım arar
                fut = c[t + 1:t + 1 + APPROACH_H]
                hit = np.any(fut > p + thr) if side > 0 else np.any(fut < p - thr)
                appr.append(dict(i=t, ts=d.ts.iloc[t], touches=x["n"], broke=bool(hit)))
    return pd.DataFrame(brk), pd.DataFrame(appr)


def main() -> None:
    trades, approaches = [], []
    for tf in ["30m", "1h"]:
        for sym in SYMS:
            d = load(sym, tf)
            brk, appr = scan(d)
            a, sp = d.atr.values, SPREAD[sym]
            mk = lambda i, direction, ref: simulate(d, i, direction, a[i], a[i], 24, sp)   # noqa: E731
            for b in ["2", "3", "4+"]:
                sig = brk[brk.touches.map(bucket) == b][["i", "dir"]]
                t = run_with_placebo(d, sig, sym, mk)
                t["tf"], t["exit"], t["bucket"] = tf, "race1", b
                trades.append(t)
            appr["sym"], appr["tf"], appr["bucket"] = sym, tf, appr.touches.map(bucket)
            appr["period"] = np.where(appr.ts < SPLIT, "dev", "test")
            approaches.append(appr)
            r = pd.concat(trades[-3:])
            print(tf, sym, len(brk), r.groupby("bucket").agg(n=("r", "size"), R=("r", "mean"), d=("d", "mean")).round(3).to_dict(),
                  appr.groupby("bucket").broke.mean().round(3).to_dict(), flush=True)
    pd.concat(trades).to_parquet(OUT / "hk3_trades.parquet")
    pd.concat(approaches).to_parquet(OUT / "hk3_approach.parquet")


if __name__ == "__main__":
    main()
