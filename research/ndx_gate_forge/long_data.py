"""Uzun geçmiş (broker saati = NY+7s) → gerçek UTC + NY alanları + günlük makro."""
from __future__ import annotations
import numpy as np, pandas as pd
from common import LONG, DATA

CUT = pd.Timestamp("2026-07-15", tz="UTC")   # sonrası candle_cache UTC'ye onarıldı → karışmasın


def load_long(tf: str) -> pd.DataFrame:
    p = DATA / f"long_{tf}_utc.parquet"
    if p.exists():
        return pd.read_parquet(p)
    d = pd.read_csv(LONG / f"long_{tf}.csv")
    naive = pd.to_datetime(d.ts, utc=True).dt.tz_localize(None) - pd.Timedelta(hours=7)
    ny = naive.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="shift_forward")
    d["ts"] = ny.dt.tz_convert("UTC")
    d = d.dropna(subset=["ts"])
    d = d[d.ts < CUT].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    d.to_parquet(p)
    return d


def macro() -> pd.DataFrame:
    m = pd.read_csv(DATA / "macro_daily_patched.csv", parse_dates=["date"]).set_index("date").sort_index()
    return m


if __name__ == "__main__":
    for tf in ["15m", "30m", "1h"]:
        d = load_long(tf)
        ny = d.ts.dt.tz_convert("America/New_York")
        d["rng"] = d.high - d.low
        g = d.assign(y=ny.dt.year.values, m=(ny.dt.hour * 60 + ny.dt.minute).values).groupby(["y", "m"]).rng.median().reset_index()
        g.columns = ["y", "m", "r"]
        pk = g.loc[g.groupby("y").r.idxmax()]
        print(tf, len(d), d.ts.min(), d.ts.max(), "peak NY:", [(int(a), f"{int(b)//60:02d}:{int(b)%60:02d}") for a, b in zip(pk.y, pk.m)])
