"""strike.py — NB-04 QQQ strike çekimi (0DTE çağı). python strike.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/fitil_gece_20261118/src", "research/moc_pencere_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import gece as G  # noqa: E402
import moc  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
NY = "America/New_York"
ERA = (("ESKI", "2018-04-01", "2022-10-31"), ("0DTE", "2022-11-01", "2026-12-31"))
U_LO, U_HI = 0.20, 0.45


def qqq_close() -> pd.Series:
    d = pd.read_parquet(HERE / "data/QQQ.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return d.Close.astype(float)


def trades(b: pd.DataFrame, step: int) -> pd.DataFrame:
    x = G._local(b, NY)
    x = x[(x.mn >= 900) & (x.mn <= 960)]
    q = qqq_close()
    groups = {d: g for d, g in x.groupby("day")}
    days = sorted(groups)
    rows = []
    prev_k = None
    for d in days:
        g = groups[d]
        mn = g.mn.values
        i0 = np.flatnonzero(mn == 900)
        i1 = np.flatnonzero(mn == 960)
        ts = pd.Timestamp(d)
        k_today = q.get(ts, np.nan) / g.o.values[i1[0]] if i1.size and ts in q.index else None
        if prev_k is not None and i0.size and i1.size and d.weekday() < 5 and G.nyse_ok(d):
            o, h, l, sp = g.o.values, g.h.values, g.l.values, g.sp.values
            j0, j1 = i0[0], i1[0]
            q0 = o[j0] * prev_k
            for grid, off in (("gercek", 0.0), ("plasebo", 0.5)):
                K = np.round(q0 - off) + off
                u = abs(q0 - K)
                if not (U_LO <= u <= U_HI):
                    continue
                side = 1 if K > q0 else -1
                tp = K / prev_k
                ent = o[j0] + sp[j0] if side > 0 else o[j0]
                px = None
                for j in range(j0, j1):
                    if side > 0 and h[j] >= tp:
                        px = max(tp, o[j])
                        break
                    if side < 0 and l[j] + sp[j] <= tp:
                        px = min(tp, o[j] + sp[j])
                        break
                hit = px is not None
                if px is None:
                    px = o[j1] if side > 0 else o[j1] + sp[j1]
                net = side * (px / ent - 1) * 1e4
                rows.append({"d": d, "grid": grid, "side": side, "u": u, "net": net, "hit": hit, "cuma": d.weekday() == 4,
                             "n15": net - 0.5 * (sp[j0] + sp[j1]) / ent * 1e4})
        prev_k = k_today if k_today and np.isfinite(k_today) else None
    df = pd.DataFrame(rows)
    df["era"] = np.select([pd.to_datetime(df.d) <= pd.Timestamp(ERA[0][2])], ["ESKI"], "0DTE")
    df.loc[pd.to_datetime(df.d) < pd.Timestamp(ERA[0][1]), "era"] = "DIS"
    return df


def boot(a: np.ndarray, b: np.ndarray, n: int = 4000) -> float:
    r = np.random.default_rng(11)
    return float((r.choice(a, (n, len(a))).mean(1) - r.choice(b, (n, len(b))).mean(1) > 0).mean())


def summ(df: pd.DataFrame) -> dict:
    out = {}
    for e in ("ESKI", "0DTE"):
        for cn, cm in (("cuma_disi", False), ("cuma", True)):
            z = df[(df.era == e) & (df.cuma == cm)]
            g, p = z[z.grid == "gercek"], z[z.grid == "plasebo"]
            if len(g) < 10 or len(p) < 10:
                continue
            out[f"{e}_{cn}"] = {"n": int(len(g)), "gercek": round(float(g.net.mean()), 2), "plasebo": round(float(p.net.mean()), 2),
                                "fark": round(float(g.net.mean() - p.net.mean()), 2), "s15": round(float(g.n15.mean()), 2),
                                "dokunus_gercek": round(float(g.hit.mean()), 3), "dokunus_plasebo": round(float(p.hit.mean()), 3),
                                "P": round(boot(g.net.values, p.net.values), 4)}
    return out


def main() -> None:
    out = {}
    for src, (b, st) in {"duka": (G.ndx_bars(), 60), "mt5": moc.mt5_2m()}.items():
        df = trades(b, st)
        df.to_parquet(HERE / f"results/strike_{src}.parquet")
        out[src] = summ(df)
        for k, v in out[src].items():
            print(src, k, v)
    (HERE / "results/strike.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
