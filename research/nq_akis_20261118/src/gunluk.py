"""gunluk.py — NA-01 (oynaklık hedefli fon akışı) + NA-02 (varyans primi). python gunluk.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/ndx_ath_20261118/src"))
import ath  # noqa: E402

lib = ath.lib
HERE = Path(__file__).resolve().parents[1]
DATA, RES = HERE / "data", HERE / "results"
TEST0 = pd.Timestamp("2021-11-01")
COST = 2.0


def load(name: str) -> pd.Series:
    d = pd.read_parquet(DATA / f"{name}.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return d["Close"].astype(float).dropna()


def frame(px: pd.Series) -> pd.DataFrame:
    x = pd.DataFrame({"c": px})
    lr = np.log(x.c).diff()
    x["rv20"] = lr.rolling(20).std() * np.sqrt(252)
    x["E"] = np.minimum(1.5, 0.15 / x.rv20)
    x["dE5"] = x.E - x.E.shift(5)
    x["r5"] = x.c / x.c.shift(5) - 1
    days = x.index.to_series()
    for h in (5, 20):
        cal = (days.shift(-h) - days).dt.days.values
        x[f"f{h}"] = (x.c.shift(-h) / x.c - 1) * 1e4
        x[f"fin{h}"] = lib.FIN_BP_PER_DAY * cal
    return x


def cell(x: pd.DataFrame, m: pd.Series, h: int, side: int) -> dict:
    z = x.dropna(subset=[f"f{h}"])
    mm = m.reindex(z.index).fillna(False).values.astype(bool)
    f = z[f"f{h}"].values
    if mm.sum() < 5:
        return {"n": int(mm.sum())}
    net = side * f - COST - (z[f"fin{h}"].values if side > 0 else 0)
    diff = side * (f[mm].mean() - f.mean())
    P = ath.bboot(side * f[mm], side * f, h) if mm.sum() >= 10 else None
    yrs = pd.Series(net[mm], index=z.index[mm]).groupby(z.index[mm].year).mean()
    return {"n": int(mm.sum()), "net": round(float(net[mm].mean()), 1), "ham_tetik": round(float(f[mm].mean()), 1),
            "taban": round(float(f.mean()), 1), "fark_yonlu": round(float(diff), 1), "P": None if P is None else round(P, 4),
            "isabet": round(float((net[mm] > 0).mean()), 3), "yil_arti": f"{int((yrs > 0).sum())}/{len(yrs)}"}


def by_era(x: pd.DataFrame, m: pd.Series, h: int, side: int, eras: list[tuple[str, str, str]]) -> dict:
    return {nm: cell(x[(x.index >= a) & (x.index <= b)], m, h, side) for nm, a, b in eras}


def na01(x: pd.DataFrame) -> dict:
    eras = [("1990_2011", "1990-01-01", "2011-12-31"), ("KESIF_2012_2021", "2012-01-01", "2021-10-31"), ("TEST", "2021-11-01", "2026-12-31")]
    calm = x.r5.abs() < 0.02
    cells = {"OH1_SAT": (x.dE5 <= -0.30, -1), "OH2_AL": (x.dE5 >= 0.30, 1),
             "OH1b_SAT_sakin": ((x.dE5 <= -0.30) & calm, -1), "OH2b_AL_sakin": ((x.dE5 >= 0.30) & calm, 1)}
    return {k: by_era(x, m, 5, s, eras) for k, (m, s) in cells.items()}


def na02(x: pd.DataFrame, vxn: pd.Series) -> dict:
    v = vxn.reindex(x.index)
    vrp = v - 100 * x.rv20
    pct = vrp.rolling(504, min_periods=252).apply(lambda a: (a[:-1] < a[-1]).mean() if np.isfinite(a[-1]) else np.nan, raw=True)
    eras = [("KESIF", "2001-01-01", "2021-10-31"), ("K_2001_2010", "2001-01-01", "2010-12-31"), ("K_2011_2021", "2011-01-01", "2021-10-31"),
            ("TEST", "2021-11-01", "2026-12-31")]
    cells = {"VP1_AL": (pct >= 0.80, 1), "VP2_SAT": (pct <= 0.20, -1), "VP3_AL_negatif": (vrp < 0, 1)}
    out = {}
    for k, (m, s) in cells.items():
        for h in (5, 20):
            out[f"{k}_h{h}"] = by_era(x, m, h, s, eras)
    q = pd.qcut(pct.dropna(), 5, labels=False)
    out["kantil_f20"] = {e: {int(i): round(float(x.f20.reindex(g.index)[(g.index >= a) & (g.index <= b)].mean()), 1)
                             for i, g in q.groupby(q)} for e, a, b in eras}
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    out = {}
    for nm in ("NDX", "QQQ"):
        x = frame(load(nm))
        out[nm] = {"NA01": na01(x), "NA02": na02(x, load("VXN"))}
    (RES / "gunluk.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for nm, r in out.items():
        print(f"\n===== {nm}")
        for fam, cs in r.items():
            for c, eras in cs.items():
                print(fam, c, json.dumps(eras, ensure_ascii=False))


if __name__ == "__main__":
    main()
