"""QS-10 verisi: GLD (yalnız indirme)."""
from pathlib import Path
import pandas as pd, yfinance as yf
D = Path(__file__).resolve().parent / "data"
for tk in ("GLD",):
    x = yf.Ticker(tk).history(start="2004-01-01", end="2026-11-12", auto_adjust=False)
    x.index = pd.DatetimeIndex(x.index).tz_localize(None).normalize(); x.to_parquet(D / f"{tk}.parquet")
    print(tk, len(x), x.index[0].date(), x.index[-1].date())
