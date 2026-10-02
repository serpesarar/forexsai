"""Dukascopy US100 2025 tick -> 1m bid/ask bars (UTC, bar START stamps)."""
from __future__ import annotations
import glob, os
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd

SRC = os.path.expanduser("~/dukascopy_us100/data")
OUT = os.path.join(os.path.dirname(__file__), "data", "duka_1m_2025.parquet")

def one(path: str) -> pd.DataFrame | None:
    try:
        d = pd.read_csv(path, dtype={"timestamp": "int64", "askPrice": "float64", "bidPrice": "float64"})
    except Exception:
        return None
    if d.empty:
        return None
    d["m"] = (d.timestamp // 60000) * 60
    g = d.groupby("m")
    out = pd.DataFrame({
        "open": g.bidPrice.first(), "high": g.bidPrice.max(), "low": g.bidPrice.min(), "close": g.bidPrice.last(),
        "ask_open": g.askPrice.first(), "ask_high": g.askPrice.max(), "ask_low": g.askPrice.min(), "ask_close": g.askPrice.last(),
        "volume": g.bidPrice.size(),
    })
    sp = (d.askPrice - d.bidPrice)
    out["spread_px"] = sp.groupby(d.m).median()
    out.index.name = "t"
    return out.reset_index()

if __name__ == "__main__":
    files = sorted(glob.glob(f"{SRC}/*/*.csv"))
    with ProcessPoolExecutor(8) as ex:
        parts = [p for p in ex.map(one, files, chunksize=4) if p is not None]
    b = pd.concat(parts).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    b["ts"] = pd.to_datetime(b.t, unit="s", utc=True)
    b.to_parquet(OUT)
    print(len(b), b.ts.min(), b.ts.max(), b.spread_px.describe().to_dict())
