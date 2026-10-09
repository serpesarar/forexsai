"""build_bars.py — NASDAQ (NDX/NAS100) 1m/5m/15m/30m bar setini kur.

Kaynaklar (hepsi gerçek UTC, bar BAŞLANGICI damgalı):
  1m  : research/ndx_gate_forge/data/bars_1m_all.parquet
        (Dukascopy 2025 tick→1m + candle_cache 2026-02-10→05-19 [+60dk düzeltilmiş]
         + MT5 M1 05-19→08-28 + indicator_snapshots 08-30→09-30)
        + candle_cache 1m (son günler) — 2026-01 başında ~6 haftalık boşluk var.
  5m  : 1m'den kova-hizalı resample.
  15m/30m : broker (Pepperstone NAS100) candle_cache —
        2026-07-15 öncesi broker saatindeydi (NY+7) → gate_forge long_<tf>_utc.parquet
        (dönüştürülmüş), sonrası Supabase'ten taze (zaten UTC).

Temizlik: saniye≠0 tick kirliliği, kovaya hizasız dakika, NY 17:00-18:00 günlük
ara (candle_cache bu saatte bir önceki saatin KOPYASINI tutuyor — 2026-09-16'da
görüldü), hafta sonu barları. Segment = arada >4 gün boşluk olmayan kesintisiz blok;
hiçbir pencere segment sınırını aşmaz.

Çıktı: data/bars_<tf>.parquet  [ts, open, high, low, close, seg]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
GF = ROOT / "research/ndx_gate_forge/data"
sys.path.insert(0, str(ROOT / "research/ndx_buy_lab"))

START = pd.Timestamp("2023-10-01", tz="UTC")       # 15m/30m için 3 yıl
LONG_CUT = pd.Timestamp("2026-07-15", tz="UTC")    # candle_cache UTC onarımı
SEG_GAP = pd.Timedelta(days=4)
GRID_MIN = {"1m": 1, "5m": 5, "15m": 15, "30m": 30}


def _market_open_mask(ts: pd.Series) -> np.ndarray:
    """NY saatine göre işlem saati: Paz 18:00 → Cum 17:00, her gün 17-18 arası kapalı."""
    ny = ts.dt.tz_convert("America/New_York")
    h, wd = ny.dt.hour.values, ny.dt.weekday.values
    closed = (h == 17) | (wd == 5) | ((wd == 6) & (h < 18)) | ((wd == 4) & (h >= 17))
    return ~closed


def _clean(d: pd.DataFrame, tf: str) -> pd.DataFrame:
    d = d[(d.ts.dt.second == 0)].copy()
    mins = d.ts.dt.hour * 60 + d.ts.dt.minute
    d = d[(mins % GRID_MIN[tf]) == 0]
    d = d.sort_values("ts").drop_duplicates("ts", keep="last")
    d = d[_market_open_mask(d.ts)]
    ohlc = d[["open", "high", "low", "close"]].to_numpy()
    d = d[(ohlc > 0).all(1) & (d.high >= d.low).to_numpy()]
    return d.reset_index(drop=True)


def _segment(d: pd.DataFrame) -> pd.DataFrame:
    gap = d.ts.diff() > SEG_GAP
    d["seg"] = gap.cumsum().astype(int)
    return d


def _pull_cache(tf: str, since: pd.Timestamp) -> pd.DataFrame:
    from pull_data import client, fetch_all
    df = fetch_all(client(), "candle_cache", "candle_time,open,high,low,close,fetched_at",
                   [("symbol", "eq", "NDX.INDX"), ("timeframe", "eq", tf),
                    ("candle_time", "gte", since.isoformat())], "candle_time")
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df.candle_time, utc=True)
    df = df.sort_values(["ts", "fetched_at"]).drop_duplicates("ts", keep="last")
    return df[["ts", "open", "high", "low", "close"]].astype(
        {c: float for c in ["open", "high", "low", "close"]})


def build_1m() -> pd.DataFrame:
    b = pd.read_parquet(GF / "bars_1m_all.parquet")[["ts", "open", "high", "low", "close"]]
    tail = _pull_cache("1m", b.ts.max() + pd.Timedelta(minutes=1))
    d = pd.concat([b, tail], ignore_index=True)
    return _segment(_clean(d, "1m"))


def resample(d1: pd.DataFrame, minutes: int) -> pd.DataFrame:
    g = d1.set_index("ts").groupby([pd.Grouper(freq=f"{minutes}min"), "seg"])
    out = g.agg(open=("open", "first"), high=("high", "max"),
                low=("low", "min"), close=("close", "last")).dropna().reset_index()
    return out.sort_values("ts").reset_index(drop=True)


def build_broker(tf: str) -> pd.DataFrame:
    old = pd.read_parquet(GF / f"long_{tf}_utc.parquet")[["ts", "open", "high", "low", "close"]]
    old = old[(old.ts >= START) & (old.ts < LONG_CUT)]
    new = _pull_cache(tf, LONG_CUT)
    d = pd.concat([old, new], ignore_index=True)
    d = _clean(d, tf)
    # candle_cache günlük arada bir önceki saatin kopyasını yazmış olabilir → birebir
    # aynı OHLC'li ve tam 1 saat sonraki barı at (piyasa açıkken de yakalanır)
    key = d[["open", "high", "low", "close"]].round(2).astype(str).agg("|".join, axis=1)
    prev = dict(zip(d.ts + pd.Timedelta(hours=1), key))
    dup = np.array([prev.get(t) == k for t, k in zip(d.ts, key)])
    d = d[~dup].reset_index(drop=True)
    return _segment(d)


def main() -> None:
    d1 = build_1m()
    d1.to_parquet(DATA / "bars_1m.parquet")
    d5 = resample(d1, 5)
    d5.to_parquet(DATA / "bars_5m.parquet")
    for tf in ("15m", "30m"):
        build_broker(tf).to_parquet(DATA / f"bars_{tf}.parquet")
    for tf in ("1m", "5m", "15m", "30m"):
        d = pd.read_parquet(DATA / f"bars_{tf}.parquet")
        print(f"{tf:>4}: {len(d):>8} bar  {d.ts.min()} → {d.ts.max()}  segment={d.seg.nunique()}")


if __name__ == "__main__":
    main()
