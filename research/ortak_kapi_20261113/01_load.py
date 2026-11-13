"""Son 3 ayın tüm kapanmış pozisyonları (bot + decider + diğer) → parquet."""
import sys, pandas as pd
sys.path.insert(0, ".")
from scripts.islem_otopsi import data as D
cl = D.get_client()
df = D.load_trades(cl, pd.Timestamp("2026-06-01", tz="UTC"))
df.to_parquet("research/ortak_kapi_20261113/data/trades.parquet")
print(len(df), df.open_raw.min(), df.open_raw.max())
print(df.groupby(["family","symbol","direction"]).agg(n=("net","size"),net=("net","sum"),lot=("volume","median")).round(0).to_string())
