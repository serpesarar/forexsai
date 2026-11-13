"""FX-01 EK-2: H8 ailesi (H8a/H8b × 4 JPY çifti) seçim düzeltmeli max-t permütasyonu + kör çift havuzu.
Çalıştır: ../../.venv/bin/python -I h8_perm.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f  # noqa: E402
import hyp  # noqa: E402

PAIRS = ["USDJPY", "EURJPY", "AUDJPY", "GBPJPY"]
BLIND = ["EURJPY", "AUDJPY", "GBPJPY"]
N_PERM = 1000


def day_table() -> pd.DataFrame:
    got, jbd = hyp.gotobi_days("2010-10-08", "2026-11-12")
    days = sorted(d for d in jbd if d.dayofweek < 5)
    rows = []
    for d in days:
        rec = {"d": d, "got": d in got}
        for p in PAIRS:
            a = hyp.trade(p, d - pd.Timedelta(hours=1), d + pd.Timedelta(hours=1), +1)
            b = hyp.trade(p, d + pd.Timedelta(hours=1), d + pd.Timedelta(hours=6), -1)
            rec[f"A_{p}"] = a["net"] if a else np.nan
            rec[f"B_{p}"] = b["net"] if b else np.nan
            rec[f"B15_{p}"] = b["net15"] if b else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def diff_t(v: np.ndarray, lab: np.ndarray) -> float:
    ok = ~np.isnan(v)
    a, b = v[ok & lab], v[ok & ~lab]
    if len(a) < 10:
        return np.nan
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return (a.mean() - b.mean()) / se


def main() -> dict:
    t = day_table()
    t.to_parquet(f.RES / "h8_gun_tablosu.parquet")
    cols = [c for c in t.columns if c[:2] in ("A_", "B_")]
    lab = t.got.values
    obs = {c: diff_t(t[c].values, lab) for c in cols}
    yrs = t.d.dt.year.values
    rng = np.random.default_rng(17)
    mx = []
    for _ in range(N_PERM):
        perm = np.empty_like(lab)
        for y in np.unique(yrs):
            idx = np.where(yrs == y)[0]
            perm[idx] = np.roll(lab[idx], rng.integers(3, len(idx) - 3))
        mx.append(np.nanmax([diff_t(t[c].values, perm) for c in cols]))
    mx = np.array(mx)
    res = {"gozlenen_t": {c: round(float(v), 2) for c, v in obs.items()},
           "maxt_p": {c: round(float((mx >= v).mean()), 3) for c, v in obs.items()}}
    g = t[t.got]
    blind = {}
    for p in BLIND:
        v = g[f"B_{p}"].dropna()
        blind[p] = {"n": int(len(v)), "net": round(v.mean(), 2), "net15": round(g[f"B15_{p}"].mean(), 2),
                    "kontrol": round(t[~t.got][f"B_{p}"].mean(), 2),
                    "kesif": round(v[g.loc[v.index].d < f.SPLIT].mean(), 2), "kor": round(v[g.loc[v.index].d >= f.SPLIT].mean(), 2)}
    pool = g[[f"B_{p}" for p in BLIND]].mean(axis=1).dropna()
    res["kor_ciftler"] = blind
    res["kor_havuz"] = {**f.summ(pool, g.loc[pool.index].d), "P_gunkume": round(f.boot_p(pool.values), 3)}
    both = (g[[f"A_{p}" for p in ["USDJPY"]]].values.ravel() + g["B_USDJPY"].values)
    res["birlesik_USDJPY_gotobi_gunu"] = f.summ(pd.Series(both).dropna())
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    (f.RES / "h8_perm.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    return res


if __name__ == "__main__":
    main()
