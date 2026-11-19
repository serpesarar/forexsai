"""hp.py — HP aynı saat diliminin sürekliliği (HKS 2010). python hp.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/fitil_gece_20261118/src", "research/fitil_kesisim_20261118/src", "research/ndx_tf_yapilandirma_20261117/src"):
    sys.path.insert(0, str(ROOT / p))
import gece as G  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402
import kaynak  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
NY = "America/New_York"
MIN = [600, 660, 720, 780, 840, 900, 960]
ERAS = (("H1_2016_2018", "2016-01-01", "2018-04-30"), ("ESKI_2018_2021", "2018-05-01", "2021-10-31"), ("YENI_2021_2026", "2021-11-01", "2026-12-31"))


def h1_bars() -> pd.DataFrame:
    h = pd.read_csv(ROOT / "research/c1_turev_20261105/data/mt5/NAS100_H1.csv.gz")
    t = kaynak.server_to_utc(h["t"].to_numpy())
    b = pd.DataFrame({"t": t.astype(np.int64), "o": h.o, "h": h.h, "l": h.l, "c": h.c, "sp": np.where(h.sp > 0, h.sp * 0.1, 1.5)})
    return b[b.t >= int(pd.Timestamp("2016-01-01", tz=NY).timestamp())].reset_index(drop=True)


def grid(b: pd.DataFrame, step: int) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, np.ndarray]:
    dp = G.day_prices(b, NY, MIN, step)
    ok = np.all([np.isfinite(dp[f"o{m}"]) for m in MIN], axis=0)
    dp = dp[ok]
    dp = dp[[pd.Timestamp(d).dayofweek < 5 and G.nyse_ok(d) for d in dp.index]]
    P = np.stack([dp[f"o{m}"].values for m in MIN], 1)
    S = np.stack([dp[f"s{m}"].values for m in MIN], 1)
    R = P[:, 1:] / P[:, :-1] - 1
    return pd.to_datetime(dp.index), P, S, R


def nets(P: np.ndarray, S: np.ndarray, d: int, j: int, side: int) -> float:
    if side > 0:
        return (P[d, j + 1] / (P[d, j] + S[d, j]) - 1) * 1e4
    return -((P[d, j + 1] + S[d, j + 1]) / P[d, j] - 1) * 1e4


def run(b: pd.DataFrame, step: int, L: int, mode: str, shift: int = 0) -> pd.DataFrame:
    idx, P, S, R = grid(b, step)
    rows = []
    for d in range(L, len(idx)):
        s = R[d - L:d].mean(0)
        if shift:
            s = np.roll(s, shift)
        if mode == "P1":
            v = [nets(P, S, d, j, 1 if s[j] > 0 else -1) for j in range(6)]
            rows.append({"d": idx[d], "net": float(np.mean(v))})
        else:
            jb, jw = int(np.argmax(s)), int(np.argmin(s))
            rows.append({"d": idx[d], "net": 0.5 * (nets(P, S, d, jb, 1) + nets(P, S, d, jw, -1))})
    return pd.DataFrame(rows)


def boot(v: np.ndarray, w: np.ndarray | None = None) -> float:
    r = np.random.default_rng(5)
    a = r.choice(v, (4000, len(v))).mean(1)
    if w is None:
        return float((a > 0).mean())
    return float((a - r.choice(w, (4000, len(w))).mean(1) > 0).mean())


def main() -> None:
    RES.mkdir(exist_ok=True)
    feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_NAS100_H1": (h1_bars(), 3600), "MT5_US500": (KD.mt5_m30("US500", "2018-06-01"), 1800),
             "MT5_US30": (KD.mt5_m30("US30"), 1800), "MT5_US2000": (KD.mt5_m30("US2000"), 1800)}
    out = {}
    for fn, (b, st) in feeds.items():
        for nm, L, mode in (("P1", 20, "P1"), ("P2", 20, "P2"), ("P3", 40, "P1")):
            real = run(b, st, L, mode)
            pl = run(b, st, L, mode, shift=3)
            rec = {}
            for e, a, z in ERAS:
                m, mp = (real.d >= a) & (real.d <= z), (pl.d >= a) & (pl.d <= z)
                if m.sum() < 60:
                    continue
                v, w = real.net[m].values, pl.net[mp].values
                rec[e] = {"gun": int(m.sum()), "gercek": round(float(v.mean()), 2), "plasebo": round(float(w.mean()), 2),
                          "fark": round(float(v.mean() - w.mean()), 2), "P_net": round(boot(v), 4), "P_fark": round(boot(v, w), 4)}
            out[f"{fn}_{nm}"] = rec
            print(fn, nm, rec, flush=True)
    (RES / "hp.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
