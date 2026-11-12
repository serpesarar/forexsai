"""QS-11 verisi: SLV, SI=F (yalnız indirme)."""
from pathlib import Path
import pandas as pd, yfinance as yf
D = Path(__file__).resolve().parent / "data"
for tk, nm in (("SLV", "SLV"), ("SI=F", "SI")):
    x = yf.Ticker(tk).history(start="2000-01-01", end="2026-11-12", auto_adjust=False)
    x.index = pd.DatetimeIndex(x.index).tz_localize(None).normalize(); x.to_parquet(D / f"{nm}.parquet")
    print(nm, len(x), x.index[0].date(), x.index[-1].date())
