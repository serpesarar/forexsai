"""DAX saat ekseni bağımsız denetimi (sonuçlara bakmadan, yalnız bar aralığı).

İki çapa, ikisi de UTC'de ölçülür (Berlin/NY dönüşümüne güvenmeden):
  A) Xetra açılışı 09:00 Berlin  → gerçek UTC 08:00 (Berlin kış) / 07:00 (Berlin yaz)
  B) ABD nakit açılışı 09:30 NY  → gerçek UTC 14:30 (NY kış)     / 13:30 (NY yaz)
Her (ay × DST-durumu) hücresinde hafta içi medyan aralığın tepe yaptığı ETİKET UTC dakikası bulunur;
fark = etiket − gerçek. DST durumları dört sınıfa ayrılır: her ikisi yaz / her ikisi kış /
NY yaz ∧ Berlin kış (Mart ve Ekim-Kasım omuz haftaları).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GF = Path("/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data")
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(exist_ok=True)


def dst_flags(ts: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    ny = ts.dt.tz_convert("America/New_York").map(lambda t: bool(t.dst())).to_numpy()
    be = ts.dt.tz_convert("Europe/Berlin").map(lambda t: bool(t.dst())).to_numpy()
    return ny, be


def peak(x: pd.DataFrame, lo: int, hi: int) -> tuple[int | None, float]:
    """lo..hi (UTC dakika, bar başlangıcı) arasında medyan aralığın tepe yaptığı dakika."""
    w = x[(x.um >= lo) & (x.um <= hi)]
    if w.empty:
        return None, np.nan
    g = w.groupby("um").rng.median()
    return int(g.idxmax()), float(g.max())


def analyse(tf: str, start: str = "2019-01-01") -> pd.DataFrame:
    step = {"15m": 15, "30m": 30, "1h": 60}[tf]
    d = pd.read_parquet(GF / f"dax_{tf}.parquet")
    d = d[d.ts >= start].copy()
    d["um"] = d.ts.dt.hour * 60 + d.ts.dt.minute
    d["rng"] = d.high - d.low
    d["wd"] = d.ts.dt.weekday
    d = d[d.wd <= 4]
    ny, be = dst_flags(d.ts)
    d["cls"] = np.select([ny & be, ~ny & ~be, ny & ~be], ["ikisi_yaz", "ikisi_kis", "NYyaz_BERkis"], "NYkis_BERyaz")
    d["mon"] = d.ts.dt.strftime("%Y-%m")
    rows = []
    for (mon, cls), x in d.groupby(["mon", "cls"]):
        if x.ts.dt.date.nunique() < 3:
            continue
        true_x = 420 if cls in ("ikisi_yaz", "NYkis_BERyaz") else 480        # Xetra 09:00 Berlin → UTC
        true_u = 810 if cls in ("ikisi_yaz", "NYyaz_BERkis") else 870        # 09:30 NY → UTC
        # 1h barlarda 09:30 NY açılışı 13:00/14:00 UTC barının içine düşer (bar başı)
        true_u_bar = (true_u // step) * step
        px, rx = peak(x, 300, 600)
        pu, ru = peak(x, 720, 960)
        rows.append({"ay": mon, "sinif": cls, "gun": int(x.ts.dt.date.nunique()),
                     "xetra_tepe_UTC": f"{px//60:02d}:{px%60:02d}" if px is not None else None,
                     "xetra_kayma_dk": (px - true_x) if px is not None else None,
                     "us_tepe_UTC": f"{pu//60:02d}:{pu%60:02d}" if pu is not None else None,
                     "us_kayma_dk": (pu - true_u_bar) if pu is not None else None})
    return pd.DataFrame(rows)


def by_day_shift(tf: str = "15m") -> pd.DataFrame:
    """Gün bazında: Xetra açılış barı gerçek UTC'de mi yoksa 60 dk önce mi? (aralık oranı)"""
    step = {"15m": 15, "30m": 30, "1h": 60}[tf]
    d = pd.read_parquet(GF / f"dax_{tf}.parquet")
    d = d[d.ts >= "2019-01-01"].copy()
    d["date"] = d.ts.dt.date
    d["um"] = d.ts.dt.hour * 60 + d.ts.dt.minute
    d["rng"] = d.high - d.low
    ny, be = dst_flags(d.ts)
    d["ny"], d["be"] = ny, be
    out = []
    for dt, x in d.groupby("date"):
        b = bool(x.be.iat[0]); n = bool(x.ny.iat[0])
        t = 420 if b else 480
        r = x.set_index("um").rng
        if t in r.index and (t - 60) in r.index:
            out.append({"date": dt, "be_dst": b, "ny_dst": n, "dogru": r[t], "erken60": r[t - 60]})
    return pd.DataFrame(out)


if __name__ == "__main__":
    res = {}
    for tf in ["15m", "30m", "1h"]:
        t = analyse(tf)
        res[tf] = t.to_dict("records")
        print(f"\n===== DAX {tf} =====")
        print(t.to_string(index=False))
        s = t.groupby("sinif")[["xetra_kayma_dk", "us_kayma_dk"]].agg(lambda v: v.value_counts().to_dict())
        print(s.to_string())
    # gün bazında oran: hangi gün tipinde açılış tepesi 60 dk erken etikette
    for tf in ["15m", "1h"]:
        g = by_day_shift(tf)
        g["erken_mi"] = g.erken60 > g.dogru
        g["sinif"] = np.select([g.ny_dst & g.be_dst, ~g.ny_dst & ~g.be_dst, g.ny_dst & ~g.be_dst],
                               ["ikisi_yaz", "ikisi_kis", "NYyaz_BERkis"], "NYkis_BERyaz")
        print(f"\n{tf} gün bazında 'açılış sıçraması 60 dk erken etikette' oranı:")
        print(g.groupby("sinif").erken_mi.agg(["mean", "size"]).to_string())
        res[f"gun_{tf}"] = g.groupby("sinif").erken_mi.agg(["mean", "size"]).reset_index().to_dict("records")
    (OUT / "axis_dax.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
