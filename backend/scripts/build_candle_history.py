"""Mum benzerlik motoru için yerel geçmiş arşivi (backend/data/candle_history/{SYM}_{tf}.npz — yalnız numpy ile okunur).

Kaynaklar (UTC, broker verisi, zaman ekseni daha önce doğrulanmış araştırma dosyaları):
  NDX.INDX    : 5m bars_5m; 15m/30m long_*_utc + sonrası bars_*; 1h long_1h_utc + 15m'den uzatma; 4h ← 1h
  GDAXI.INDX  : caprev_dax_recheck/data_fixed 15m/30m/1h (1h ≥ 2020); 4h ← 1h
  XAUUSD, USOIL.FOREX : pinbar_20261010/data (yalnız src == broker; Yahoo satırları atılır); 4h ← 1h
4h/1d türetmesi broker gün sınırıyla (NY 17:00). Çalıştır (proje kökünden):
    python3 backend/scripts/build_candle_history.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "backend/data/candle_history"
GF, PM = ROOT / "research/ndx_gate_forge/data", ROOT / "research/ndx_pattern_motifs/data"
FIX, PB = ROOT / "research/nasdaq_derin_20261013/caprev_dax_recheck/data_fixed", ROOT / "research/pinbar_20261010/data"
DAX_1H_START = pd.Timestamp("2020-01-01", tz="UTC")
COLS = ["ts", "open", "high", "low", "close"]


def _clean(d: pd.DataFrame) -> pd.DataFrame:
    if "src" in d.columns:
        d = d[d.src == "broker"]
    d = d[COLS].dropna()
    d = d[(d.high >= d.low) & (d.close > 0)]
    return d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def _extend(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    a, b = _clean(a), _clean(b)
    return _clean(pd.concat([a, b[b.ts > a.ts.max()]]))


def _resample(d: pd.DataFrame, rule: str) -> pd.DataFrame:
    return (d.set_index("ts").resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last"})
            .dropna().reset_index())


def derive(d1h: pd.DataFrame, tf: str) -> pd.DataFrame:
    """1h → 4h / 1d, broker gün sınırı NY 17:00 (kovanın ilk barının UTC zamanı ts olur)."""
    ny = d1h.ts.dt.tz_convert("America/New_York").dt.tz_localize(None) - pd.Timedelta(hours=17)
    key = ny.dt.floor("1D") if tf == "1d" else ny.dt.floor("4h")
    g = d1h.assign(k=key.to_numpy()).groupby("k", sort=True)
    out = g.agg(ts=("ts", "first"), open=("open", "first"), high=("high", "max"), low=("low", "min"),
                close=("close", "last"), n=("close", "size"))
    out = out[out.n >= (3 if tf == "4h" else 15)]
    return _clean(out.reset_index(drop=True))


def sources() -> dict[tuple[str, str], pd.DataFrame]:
    out: dict[tuple[str, str], pd.DataFrame] = {}
    ndx1h = _extend(pd.read_parquet(GF / "long_1h_utc.parquet"), _resample(_clean(pd.read_parquet(PM / "bars_15m.parquet")), "1h"))
    out[("NDX.INDX", "5m")] = _clean(pd.read_parquet(PM / "bars_5m.parquet"))
    out[("NDX.INDX", "15m")] = _extend(pd.read_parquet(GF / "long_15m_utc.parquet"), pd.read_parquet(PM / "bars_15m.parquet"))
    out[("NDX.INDX", "30m")] = _extend(pd.read_parquet(GF / "long_30m_utc.parquet"), pd.read_parquet(PM / "bars_30m.parquet"))
    out[("NDX.INDX", "1h")] = ndx1h
    dax1h = _clean(pd.read_parquet(FIX / "dax_1h.parquet"))
    out[("GDAXI.INDX", "15m")] = _clean(pd.read_parquet(FIX / "dax_15m.parquet"))
    out[("GDAXI.INDX", "30m")] = _clean(pd.read_parquet(FIX / "dax_30m.parquet"))
    out[("GDAXI.INDX", "1h")] = dax1h[dax1h.ts >= DAX_1H_START].reset_index(drop=True)
    for sym, base in (("XAUUSD", "XAUUSD"), ("USOIL.FOREX", "USOIL")):
        for tf in ("5m", "15m", "30m", "1h"):
            out[(sym, tf)] = _clean(pd.read_parquet(PB / f"{base}_{tf}.parquet"))
    for sym in ("NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX"):
        out[(sym, "4h")] = derive(out[(sym, "1h")], "4h")
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for (sym, tf), d in sources().items():
        path = OUT / f"{sym.split('.')[0]}_{tf}.npz"
        ts = (pd.to_datetime(d.ts, utc=True).astype("int64") // 10**9).to_numpy()
        np.savez_compressed(path, ts=ts, **{c: d[c].to_numpy(np.float64) for c in ("open", "high", "low", "close")})
        print(f"{sym:12s} {tf:4s} {len(d):7d} bar  {d.ts.min()} → {d.ts.max()}  → {path.name}")


if __name__ == "__main__":
    main()
