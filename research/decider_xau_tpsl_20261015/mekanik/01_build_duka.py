"""Dukascopy H1 BID/ASK ay dosyalarını çöz → data/duka_h1.parquet (UTC bar başlangıcı).
Kayıt: >i4 ×6: saniye(ay başından), open, close, low, high (×1e-3), float32 hacim."""
from __future__ import annotations
import glob, lzma, os, struct, datetime as dt
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "data", "duka", "raw")

def decode(path: str) -> pd.DataFrame | None:
    b = open(path, "rb").read()
    if not b:
        return None
    a = np.frombuffer(lzma.decompress(b), dtype=">i4").reshape(-1, 6)
    base = pd.Timestamp(os.path.basename(path)[:10], tz="UTC")
    vol = a[:, 5].astype(">i4").view(">f4").astype(float)
    return pd.DataFrame({"ts": base + pd.to_timedelta(a[:, 0], unit="s"),
                         "o": a[:, 1] / 1000, "c": a[:, 2] / 1000, "l": a[:, 3] / 1000, "h": a[:, 4] / 1000, "v": vol})

def side(s: str) -> pd.DataFrame:
    parts = [decode(p) for p in sorted(glob.glob(f"{RAW}/{s}_H1/*.bi5"))]
    return pd.concat([p for p in parts if p is not None]).drop_duplicates("ts").set_index("ts").sort_index()

if __name__ == "__main__":
    b, a = side("BID"), side("ASK")
    d = b.join(a.add_prefix("a"), how="left")
    d = d[d.v > 0].copy()
    d["spr"] = (d.ao - d.o).where(lambda x: (x > 0) & (x < 20))
    d.reset_index().to_parquet(os.path.join(ROOT, "data", "duka_h1.parquet"))
    print(len(d), d.index.min(), d.index.max())
    print(d.spr.groupby(d.index.year).median().round(3).to_dict())
    m = d.index.to_series().dt.to_period("M").value_counts().sort_index()
    print("ay sayısı", len(m), "min bar/ay", m.min(), m.idxmin())
