"""Gün bazında kayma tahmini (Xetra açılış çapası) + kayma bölütleri.

Her gün için gerçek Xetra açılış UTC dakikası t (Berlin yaz 07:00, kış 08:00). Kayma s ∈ {−60, 0, +60}:
etiket (t+s) barının aralığı, diğer ikisinden büyükse gün o kaymaya oy verir. Ardışık günler hafta
bazında çoğunluk oyu ile bölütlenir (tek-gün gürültüsü haftalık oyla bastırılır).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

GF = Path("/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data")
OUT = Path(__file__).resolve().parent / "results"


def day_votes(tf: str, start: str = "2019-01-01") -> pd.DataFrame:
    step = {"15m": 15, "30m": 30, "1h": 60}[tf]
    d = pd.read_parquet(GF / f"dax_{tf}.parquet")
    d = d[d.ts >= start].copy()
    d["date"] = pd.to_datetime(d.ts.dt.date)
    d["um"] = d.ts.dt.hour * 60 + d.ts.dt.minute
    d["rng"] = d.high - d.low
    rows = []
    for dt, x in d[d.ts.dt.weekday <= 4].groupby("date"):
        noon = pd.Timestamp(dt).tz_localize("UTC") + pd.Timedelta(hours=12)
        be = bool(noon.tz_convert("Europe/Berlin").dst())
        ny = bool(noon.tz_convert("America/New_York").dst())
        t = 420 if be else 480
        r = x.set_index("um").rng
        cand = {s: r.get(t + s, np.nan) for s in (-60, 0, 60)}
        if any(np.isnan(v) for v in cand.values()):
            continue
        s = max(cand, key=cand.get)
        rows.append({"date": dt, "be_dst": be, "ny_dst": ny, "oy": s, "r_m60": cand[-60], "r_0": cand[0], "r_p60": cand[60]})
    v = pd.DataFrame(rows)
    v["hafta"] = v.date.dt.to_period("W")
    v["sinif"] = np.where(v.ny_dst, np.where(v.be_dst, "ikisi_yaz", "NYyaz_BERkis"), np.where(v.be_dst, "NYkis_BERyaz", "ikisi_kis"))
    return v


def segments(v: pd.DataFrame) -> pd.DataFrame:
    w = v.groupby(["hafta", "sinif"]).agg(bas=("date", "min"), son=("date", "max"), n=("oy", "size"),
                                          oy=("oy", lambda s: s.value_counts().idxmax()),
                                          pay=("oy", lambda s: s.value_counts(normalize=True).max())).reset_index()
    w = w.sort_values("bas").reset_index(drop=True)
    seg, cur = [], None
    for r in w.itertuples():
        key = (r.oy, r.sinif)
        if cur and cur["key"] == key:
            cur["son"], cur["hafta"] = r.son, cur["hafta"] + 1
        else:
            if cur:
                seg.append(cur)
            cur = {"key": key, "bas": r.bas, "son": r.son, "hafta": 1}
    seg.append(cur)
    return pd.DataFrame([{"bas": s["bas"].date(), "son": s["son"].date(), "hafta": s["hafta"], "sinif": s["key"][1],
                          "kayma_dk": s["key"][0]} for s in seg])


if __name__ == "__main__":
    tf = sys.argv[1] if len(sys.argv) > 1 else "1h"
    v = day_votes(tf)
    v.to_csv(OUT / f"axis_days_{tf}.csv", index=False)
    s = segments(v)
    s.to_csv(OUT / f"axis_segments_{tf}.csv", index=False)
    print(s.to_string(index=False))
