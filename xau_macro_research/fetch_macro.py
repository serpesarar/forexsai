"""Pull daily macro panel from FRED (free, no key) + align with XAUUSD D1.

Gold's textbook drivers: 10Y real yield (DFII10, inverse), USD (DTWEXBGS, inverse),
nominal yield (DGS10), inflation breakeven (T10YIE), risk (VIXCLS), curve (DGS2).
NOTE: the real-yield↔gold inverse link BROKE in 2024-26 (gold rose with rising real
yields — CB buying/de-dollarization). The model must cope with this regime shift.
"""
from __future__ import annotations
import io, urllib.request as u
import pandas as pd

FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}&cosd=2021-01-01"
SERIES = ["DFII10", "DGS10", "DGS2", "T10YIE", "DTWEXBGS", "VIXCLS"]
OUT = "xau_macro_research/macro_panel.csv"


def fred(series_id: str) -> pd.Series:
    raw = u.urlopen(FRED.format(id=series_id), timeout=30).read().decode()
    df = pd.read_csv(io.StringIO(raw))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    return df.set_index("date")[series_id]


def load_gold() -> pd.Series:
    g = pd.read_csv("xauusdegitim/data/raw/XAUUSD_D1.csv")
    g["date"] = pd.to_datetime(g["timestamp"], utc=True).dt.tz_localize(None).dt.normalize()
    return g.set_index("date")["close"].astype(float).rename("gold")


def main():
    cols = {}
    for s in SERIES:
        try:
            cols[s] = fred(s)
            print(f"  {s}: {cols[s].notna().sum()} obs  {cols[s].dropna().index[0].date()}→{cols[s].dropna().index[-1].date()}")
        except Exception as e:
            print(f"  {s}: FAIL {e}")
    macro = pd.DataFrame(cols)
    gold = load_gold()
    # daily calendar, forward-fill macro (holiday gaps), align gold
    idx = pd.date_range(macro.index.min(), max(macro.index.max(), gold.index.max()), freq="D")
    df = macro.reindex(idx).ffill()
    df["gold"] = gold.reindex(idx)
    df = df.dropna(subset=["gold"]).copy()      # keep only days gold traded
    df = df.dropna()                             # need all macro present
    df.index.name = "date"
    df.to_csv(OUT)
    print(f"\nsaved {OUT}: {len(df)} aligned rows  {df.index[0].date()}→{df.index[-1].date()}")
    print(df.tail(3).round(2).to_string())


if __name__ == "__main__":
    main()
