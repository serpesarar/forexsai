"""Makro (VIX, US10Y=^TNX, DXY) 1h geçmişini çek — NDX sinyal dönemine hizalamak için."""
import yfinance as yf, json
from pathlib import Path
OUT = Path("/Users/melihcanodacioglu/Desktop/panel/macro_ndx_test")
TICKERS = {"VIX": "^VIX", "TNX": "^TNX", "DXY": "DX-Y.NYB"}
START, END = "2026-02-15", "2026-06-27"
for name, tk in TICKERS.items():
    try:
        df = yf.download(tk, start=START, end=END, interval="1h", progress=False, auto_adjust=False)
        if df is None or len(df) == 0:
            df = yf.download(tk, start=START, end=END, interval="1d", progress=False, auto_adjust=False)
            gran = "1d"
        else:
            gran = "1h"
        rows = []
        for ts, r in df.iterrows():
            # UTC epoch
            ep = ts.tz_convert("UTC").timestamp() if ts.tzinfo else ts.tz_localize("UTC").timestamp()
            c = float(r["Close"]) if "Close" in r else float(r["Close"].iloc[0])
            rows.append({"t": ep, "close": c})
        (OUT / f"{name}.json").write_text(json.dumps(rows))
        print(f"  {name} ({tk}) [{gran}]: {len(rows)} bar  {df.index[0]} → {df.index[-1]}")
    except Exception as e:
        print(f"  {name} HATA: {e}")
