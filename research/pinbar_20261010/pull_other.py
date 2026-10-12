"""XAUUSD / USOIL.FOREX 5m/15m/30m/1h candle_cache → data/<sym>_<tf>.parquet (temizlik build_bars ile aynı mantık).
Not: 2026-07-15 öncesi broker saati (NY+7), 2026-09-03+ Yahoo vadelisi (E21) — mum şekli testi saatten bağımsız;
kaynak bayrağı 'src' sütununda."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / "research/ndx_buy_lab"))
from pull_data import client, fetch_all
GRID = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}
cl = client()
for sym in ("XAUUSD", "USOIL.FOREX"):
    for tf, g in GRID.items():
        df = fetch_all(cl, "candle_cache", "candle_time,open,high,low,close,fetched_at",
                       [("symbol", "eq", sym), ("timeframe", "eq", tf)], "candle_time")
        df["ts"] = pd.to_datetime(df.candle_time, utc=True, format="ISO8601")
        df = df[(df.ts.dt.second == 0) & ((df.ts.dt.hour * 60 + df.ts.dt.minute) % g == 0)]
        df = df.sort_values(["ts", "fetched_at"]).drop_duplicates("ts", keep="last")
        df = df[["ts", "open", "high", "low", "close"]].astype({c: float for c in ["open", "high", "low", "close"]})
        df = df[(df.high >= df.low) & (df.low > 0)]
        df["src"] = "broker"; df.loc[df.ts >= "2026-09-03", "src"] = "yahoo"
        df["seg"] = (df.ts.diff() > pd.Timedelta(days=4)).cumsum()
        df.reset_index(drop=True).to_parquet(Path(__file__).resolve().parent / "data" / f"{sym.split('.')[0]}_{tf}.parquet")
        print(sym, tf, len(df), df.ts.min().date(), df.ts.max().date())
