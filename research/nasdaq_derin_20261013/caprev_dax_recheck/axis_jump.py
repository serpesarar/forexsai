"""Gün bazında keskin kayma tahmini: Xetra açılış SIÇRAMASI (açılış barı / bir önceki bar aralık oranı).

Aday kayma s ∈ {−120, −60, 0, +60}: sıçrama_s = log(aralık[t+s] / aralık[t+s−step]). En büyük sıçrama = günün oyu.
Çıktı: (a) DST sınıfı × kış dönemi bazında oy dağılımı, (b) belirtilen aralıktaki günlerin listesi.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

GF = Path("/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data")
OUT = Path(__file__).resolve().parent / "results"
CANDS = (-120, -60, 0, 60)


def votes(tf: str, start: str = "2019-01-01") -> pd.DataFrame:
    step = {"15m": 15, "30m": 30, "1h": 60}[tf]
    d = pd.read_parquet(GF / f"dax_{tf}.parquet")
    d = d[(d.ts >= start) & (d.ts.dt.weekday <= 4)].copy()
    d["date"] = pd.to_datetime(d.ts.dt.date)
    d["um"] = d.ts.dt.hour * 60 + d.ts.dt.minute
    d["rng"] = (d.high - d.low).clip(lower=1e-9)
    rows = []
    for dt, x in d.groupby("date"):
        noon = pd.Timestamp(dt).tz_localize("UTC") + pd.Timedelta(hours=12)
        be, ny = bool(noon.tz_convert("Europe/Berlin").dst()), bool(noon.tz_convert("America/New_York").dst())
        t = 420 if be else 480
        r = x.set_index("um").rng
        j = {}
        for s in CANDS:
            a, b = r.get(t + s), r.get(t + s - step)
            if a is not None and b is not None:
                j[s] = float(np.log(a / b))
        if len(j) < 3:
            continue
        best = max(j, key=j.get)
        rows.append({"date": dt.date(), "be_dst": be, "ny_dst": ny, "oy": best, "sicrama": round(j[best], 2),
                     **{f"j{s}": round(v, 2) for s, v in j.items()}})
    v = pd.DataFrame(rows)
    v["sinif"] = np.where(v.ny_dst, np.where(v.be_dst, "ikisi_yaz", "NYyaz_BERkis"),
                          np.where(v.be_dst, "NYkis_BERyaz", "ikisi_kis"))
    # kış dönemi etiketi (Kasım–Mart → "2019/20" vb.)
    dts = pd.to_datetime(v.date)
    v["donem"] = np.where(dts.dt.month >= 7, dts.dt.year.astype(str) + "/" + (dts.dt.year + 1).astype(str).str[2:],
                          (dts.dt.year - 1).astype(str) + "/" + dts.dt.year.astype(str).str[2:])
    return v


if __name__ == "__main__":
    tf = sys.argv[1]
    v = votes(tf)
    v.to_csv(OUT / f"axis_jump_{tf}.csv", index=False)
    tab = v.groupby(["sinif", "donem"]).oy.value_counts(normalize=True).unstack(fill_value=0).round(2)
    tab["n"] = v.groupby(["sinif", "donem"]).size()
    print(tab.to_string())
    if len(sys.argv) > 3:
        w = v[(pd.to_datetime(v.date) >= sys.argv[2]) & (pd.to_datetime(v.date) <= sys.argv[3])]
        print(w.to_string(index=False))
