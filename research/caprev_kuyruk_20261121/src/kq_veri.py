"""kq_veri.py — KQ-01 (PROTOCOL.md): her CAPREV olayı için kapanış kapanış yol verisi (s = 0…5) + 3×dvol stop yolu.

python kq_veri.py → cache/yollar.pkl  (liste: olay sözlükleri)
Olay tanımı ve sonuç hesabı caprev_derin_20261120/src/cd_veri.py ile birebir (X_5_3.0_kar tutarlılık denetimi main'de).
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/caprev_derin_20261120/src"))
import cd_veri as V  # noqa: E402

M, G = V.M, V.G
STOP_K = 3.0
MAXS = 5
DAILY = {n: V.daily(n) for n in V.ALL}
R1D = {n: DAILY[n].Close.pct_change() for n in V.US}


def _last_le(s: pd.Series, d: pd.Timestamp, strict: bool) -> float:
    k = int(s.index.searchsorted(d, side="left" if strict else "right")) - 1
    return float(s.iloc[k]) if 0 <= k < len(s) else np.nan


def path_feats(idx: str, d0: pd.Timestamp, dates: list[pd.Timestamp], cl: list[float], E: float, dvol: float) -> list[dict]:
    """Her kapanış s için karar anında bilinen yol özellikleri."""
    x = DAILY[idx]
    us = idx in V.US
    v_entry = V._prev(V.VIXS, d0)
    out = []
    for s, d in enumerate(dates):
        d = pd.Timestamp(d).normalize()
        row = x.loc[d] if d in x.index else None
        k = int(x.index.searchsorted(d))
        prevrow = x.iloc[k - 1] if k >= 1 else None
        vix = _last_le(V.VIXS, d, strict=not us)
        v3 = _last_le(V.VIX3M, d, strict=not us) if d >= pd.Timestamp("2006-07-18") else np.nan
        if us:
            br = sum(1 for u in V.US if u != idx and d in R1D[u].index and R1D[u].loc[d] <= M.STRESS_R1)
        else:
            br = sum(1 for u in V.US if _last_le(R1D[u].dropna(), d, True) <= M.STRESS_R1)
        f = {"s": s, "z": (cl[s] / E - 1) / dvol, "dz": ((cl[s] - cl[s - 1]) / E) / dvol if s else (cl[0] / E - 1) / dvol,
             "vix": vix, "vixchg": vix / v_entry - 1 if np.isfinite(v_entry) and v_entry > 0 else np.nan,
             "term": vix / v3 if np.isfinite(v3) and v3 > 0 else np.nan, "br": br,
             "clv": np.nan, "ll": False, "nobounce": bool(s >= 1 and cl[s] < cl[s - 1])}
        if row is not None and float(row.High) > float(row.Low):
            f["clv"] = (float(row.Close) - float(row.Low)) / (float(row.High) - float(row.Low))
        if s >= 1 and row is not None and prevrow is not None:
            f["ll"] = bool(float(row.Low) < float(prevrow.Low))
        out.append(f)
    return out


def daily_paths(name: str, start: str, end: str, set_name: str) -> list[dict]:
    x = DAILY[name]
    O, H, L, C = (x[c].values for c in ("Open", "High", "Low", "Close"))
    days = list(x.index)
    a, b = pd.Timestamp(start), pd.Timestamp(end)
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
        bid = lambda p: p * (1 - V.COST_BP / 1e4)  # noqa: E731
        fin = [M.FIN * (days[i + s] - d).days for s in range(6)]
        cl = [bid(C[i + s]) for s in range(6)]
        res = [(cl[s] / E - 1) * 1e4 - fin[s] for s in range(6)]
        sl = E * (1 - STOP_K * dvol)
        stop_s, stop_res = None, None
        if L[i] <= sl:
            stop_s, stop_res = 0, (bid(sl) / E - 1) * 1e4
        else:
            for s in range(1, 6):
                if O[i + s] <= sl or L[i + s] <= sl:
                    stop_s, stop_res = s, (bid(min(sl, O[i + s])) / E - 1) * 1e4 - fin[s]
                    break
        sl1 = E * (1 - dvol)
        base = (bid(sl1) / E - 1) * 1e4 if L[i] <= sl1 else res[0]
        dates = days[i:i + 6]
        out.append({"set": set_name, "idx": name, "feed": f"G_{name}", "d": d, "E": E, "dvol": dvol, "base": base,
                    "cl": cl, "res": res, "stop_s": stop_s, "stop_res": stop_res,
                    "pf": path_feats(name, d, dates, cl, E, dvol)})
    return out


def feed_paths(feed: str) -> list[dict]:
    F = M.Feed(feed)
    idx = V.FEED_IDX[feed]
    out = []
    for ev in F.events():
        tr = F.trade_row(ev)
        if tr is None:
            continue
        cps = [c for c in F.checkpoints(ev) if c[0].endswith("c")]
        pts = []
        for lab, uu, dd in cps:
            got = F.px_at(uu)
            if got is None:
                break
            pts.append((got[0], got[1], dd))
        if len(pts) < 2:
            continue
        pts = pts[:MAXS + 1]
        i0, E, dvol, d0 = ev["i0"], ev["E"], ev["dvol"], ev["d"]
        cl = [p[1] for p in pts]
        res = [(cl[s] / E - 1) * 1e4 - M.FIN * (pts[s][2] - d0).days for s in range(len(pts))]
        sl = E * (1 - STOP_K * dvol)
        lo = F.l[i0:pts[-1][0]]
        stop_s, stop_res = None, None
        if (lo <= sl).any():
            js = int(np.argmax(lo <= sl))
            gi = i0 + js
            stop_s = next(s for s in range(len(pts)) if gi < pts[s][0])
            stop_res = (min(sl, F.o[gi]) / E - 1) * 1e4 - M.FIN * (F.d[gi] - d0).days
        dates = [pd.Timestamp(p[2]) for p in pts]
        out.append({"set": feed, "idx": idx, "feed": feed, "d": pd.Timestamp(d0), "E": E, "dvol": dvol, "base": tr["base"],
                    "cl": cl, "res": res, "stop_s": stop_s, "stop_res": stop_res,
                    "pf": path_feats(idx, pd.Timestamp(d0), dates, cl, E, dvol)})
    return out


def main() -> None:
    P = []
    for n in V.ALL:
        P += daily_paths(n, "1990-01-01", "2015-12-31", "KESIF")
        P += daily_paths(n, "2016-01-01", "2026-12-31", "G2016")
    for f in V.FEED_IDX:
        P += feed_paths(f)
    with open(HERE / "cache/yollar.pkl", "wb") as fh:
        pickle.dump(P, fh)
    print(len(P), "olay")


if __name__ == "__main__":
    main()
