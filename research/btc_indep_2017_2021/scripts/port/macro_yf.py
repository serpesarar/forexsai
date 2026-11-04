"""Günlük makro kapanışlar (yfinance): ^VIX, DX-Y.NYB, ^TNX, QQQ, ^NDX.

Çıktı: macro_daily.parquet (geniş format, her satır bir ABD işlem günü).
- date: borsanın yerel işlem günü (NY). Değer o günün KAPANIŞINDAN sonra bilinir.
- avail_utc: değerin kesin bilinir olduğu en erken an (konservatif):
  date 22:30 UTC (NY 16:00-17:00 ET kapanışları DST'ye göre 20:00-22:00 UTC;
  DXY ICE kapanışı 17:00 ET = 21:00/22:00 UTC). Backtest'te BTC barı
  t için yalnız avail_utc <= t olan satırlar kullanılmalı (merge_asof).

Kullanım: python -I 04_macro_yf.py <out_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

TICKERS = {"^VIX": "vix", "DX-Y.NYB": "dxy", "^TNX": "us10y", "QQQ": "qqq", "^NDX": "ndx"}
START, END = "2017-01-01", "2021-07-01"


def main() -> None:
    out = Path(sys.argv[1])
    frames, rep = [], {}
    for tk, name in TICKERS.items():
        df = yf.download(tk, start=START, end=END, auto_adjust=False, progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.lower)
        keep = {"close": f"{name}_close"}
        if name == "qqq":
            keep["adj close"] = "qqq_adj_close"
            keep["volume"] = "qqq_volume"
        if name in ("vix", "ndx", "qqq"):
            keep["open"] = f"{name}_open"
        sub = df[list(keep)].rename(columns=keep)
        sub.index = pd.to_datetime(sub.index).tz_localize(None).normalize()
        rep[name] = {"rows": len(sub), "first": str(sub.index.min().date()), "last": str(sub.index.max().date()),
                     "nan_close": int(sub[f"{name}_close"].isna().sum())}
        frames.append(sub)
    m = pd.concat(frames, axis=1).sort_index()
    m.index.name = "date"
    m = m.reset_index()
    m["us10y_close"] = m["us10y_close"] / 10 if m["us10y_close"].median() > 20 else m["us10y_close"]
    m["avail_utc"] = (pd.to_datetime(m["date"]) + pd.Timedelta(hours=22, minutes=30)).dt.tz_localize("UTC")
    rep["merged_rows"] = len(m)
    rep["rows_with_any_nan"] = int(m.drop(columns=["date", "avail_utc"]).isna().any(axis=1).sum())
    rep["nan_by_col"] = m.isna().sum().astype(int).to_dict()
    out.mkdir(parents=True, exist_ok=True)
    m.to_parquet(out / "macro_daily.parquet", index=False)
    (out / "macro_quality_report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    print(m.tail(3).to_string())
    print(m.describe().T[["min", "50%", "max"]].to_string())


if __name__ == "__main__":
    main()
