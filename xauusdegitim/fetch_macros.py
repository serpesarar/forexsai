"""Pull DXY / VIX / US10Y daily+hourly history from Yahoo Finance and save in MT5 CSV format."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

OUT = Path(__file__).resolve().parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

TICKERS = {
    "DXY":   "DX-Y.NYB",   # ICE US Dollar Index
    "VIX":   "^VIX",
    "US10Y": "^TNX",        # 10-yr yield (in %)
}

# yfinance limits: 1h history capped at ~730 days; 1d history is full.
PERIODS = {
    "H1": ("60m", "730d"),   # ~2 yıl saatlik
    "D1": ("1d",  "max"),    # tüm tarih
}


def save(df: pd.DataFrame, sym: str, tf: str) -> int:
    if df.empty:
        return 0
    df = df.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "tick_volume",
    })
    # MultiIndex column case (yfinance returns multi-level when single ticker too)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    out = pd.DataFrame({
        "timestamp": df.index.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "open":  df["open"].round(4),
        "high":  df["high"].round(4),
        "low":   df["low"].round(4),
        "close": df["close"].round(4),
        "tick_volume": df.get("tick_volume", pd.Series(0, index=df.index)).fillna(0).astype(int),
        "real_volume": 0,
        "spread": 0,
    })
    p = OUT / f"{sym}_{tf}.csv"
    out.to_csv(p, index=False)
    return len(out)


def main():
    for sym, ticker in TICKERS.items():
        for tf, (interval, period) in PERIODS.items():
            print(f"Fetching {sym} ({ticker}) {tf} interval={interval} period={period}...")
            try:
                df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
                if df.empty:
                    print(f"  [empty] skipping")
                    continue
                # Normalize tz to UTC
                if df.index.tz is None:
                    df.index = df.index.tz_localize("UTC")
                else:
                    df.index = df.index.tz_convert("UTC")
                n = save(df, sym, tf)
                print(f"  saved {n} rows  {df.index.min()} → {df.index.max()}  → {OUT / f'{sym}_{tf}.csv'}")
            except Exception as e:
                print(f"  ERR: {e}")


if __name__ == "__main__":
    main()
