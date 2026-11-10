"""Günlük veri indirme (yalnız fiyat/hacim; sonuç hesaplamaz)."""
from pathlib import Path
import pandas as pd, yfinance as yf
D = Path(__file__).resolve().parent / "data"
for tk, nm in [("QQQ", "QQQ"), ("QQEW", "QQEW"), ("^VXN", "VXN"), ("^VIX", "VIX"), ("^NDX", "NDX"), ("^VVIX", "VVIX"), ("^VIX3M", "VIX3M"), ("^VIX9D", "VIX9D"), ("TQQQ", "TQQQ"), ("SQQQ", "SQQQ"), ("^SKEW", "SKEW")]:
    x = yf.Ticker(tk).history(start="1999-01-01", end="2026-11-10", auto_adjust=False)
    x.index = pd.DatetimeIndex(x.index).tz_localize(None).normalize(); x.to_parquet(D / f"{nm}.parquet")
    print(nm, len(x), x.index[0].date(), x.index[-1].date(), list(x.columns)[:6])
