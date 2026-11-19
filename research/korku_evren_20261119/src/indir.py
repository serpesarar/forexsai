"""indir.py — evren günlük OHLCV (yfinance, düzeltilmiş). python indir.py"""
import time
from pathlib import Path
import pandas as pd
import yfinance as yf

D = Path(__file__).resolve().parents[1] / "data"
SEKTOR = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU"]
SANAYI = ["SMH", "IBB", "XBI", "KRE", "XHB", "XRT", "MDY", "RSP"]
HISSE = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "JPM", "V", "WMT", "XOM", "UNH", "JNJ", "PG", "HD", "COST",
         "ORCL", "NFLX", "AMD"]
REF = ["QQQ", "SPY"]

if __name__ == "__main__":
    D.mkdir(exist_ok=True)
    for t in SEKTOR + SANAYI + HISSE + REF:
        df = yf.Ticker(t).history(start="1993-01-01", end="2026-11-06", auto_adjust=True)
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df[["Open", "High", "Low", "Close", "Volume"]].to_parquet(D / f"{t}.parquet")
        print(t, df.index.min().date(), df.index.max().date(), len(df), flush=True)
        time.sleep(0.5)
