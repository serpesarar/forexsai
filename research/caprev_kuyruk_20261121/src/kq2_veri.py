"""kq2_veri.py — KQ-02: stop takvimini serbestçe değiştirebilmek için ham yol dizileri (segment s = kapanış s'ye kadar olan barlar).

python kq2_veri.py → cache/yollar2.pkl
Daily: segment s tek "bar" (O, L); D0 barının açılışı yok sayılır (cd_veri walk ile birebir). Feed: [i0, kapanış0), [kapanış0, kapanış1)…
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
import kq_veri as Q  # noqa: E402

V, M = Q.V, Q.M
FEEDS = dict(V.FEED_IDX) | {"EET30": "NDX", "NQ": "NDX", "MT5_GER40": "GDAXI"}


def daily_paths(name: str, start: str, end: str, set_name: str) -> list[dict]:
    x = Q.DAILY[name]
    O, H, L, C = (x[c].values for c in ("Open", "High", "Low", "Close"))
    days = list(x.index)
    a, b = pd.Timestamp(start), pd.Timestamp(end)
    fac = 1 - V.COST_BP / 1e4
    out = []
    for i in range(22, len(days) - 6):
        d = days[i]
        if not (a <= d <= b) or d.weekday() > 3 or (d - days[i - 1]).days > 4:
            continue
        rets = C[i - 21:i] / C[i - 22:i - 1] - 1
        r1, r5, dvol = rets[-1], C[i - 1] / C[i - 6] - 1, float(np.std(rets[-20:], ddof=1))
        v = V._prev(V.VIXS, d)
        if not np.isfinite(v) or v < M.VIX_MIN or not (r1 <= M.STRESS_R1 or r5 <= M.STRESS_R5) or L[i] >= L[i - 1]:
            continue
        E = min(O[i], L[i - 1]) * (1 + V.COST_BP / 1e4)
        dd = np.array([(days[i + s] - d).days for s in range(6)])
        cl = [C[i + s] * fac for s in range(6)]
        res = [(cl[s] / E - 1) * 1e4 - M.FIN * dd[s] for s in range(6)]
        op = np.array([np.inf] + [O[i + s] for s in range(1, 6)])
        out.append({"set": set_name, "idx": name, "feed": f"G_{name}", "d": d, "E": E, "dvol": dvol, "cl": cl, "res": res,
                    "lo": np.array([L[i + s] for s in range(6)]), "op": op, "dd": dd, "seg": list(range(1, 7)), "fac": fac,
                    "pf": Q.path_feats(name, d, days[i:i + 6], cl, E, dvol)})
    return out


def feed_paths(feed: str) -> list[dict]:
    F = M.Feed(feed)
    idx = FEEDS[feed]
    out = []
    for ev in F.events():
        tr = F.trade_row(ev)
        if tr is None:
            continue
        pts = []
        for lab, uu, dd in [c for c in F.checkpoints(ev) if c[0].endswith("c")]:
            got = F.px_at(uu)
            if got is None:
                break
            pts.append((got[0], got[1], dd))
        if len(pts) < 2:
            continue
        pts = pts[:Q.MAXS + 1]
        i0, E, dvol, d0 = ev["i0"], ev["E"], ev["dvol"], ev["d"]
        cl = [p[1] for p in pts]
        res = [(cl[s] / E - 1) * 1e4 - M.FIN * (pts[s][2] - d0).days for s in range(len(pts))]
        sl_ = slice(i0, pts[-1][0])
        dd = np.array([(x - d0).days for x in F.d[sl_]])
        out.append({"set": feed, "idx": idx, "feed": feed, "d": pd.Timestamp(d0), "E": E, "dvol": dvol, "base_motor": tr["base"],
                    "sp_bp": float(F.sp[i0] / E * 1e4), "e_opt": float(F.c[i0 - 1]),
                    "cl": cl, "res": res, "lo": F.l[sl_].copy(), "op": F.o[sl_].copy(), "dd": dd,
                    "seg": [p[0] - i0 for p in pts], "fac": 1.0,
                    "pf": Q.path_feats(idx, pd.Timestamp(d0), [pd.Timestamp(p[2]) for p in pts], cl, E, dvol)})
    return out


def main() -> None:
    P = []
    for n in V.ALL:
        P += daily_paths(n, "1990-01-01", "2015-12-31", "KESIF")
        P += daily_paths(n, "2016-01-01", "2026-12-31", "G2016")
    for f in FEEDS:
        P += feed_paths(f)
    with open(HERE / "cache/yollar2.pkl", "wb") as fh:
        pickle.dump(P, fh)
    print(len(P), "olay", {f: sum(e["feed"] == f for e in P) for f in FEEDS})


if __name__ == "__main__":
    main()
