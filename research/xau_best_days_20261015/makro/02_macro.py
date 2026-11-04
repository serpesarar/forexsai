"""Günlük makro paneli (yfinance + FRED DFII10) ve olay takvimleri → out/macro_daily.csv, out/calendar.csv.
Takvimler: FOMC planlı toplantı karar günleri (federalreserve.gov tarihî sayfaları + ndx_gate_forge listesi),
CPI ve İstihdam (NFP) yayın günleri (bls.gov arşiv sayfaları). Hepsi önceden ilan edilmiş tarihlerdir."""
import os, io, urllib.request
import pandas as pd, yfinance as yf
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
TK = {"dxy": "DX-Y.NYB", "tnx": "^TNX", "vix": "^VIX", "spx": "^GSPC", "oil": "CL=F", "gcf": "GC=F"}
fr = []
for k, t in TK.items():
    h = yf.Ticker(t).history(start="2007-01-01", end="2026-10-16", interval="1d", auto_adjust=False)
    s = h["Close"].copy(); s.index = pd.to_datetime(s.index.date); s.name = k; fr.append(s)
    print(k, len(s), s.index.min().date(), s.index.max().date())
raw = urllib.request.urlopen("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10&cosd=2007-01-01", timeout=60).read()
r = pd.read_csv(io.BytesIO(raw), na_values=".")
r = r.set_index(pd.to_datetime(r.iloc[:, 0])).iloc[:, 1].rename("ry10")
fr.append(r)
M = pd.concat(fr, axis=1).sort_index()
M = M[M.index >= "2007-01-01"]
M.to_csv(os.path.join(OUT, "macro_daily.csv")); print(M.tail(3))
