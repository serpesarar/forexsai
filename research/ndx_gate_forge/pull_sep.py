"""indicator_snapshots NDX 1m (MT5 broker gerçeği, UTC) → S26 dönemi."""
import os, requests, pandas as pd
from dotenv import dotenv_values
from common import DATA, ROOT
env = dotenv_values(ROOT / "backend/.env")
url = env["SUPABASE_URL"].rstrip("/")
key = env.get("SUPABASE_SERVICE_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY") or env["SUPABASE_KEY"]
rows, lo = [], 0
while True:
    r = requests.get(f"{url}/rest/v1/indicator_snapshots",
                     params={"symbol": "eq.NDX.INDX", "timeframe": "eq.1m", "candle_time": "gte.2026-08-15",
                             "select": "candle_time,open,high,low,close,volume", "order": "candle_time.asc"},
                     headers={"apikey": key, "Authorization": f"Bearer {key}", "Range-Unit": "items",
                              "Range": f"{lo}-{lo + 999}"}, timeout=60)
    r.raise_for_status(); ch = r.json(); rows += ch
    if len(ch) < 1000: break
    lo += 1000
d = pd.DataFrame(rows)
d["ts"] = pd.to_datetime(d.candle_time, utc=True, format="ISO8601")
d = d.sort_values("ts").drop_duplicates("ts")
d.to_parquet(DATA / "snap_ndx_1m.parquet")
print(len(d), d.ts.min(), d.ts.max())
