"""
MT5 CSV loader — XAUUSD + macros (DXY, US10Y, VIX).

CSV format (ExportHistoryToCSV.mq5 outputs):
  timestamp,open,high,low,close,tick_volume,real_volume,spread

Timestamp: ISO-8601 in broker server time (NOT pure UTC — broker offset must be subtracted).
The MT5 export script writes server time as if it were UTC (Z suffix). We correct it here
using BROKER_GMT_OFFSET.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data" / "raw"

# IMPORTANT: set this once user tells us their broker's GMT offset.
# Most retail brokers run GMT+2 (winter) / GMT+3 (summer) ≈ "GMT+3" effective.
BROKER_GMT_OFFSET_HOURS = 3  # adjust after user confirms

XAUUSD_TFS = ("M5", "M15", "M30", "H1", "H4", "D1")
MACRO_TFS = ("H1", "D1")


@dataclass
class LoadedSeries:
    symbol: str
    timeframe: str
    df: pd.DataFrame  # index = UTC datetime, cols: open,high,low,close,tick_volume,real_volume,spread


def _read_csv(path: Path, broker_offset_h: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    # MT5 writes "Z" but it's actually broker server time → convert.
    ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    ts = ts - pd.Timedelta(hours=broker_offset_h)  # back to true UTC
    df.index = ts
    df = df.drop(columns=["timestamp"])
    df = df[~df.index.isna()].sort_index()
    df = df[~df.index.duplicated(keep="last")]
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    return df


def load_xauusd(broker_offset_h: int = BROKER_GMT_OFFSET_HOURS,
                tfs: Iterable[str] = XAUUSD_TFS,
                base_dir: Path = DATA_DIR,
                symbol_name: str = "XAUUSD") -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for tf in tfs:
        p = base_dir / f"{symbol_name}_{tf}.csv"
        if not p.exists():
            print(f"  [skip] {p} yok")
            continue
        out[tf] = _read_csv(p, broker_offset_h)
        print(f"  loaded {p.name}: {len(out[tf])} rows  {out[tf].index.min()} → {out[tf].index.max()}")
    return out


def load_macros(broker_offset_h: int = 0,
                base_dir: Path = DATA_DIR) -> dict[str, dict[str, pd.DataFrame]]:
    """Returns {symbol: {tf: df}}. Skips missing files silently.
    Macros are sourced from Yahoo Finance which is already UTC, so default offset=0."""
    candidates = {
        "DXY":   ["DXY", "USDX", "DX-Y.NYB", ".DXY", "USDOLLAR"],
        "US10Y": ["US10Y", "US10YT", "USTNOTE"],
        "VIX":   ["VIX", "VIXX", "VOLATILITY"],
    }
    out: dict[str, dict[str, pd.DataFrame]] = {}
    for canonical, names in candidates.items():
        for name in names:
            for tf in MACRO_TFS:
                p = base_dir / f"{name}_{tf}.csv"
                if p.exists():
                    out.setdefault(canonical, {})[tf] = _read_csv(p, broker_offset_h)
                    print(f"  loaded macro {canonical}/{tf} from {p.name}")
        if canonical not in out:
            print(f"  [warn] {canonical} verisi yok — bu feature ailesi devre dışı kalacak")
    return out


def align_to_base(base: pd.DataFrame, other: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Forward-fill `other` onto `base`'s index. Avoids look-ahead by reindexing with method='ffill'."""
    o = other.copy()
    o.columns = [f"{prefix}_{c}" for c in o.columns]
    return o.reindex(base.index, method="ffill")


if __name__ == "__main__":
    print(f"DATA_DIR = {DATA_DIR}")
    xau = load_xauusd()
    macros = load_macros()
    print(f"\nXAUUSD timeframes loaded: {list(xau)}")
    print(f"Macros loaded: { {k: list(v) for k, v in macros.items()} }")
