"""pull_long.py — kutudan gelen DERİN geçmişi indir (15m 2023+, 30m 2021+, 1h 2016+, 1d 2008+)."""
from __future__ import annotations

import pandas as pd

from pull_data import client, fetch_all, OUT, SYMBOL

DEEP_TFS = ["15m", "30m", "1h", "1d"]
GRID = {"15m": 15, "30m": 30, "1h": 60, "1d": 1440}


def main() -> None:
    cl = client()
    for tf in DEEP_TFS:
        print(f"  {tf} …", flush=True)
        df = fetch_all(cl, "candle_cache",
                       "candle_time,open,high,low,close,volume,fetched_at",
                       [("symbol", "eq", SYMBOL), ("timeframe", "eq", tf)],
                       "candle_time")
        if df.empty:
            print("    BOŞ"); continue
        df["ts"] = pd.to_datetime(df["candle_time"], utc=True)
        n0 = len(df)
        df = df[(df["ts"].dt.second == 0) & (df["ts"].dt.microsecond == 0)]
        if tf != "1d":
            mins = df["ts"].dt.hour * 60 + df["ts"].dt.minute
            df = df[mins % GRID[tf] == 0]
        df = (df.sort_values(["ts", "fetched_at"]).drop_duplicates("ts", keep="last")
                .sort_values("ts"))[["ts", "open", "high", "low", "close", "volume"]]
        df.to_csv(OUT / f"long_{tf}.csv", index=False)
        print(f"    {tf}: {len(df)} (ham {n0})  {df.ts.min()} → {df.ts.max()}")


if __name__ == "__main__":
    main()
