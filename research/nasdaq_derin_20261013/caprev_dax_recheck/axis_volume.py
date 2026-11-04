"""Gün bazında kayma — TİK HACMİ sıçraması, iki bağımsız çapa (Xetra 09:00 Berlin + ABD 09:30 NY).

Aday s ∈ {−60, 0, +60}: skor_s = log(v[tx+s]/v[tx+s−step]) + log(v[tu+s]/v[tu+s−step]); tx, tu gerçek UTC
açılış dakikaları (DST'ye göre). 1h'te ABD açılışı bar ortasına düştüğü için yalnız Xetra çapası.
Model testi: 'beklenen kayma' = −60 eğer NY standart saatte, değilse 0 (önceki araştırmacının kuralı).
Çıktı: sınıf×dönem oy tablosu + modele uymayan GÜÇLÜ (marj ≥ 0,7) günlerin bölütleri.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

GF = Path("/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data")
OUT = Path(__file__).resolve().parent / "results"
CANDS = (-60, 0, 60)


def votes(tf: str, start: str = "2019-01-01") -> pd.DataFrame:
    step = {"15m": 15, "30m": 30, "1h": 60}[tf]
    d = pd.read_parquet(GF / f"dax_{tf}.parquet")
    d = d[(d.ts >= start) & (d.ts.dt.weekday <= 4)].copy()
    d["date"] = d.ts.dt.date
    d["um"] = d.ts.dt.hour * 60 + d.ts.dt.minute
    d["v"] = d.volume.clip(lower=1).astype(float)
    rows = []
    for dt, x in d.groupby("date"):
        noon = pd.Timestamp(dt).tz_localize("UTC") + pd.Timedelta(hours=12)
        be, ny = bool(noon.tz_convert("Europe/Berlin").dst()), bool(noon.tz_convert("America/New_York").dst())
        tx = 420 if be else 480
        tu = 810 if ny else 870
        r = x.set_index("um").v
        sc = {}
        for s in CANDS:
            parts = []
            anchors = [tx] if step == 60 else [tx, tu]
            for t in anchors:
                a, b = r.get(t + s), r.get(t + s - step)
                if a is None or b is None:
                    break
                parts.append(np.log(a / b))
            if len(parts) == len(anchors):
                sc[s] = float(sum(parts))
        if len(sc) < 3:
            continue
        o = sorted(sc, key=sc.get, reverse=True)
        rows.append({"date": dt, "be_dst": be, "ny_dst": ny, "oy": o[0], "marj": round(sc[o[0]] - sc[o[1]], 2),
                     "beklenen": 0 if ny else -60})
    v = pd.DataFrame(rows)
    v["sinif"] = np.where(v.ny_dst, np.where(v.be_dst, "ikisi_yaz", "NYyaz_BERkis"),
                          np.where(v.be_dst, "NYkis_BERyaz", "ikisi_kis"))
    dts = pd.to_datetime(v.date)
    v["donem"] = np.where(dts.dt.month >= 7, dts.dt.year.astype(str) + "/" + (dts.dt.year + 1).astype(str).str[2:],
                          (dts.dt.year - 1).astype(str) + "/" + dts.dt.year.astype(str).str[2:])
    return v


if __name__ == "__main__":
    tf = sys.argv[1]
    v = votes(tf)
    v.to_csv(OUT / f"axis_volume_{tf}.csv", index=False)
    tab = v.groupby(["sinif", "donem"]).oy.value_counts(normalize=True).unstack(fill_value=0).round(2)
    tab["n"] = v.groupby(["sinif", "donem"]).size()
    tab["modele_uyum"] = v.assign(u=v.oy == v.beklenen).groupby(["sinif", "donem"]).u.mean().round(2)
    print(tab.to_string())
    bad = v[(v.oy != v.beklenen) & (v.marj >= 0.7)]
    print(f"\nModele uymayan güçlü günler (marj≥0,7): {len(bad)} / {len(v)}")
    print(bad.to_string(index=False))
