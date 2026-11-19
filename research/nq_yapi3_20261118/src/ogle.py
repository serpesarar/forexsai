"""ogle.py — OS öğle sıkışması kırılımı (Duka NDX 1m, MT5 NAS100 2m). python ogle.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/fitil_gece_20261118/src", "research/moc_pencere_20261118/src", "research/nq_akis_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import gece as G  # noqa: E402
import moc  # noqa: E402
import ihale as I  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
NY = "America/New_York"
L0, L1, B1, XM, S_MAX = 720, 810, 955, 960, 0.6


def table(b: pd.DataFrame) -> pd.DataFrame:
    x = G._local(b, NY)
    x = x[(x.mn >= L0) & (x.mn <= XM + 5)]
    rows = []
    for d, g in x.groupby("day"):
        if d.weekday() >= 5 or not G.nyse_ok(d):
            continue
        mn, o, h, l, c, sp = (g[k].values for k in ("mn", "o", "h", "l", "c", "sp"))
        lw = (mn >= L0) & (mn < L1)
        ex = np.flatnonzero(mn >= XM)
        if lw.sum() < 5 or not ex.size:
            continue
        hi, lo = h[lw].max(), l[lw].min()
        j = ex[0]
        brk = np.flatnonzero((mn >= L1) & (mn <= B1) & ((c > hi) | (c < lo)))
        row = {"d": d, "w": (hi - lo) / c[lw][-1], "side": 0, "net": np.nan, "ayna": np.nan, "n15": np.nan}
        if brk.size and brk[0] + 1 < j:
            k = brk[0]
            side = 1 if c[k] > hi else -1
            e = k + 1
            ent = o[e] + sp[e] if side > 0 else o[e]
            out = o[j] if side > 0 else o[j] + sp[j]
            net = side * (out / ent - 1) * 1e4
            ent2 = o[e] + sp[e] if side < 0 else o[e]
            out2 = o[j] if side < 0 else o[j] + sp[j]
            row.update(side=side, net=net, ayna=-side * (out2 / ent2 - 1) * 1e4, n15=net - 0.5 * (sp[e] + sp[j]) / ent * 1e4)
        rows.append(row)
    t = pd.DataFrame(rows)
    t["s"] = t.w / t.w.shift(1).rolling(60, min_periods=40).median()
    t["era"] = [I.era_of(z) for z in t.d]
    return t


def boot(a: np.ndarray, b: np.ndarray) -> float:
    r = np.random.default_rng(21)
    return float((r.choice(a, (4000, len(a))).mean(1) - r.choice(b, (4000, len(b))).mean(1) > 0).mean())


def summ(t: pd.DataFrame) -> dict:
    out = {}
    for e in ("ESKI", "KESIF", "TEST"):
        z = t[(t.era == e) & t.net.notna() & t.s.notna()]
        sq, al = z[z.s <= S_MAX], z
        if len(sq) < 10:
            continue
        out[e] = {"n_sikisik": int(len(sq)), "n_tum": int(len(al)), "sikisik": round(float(sq.net.mean()), 1), "taban": round(float(al.net.mean()), 1),
                  "fark": round(float(sq.net.mean() - al.net.mean()), 1), "s15": round(float(sq.n15.mean()), 1),
                  "isabet": round(float((sq.net > 0).mean()), 3), "P": round(boot(sq.net.values, al.net.values), 4),
                  "ayna_sikisik": round(float(sq.ayna.mean()), 1), "kirilim_orani_sikisik": round(float(len(sq) / max(1, (t[(t.era == e) & (t.s <= S_MAX)]).shape[0])), 3)}
    return out


def main() -> None:
    res = {}
    for src, (b, st) in {"duka": (G.ndx_bars(), 60), "mt5": moc.mt5_2m()}.items():
        t = table(b)
        t.to_parquet(HERE / f"results/ogle_{src}.parquet")
        res[src] = summ(t)
        for k, v in res[src].items():
            print(src, k, v)
    (HERE / "results/ogle.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
