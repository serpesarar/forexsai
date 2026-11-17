"""Proje dışı (ev dizini) NASDAQ ham mum dosyalarının okuyucusu — biçim/ayraç/tarih biçimi kendiliğinden."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()


def read_ohlc(path: Path) -> pd.DataFrame:
    """→ DataFrame(wall: naive datetime (dosyanın kendi saat dilimi), open, high, low, close, vol)."""
    with open(path, "r", errors="replace") as h:
        first = h.readline()
    sep = "\t" if "\t" in first else ","
    has_header = any(c.isalpha() for c in first.split(sep)[0])
    x = pd.read_csv(path, sep=sep, header=0 if has_header else None, usecols=range(6),
                    low_memory=False, on_bad_lines="skip")
    x.columns = ["dt", "open", "high", "low", "close", "vol"]
    wall = pd.to_datetime(x["dt"], errors="coerce", format="mixed")
    out = pd.DataFrame({"wall": wall, **{k: pd.to_numeric(x[k], errors="coerce") for k in ("open", "high", "low", "close", "vol")}})
    out = out.dropna(subset=["wall", "open", "high", "low", "close"]).drop_duplicates("wall").sort_values("wall")
    return out.reset_index(drop=True)


def tf_minutes(df: pd.DataFrame) -> int:
    d = df["wall"].diff().dt.total_seconds().div(60).dropna()
    return int(d.mode().iloc[0]) if len(d) else 0


def read_ohlc_sample(path: Path, n: int) -> pd.DataFrame | None:
    """CSV/TXT: ilk 6 sütun (zaman + OHLC + hacim) — tüm satırlar (gün kapsamı için tam gerekir); n kullanılmaz."""
    try:
        df = read_ohlc(path)
    except Exception:  # noqa: BLE001 — biçim dışı
        return None
    df = df[~(df[["open", "high", "low", "close"]] == 0).all(axis=1)].reset_index(drop=True)  # geniş tabloların 0,0 dolgusu
    ok = (df["high"] >= df[["open", "close"]].max(axis=1) - 1e-9) & (df["low"] <= df[["open", "close"]].min(axis=1) + 1e-9)
    return df if len(df) and ok.mean() > 0.95 else None


def frame_to_ohlc(d: pd.DataFrame) -> pd.DataFrame | None:
    """Parquet/pkl çerçevesi → (wall, open, high, low, close, vol); zaman sütunu ya da DatetimeIndex aranır."""
    cols = {c.lower(): c for c in map(str, d.columns)}
    need = [cols.get(k) for k in ("open", "high", "low", "close")]
    if any(c is None for c in need):
        return None
    tcol = next((cols[k] for k in ("datetime", "time", "timestamp", "date", "ts", "candle_time", "t") if k in cols), None)
    if tcol is not None:
        w = d[tcol]
        wall = pd.to_datetime(w, unit="s") if pd.api.types.is_numeric_dtype(w) else pd.to_datetime(w, errors="coerce", utc=False)
    elif isinstance(d.index, pd.DatetimeIndex):
        wall = pd.Series(d.index)
    else:
        return None
    if getattr(wall.dt, "tz", None) is not None:
        wall = wall.dt.tz_convert("UTC").dt.tz_localize(None)
    out = pd.DataFrame({"wall": wall.to_numpy(), **{k: pd.to_numeric(d[c], errors="coerce").to_numpy() for k, c in zip(("open", "high", "low", "close"), need)}})
    out["vol"] = np.nan
    out = out.dropna(subset=["wall", "open", "high", "low", "close"]).drop_duplicates("wall").sort_values("wall").reset_index(drop=True)
    return out if len(out) else None
