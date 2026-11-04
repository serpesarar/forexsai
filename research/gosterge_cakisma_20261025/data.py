"""Veri katmanı: kaynak → temiz OHLC(V) + segment + bölme etiketi (PROTOCOL §2, §6)."""
import numpy as np
import pandas as pd

import config as C


def _read(path: str) -> pd.DataFrame:
    d = pd.read_parquet(path) if path.endswith(".parquet") else pd.read_csv(path)
    tcol = "ts" if "ts" in d.columns else ("t" if "t" in d.columns else d.columns[0])
    d = d.rename(columns={tcol: "ts"})
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    if "src" in d.columns:                      # E21: Yahoo vadeli satırları broker değil
        d = d[d["src"] != "yahoo"]
    keep = ["ts", "open", "high", "low", "close"] + (["volume"] if "volume" in d.columns else [])
    return d[keep].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def _resample(d: pd.DataFrame, tf: str) -> pd.DataFrame:
    rule = {"5m": "5min", "4h": "4h", "1d": "1D"}[tf]
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "volume" in d.columns:
        agg["volume"] = "sum"
    out = d.set_index("ts").resample(rule, label="left", closed="left").agg(agg).dropna(subset=["open", "close"])
    return out.reset_index()


def _clean(d: pd.DataFrame) -> pd.DataFrame:
    ok = (d.high >= d[["open", "close"]].max(axis=1)) & (d.low <= d[["open", "close"]].min(axis=1)) & (d.low > 0)
    return d[ok].reset_index(drop=True)


def _segments(d: pd.DataFrame, tf: str) -> np.ndarray:
    gap = d.ts.diff().dt.total_seconds().fillna(0) / 60.0
    limit = C.TF_MINUTES[tf] * C.GAP_FACTOR
    if tf == "1d":
        limit = 5 * 1440                        # hafta sonu + tatil normal
    elif tf == "4h":
        limit = 80 * 60                         # EK-2: planlı hafta sonu boşluğu segment kırmaz
    return np.cumsum(gap.values > limit).astype(np.int32)


def load(sym: str, tf: str) -> pd.DataFrame:
    path, start = C.SOURCES[sym][tf]
    if path.startswith("derive:"):
        base_tf = path.split(":")[1]
        base_path, base_start = C.SOURCES[sym][base_tf]
        d = _resample(_clean(_read(base_path)), tf)
        start = start or base_start
    else:
        d = _clean(_read(path))
    if start:
        d = d[d.ts >= pd.Timestamp(start, tz="UTC")].reset_index(drop=True)
    d["seg"] = _segments(d, tf)
    n = len(d)
    a, b = int(n * C.SPLITS[0]), int(n * (C.SPLITS[0] + C.SPLITS[1]))
    d["split"] = np.where(np.arange(n) < a, 0, np.where(np.arange(n) < b, 1, 2)).astype(np.int8)
    return d


def bucket(d: pd.DataFrame, tf: str) -> np.ndarray:
    """Taban kovası: gün-içi TF'de UTC saati, 1d'de haftanın günü (PROTOCOL §5)."""
    return (d.ts.dt.dayofweek if tf == "1d" else d.ts.dt.hour).values.astype(np.int16)
