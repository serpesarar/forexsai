"""QS-03 verisi (yalnız indirme; sonuç hesaplamaz)."""
from pathlib import Path
import io, urllib.request
import pandas as pd, yfinance as yf
D = Path(__file__).resolve().parent / "data"
for tk, nm in [("SPY", "SPY"), ("QQQ", "QQQ"), ("IWM", "IWM"), ("DIA", "DIA"), ("TLT", "TLT"), ("^TNX", "TNX"), ("^GSPC", "GSPC")]:
    x = yf.Ticker(tk).history(start="1985-01-01", end="2026-11-11", auto_adjust=False)
    x.index = pd.DatetimeIndex(x.index).tz_localize(None).normalize(); x.to_parquet(D / f"{nm}.parquet")
    print(nm, len(x), x.index[0].date(), x.index[-1].date())
for sid in ("WALCL", "WTREGEN", "RRPONTSYD"):
    s = urllib.request.urlopen(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=60).read().decode()
    pd.read_csv(io.StringIO(s)).to_csv(D / f"{sid}.csv", index=False); print(sid, "ok")
